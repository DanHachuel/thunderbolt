from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import Mock, patch

from hermes_ui import growth_youtube
from integrations import youtube_growth_api

ROOT = Path(__file__).resolve().parents[1]
MAIN_SOURCE = (ROOT / "app" / "main.py").read_text(encoding="utf-8")


def test_analysis_code_has_stable_gya_pattern():
    code = growth_youtube.analysis_code(datetime(2026, 9, 3, 19, 0, 0, tzinfo=timezone.utc))
    assert code.startswith("GYA-20260903-190000-")
    assert len(code) == len("GYA-20260903-190000-") + 6


def test_public_videos_limits_to_three_and_uses_ytdlp():
    entries = [{"id": str(i), "title": f"Video {i}"} for i in range(15)]
    fake = Mock()
    fake.extract_info.return_value = {"entries": entries}
    fake.__enter__ = Mock(return_value=fake)
    fake.__exit__ = Mock(return_value=None)
    factory = Mock(return_value=fake)
    with patch.dict("sys.modules", {"yt_dlp": Mock(YoutubeDL=factory)}):
        result = growth_youtube._public_videos("https://youtube.com/@channel")
    assert len(result) == 3
    assert result[0]["id"] == "0"
    factory.assert_called_once()
    assert factory.call_args.args[0]["playlistend"] == 3


def test_score_color_ranges_match_product_requirement():
    assert growth_youtube._score_color(0) == "red"
    assert growth_youtube._score_color(30) == "red"
    assert growth_youtube._score_color(31) == "yellow"
    assert growth_youtube._score_color(69) == "yellow"
    assert growth_youtube._score_color(70) == "green"


def test_report_contains_metrics_and_downloadable_video_summary(tmp_path):
    record = {
        "code": "GYA-20260903-190000-ABC123", "channel_name": "Canal Teste",
        "created_at": "2026-09-03T19:00:00+00:00", "overall_score": 70,
        "metrics": [{"label": "Qualidade do título", "score": 75, "value": "10 títulos", "diagnosis": "Bom"}],
        "videos": [{"title": "Título | teste", "view_count": 1000, "thumbnail_status": "baixada", "transcript_status": "disponível", "title_score": 75}],
    }
    report = growth_youtube._report_markdown(record)
    assert "CHANNEL AUDIT REPORT: Canal Teste" in report
    assert "**Título**" in report
    assert "Projecção financeira e contexto" in report
    assert "Estratégia de longo prazo" in report
    assert "Título / teste" in report


def test_paligemma_payload_is_isolated_and_uses_bearer(tmp_path):
    image = tmp_path / "thumb.jpg"
    image.write_bytes(b"fake-image")
    response = Mock(status_code=200)
    response.raise_for_status.return_value = None
    response.json.return_value = {"choices": [{"message": {"content": '{"score": 82, "diagnosis": "Boa"}'}}]}
    card = {"api_key": "secret", "base_url": "https://integrate.api.nvidia.com/v1", "model": "google/paligemma"}
    with patch("hermes_ui.growth_youtube.requests.post", return_value=response) as post:
        result = growth_youtube.analyse_thumbnail_with_paligemma(str(image), card)
    assert result["score"] == 82
    assert post.call_args.kwargs["headers"]["Authorization"] == "Bearer secret"
    assert post.call_args.kwargs["json"]["model"] == "google/paligemma"
    assert post.call_args.args[0] == "https://ai.api.nvidia.com/v1/vlm/google/paligemma"


def test_growth_oauth_account_matches_channel_id():
    account = {"id": "google-one", "email": "one@example.com", "channels": [{"youtube_channel_id": "UC123"}]}
    assert youtube_growth_api.find_account_for_channel({"youtube_channel_id": "UC123"}, {"youtube_batch_accounts": [account]}) == account


def test_growth_oauth_does_not_use_unrelated_account_when_channel_has_explicit_account():
    unrelated = {"id": "google-one", "email": "one@example.com", "channels": [{"youtube_channel_id": "UC123"}]}
    channel = {"youtube_channel_id": "UC123", "google_account_id": "google-two"}
    assert youtube_growth_api.find_account_for_channel(channel, {"youtube_batch_accounts": [unrelated]}) is None


def test_growth_analytics_is_explicitly_unavailable_without_matching_account(tmp_path):
    result = youtube_growth_api.query_channel_analytics({"youtube_channel_id": "UC123", "google_account_id": "google-two"}, {"youtube_batch_accounts": [{"id": "google-one", "channels": [{"youtube_channel_id": "UC123"}]}]}, tmp_path)
    assert result["status"] == "not_connected"


def test_growth_indicator_uses_the_selected_channel_account_only():
    block = MAIN_SOURCE.split("def render_growth_youtube():", 1)[1].split("def render_", 1)[0]
    assert "selected = st.selectbox(\"Canal a analisar\"" in block
    assert "matched_growth_account = find_youtube_growth_account(selected, growth_settings)" in block
    assert "youtube_batch_account_status(matched_growth_account, STORAGE).ok" in block
    assert "for growth_account in growth_accounts" not in block
