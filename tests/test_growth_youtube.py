from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import Mock, patch

from hermes_ui import growth_youtube


def test_analysis_code_has_stable_gya_pattern():
    code = growth_youtube.analysis_code(datetime(2026, 9, 3, 19, 0, 0, tzinfo=timezone.utc))
    assert code.startswith("GYA-20260903-190000-")
    assert len(code) == len("GYA-20260903-190000-") + 6


def test_public_videos_limits_to_ten_and_uses_ytdlp():
    entries = [{"id": str(i), "title": f"Video {i}"} for i in range(15)]
    fake = Mock()
    fake.extract_info.return_value = {"entries": entries}
    fake.__enter__ = Mock(return_value=fake)
    fake.__exit__ = Mock(return_value=None)
    factory = Mock(return_value=fake)
    with patch.dict("sys.modules", {"yt_dlp": Mock(YoutubeDL=factory)}):
        result = growth_youtube._public_videos("https://youtube.com/@channel", 10)
    assert len(result) == 10
    assert result[0]["id"] == "0"
    factory.assert_called_once()
    assert factory.call_args.args[0]["playlistend"] == 10


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
