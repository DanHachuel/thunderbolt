import json

from integrations.platforms import TikTokAdapter, YouTubeAdapter, _extract_json_assignment, _parse_public_count


class FakeResponse:
    def __init__(self, text: str, status_code: int = 200):
        self.text = text
        self.status_code = status_code

    def raise_for_status(self):
        if self.status_code >= 400:
            raise RuntimeError("HTTP error")


def test_public_count_parsing():
    assert _parse_public_count({"simpleText": "1,2 mil inscritos"}) == 1200
    assert _parse_public_count({"simpleText": "3.4M subscribers"}) == 3_400_000
    assert _parse_public_count({"simpleText": "12.345 vídeos"}) == 12345


def test_json_assignment_handles_nested_braces_and_escaped_strings():
    payload = {"title": "Canal {público}", "nested": {"id": "UC123"}}
    document = "<script>var ytInitialData = " + json.dumps(payload, ensure_ascii=False) + ";</script>"
    assert _extract_json_assignment(document, "ytInitialData") == payload


def test_fetch_channel_public_without_api_key(monkeypatch):
    initial = {
        "header": {"pageHeaderRenderer": {"content": {"pageHeaderViewModel": {"title": {"dynamicTextViewModel": {"text": {"content": "Canal Público"}}}}}}},
        "metadata": {
            "channelMetadataRenderer": {
                "title": "Canal Público",
                "description": "Descrição pública",
                "externalId": "UC123",
                "ownerUrls": ["http://www.youtube.com/@canalpublico"],
                "avatar": {"thumbnails": [{"url": "https://img.example/avatar.jpg"}]},
            }
        },
    }
    html = "<html><script>var ytInitialData = " + json.dumps(initial, ensure_ascii=False) + ";</script></html>"
    monkeypatch.setattr("integrations.platforms.requests.get", lambda *args, **kwargs: FakeResponse(html))
    result = YouTubeAdapter(settings={}).fetch_channel_public("@canalpublico")
    assert result.ok
    assert result.data["youtube_id"] == "UC123"
    assert result.data["name"] == "Canal Público"
    assert result.data["handle"] == "@canalpublico"
    assert result.data["metrics_source"] == "youtube_public_page"
    assert result.data["thumbnail_url"].endswith("avatar.jpg")


def test_public_lookup_falls_back_to_open_graph_metadata(monkeypatch):
    html = """<html><head>
    <meta property='og:url' content='https://www.youtube.com/channel/UC999'>
    <meta property='og:title' content='Canal por metatags'>
    <meta property='og:description' content='Descrição por metatags'>
    <meta property='og:image' content='https://img.example/meta.jpg'>
    </head></html>"""

    def fake_get(url, **kwargs):
        if "/feeds/videos.xml" in url:
            return FakeResponse("<feed xmlns='http://www.w3.org/2005/Atom' xmlns:yt='http://www.youtube.com/xml/schemas/2015'><title>Canal por feed</title><yt:channelId>UC999</yt:channelId><entry/><entry/></feed>")
        return FakeResponse(html)

    monkeypatch.setattr("integrations.platforms.requests.get", fake_get)
    result = YouTubeAdapter(settings={}).fetch_channel_public("@canal")
    assert result.ok
    assert result.data["youtube_id"] == "UC999"
    assert result.data["name"] == "Canal por metatags"
    assert result.data["video_count"] == 2
    assert result.data["thumbnail_url"].endswith("meta.jpg")


def test_public_lookup_uses_rss_when_direct_channel_page_has_no_metadata(monkeypatch):
    channel_id = "UC1234567890ABCDEF"
    feed = "<feed xmlns='http://www.w3.org/2005/Atom' xmlns:yt='http://www.youtube.com/xml/schemas/2015'><title>Canal RSS</title><yt:channelId>UC1234567890ABCDEF</yt:channelId><entry/></feed>"

    def fake_get(url, **kwargs):
        if "/feeds/videos.xml" in url:
            return FakeResponse(feed)
        return FakeResponse("<html><body>consent</body></html>")

    monkeypatch.setattr("integrations.platforms.requests.get", fake_get)
    result = YouTubeAdapter(settings={}).fetch_channel_public(f"https://www.youtube.com/channel/{channel_id}/videos?hl=pt-BR")
    assert result.ok
    assert result.data["youtube_id"] == channel_id
    assert result.data["name"] == "Canal RSS"
    assert result.data["metrics_source"] == "youtube_public_feed"


def test_public_lookup_reports_nonexistent_channel_instead_of_empty_success(monkeypatch):
    payload = {
        "header": {"c4TabbedHeaderRenderer": {"channelId": "UC1234567890ABCDEF"}},
        "alerts": [{"alertRenderer": {"type": "ERROR", "text": {"simpleText": "Este canal não existe."}}}],
    }
    html = "<script>var ytInitialData = " + json.dumps(payload, ensure_ascii=False) + ";</script>"
    monkeypatch.setattr("integrations.platforms.requests.get", lambda *args, **kwargs: FakeResponse(html, 200))
    result = YouTubeAdapter(settings={}).fetch_channel_public("https://www.youtube.com/channel/UC1234567890ABCDEF")
    assert not result.ok
    assert "não existe" in result.message
    assert result.data["public_error"] == "Este canal não existe."


def test_public_lookup_rejects_non_youtube_url_without_request(monkeypatch):
    calls = []
    monkeypatch.setattr("integrations.platforms.requests.get", lambda *args, **kwargs: calls.append(args) or FakeResponse(""))
    result = YouTubeAdapter(settings={}).fetch_channel_public("https://example.com/channel/UC1234567890ABCDEF")
    assert not result.ok
    assert "youtube.com" in result.message
    assert calls == []


def test_public_lookup_does_not_report_id_only_page_as_success(monkeypatch):
    html = "<html><script>var ytInitialData = {\"responseContext\": {}};</script></html>"
    monkeypatch.setattr("integrations.platforms.requests.get", lambda *args, **kwargs: FakeResponse(html, 200))
    result = YouTubeAdapter(settings={}).fetch_channel_public("https://www.youtube.com/channel/UC1234567890ABCDEF")
    assert not result.ok
    assert "metadados públicos" in result.message
    assert result.data["youtube_id"] == "UC1234567890ABCDEF"


def test_api_lookup_reports_optional_key_instead_of_blocking_public_flow():
    result = YouTubeAdapter(settings={}).fetch_channel("@canalpublico")
    assert not result.ok
    assert result.data["status"] == "api_key_not_configured"
    assert "Data API Key própria" in result.message
    assert "OAuth Client ID" in result.message


def test_fetch_channel_videos_public_reads_latest_atom_entries_without_api_key(monkeypatch):
    feed = """<feed xmlns="http://www.w3.org/2005/Atom" xmlns:yt="http://www.youtube.com/xml/schemas/2015" xmlns:media="http://search.yahoo.com/mrss/">
      <title>Canal Vídeos</title><yt:channelId>UCVIDEOS123</yt:channelId>
      <entry><id>yt:video:video1</id><yt:videoId>video1</yt:videoId><title>Vídeo 1</title><published>2026-08-21T08:00:00+00:00</published><updated>2026-08-21T08:01:00+00:00</updated><link rel="alternate" href="https://www.youtube.com/watch?v=video1"/><media:group><media:thumbnail url="https://img.example/video1.jpg"/></media:group></entry>
      <entry><id>yt:video:video2</id><yt:videoId>video2</yt:videoId><title>Vídeo 2</title><published>2026-08-20T08:00:00+00:00</published><updated>2026-08-20T08:01:00+00:00</updated><link rel="alternate" href="https://www.youtube.com/watch?v=video2"/></entry>
    </feed>"""
    monkeypatch.setattr("integrations.platforms.requests.get", lambda *args, **kwargs: FakeResponse(feed))

    result = YouTubeAdapter(settings={}).fetch_channel_videos_public({"youtube_channel_id": "UCVIDEOS123"}, limit=10)

    assert result.ok
    assert len(result.data["videos"]) == 2
    assert result.data["videos"][0]["id"] == "youtube_video1"
    assert result.data["videos"][0]["title"] == "Vídeo 1"
    assert result.data["videos"][0]["thumbnail_url"].endswith("video1.jpg")
    assert result.data["videos"][1]["url"].endswith("video2")


def test_fetch_channel_videos_public_caps_result_at_ten(monkeypatch):
    entries = "".join(f"<entry><yt:videoId>video{index}</yt:videoId><title>Vídeo {index}</title></entry>" for index in range(15))
    feed = f'<feed xmlns="http://www.w3.org/2005/Atom" xmlns:yt="http://www.youtube.com/xml/schemas/2015">{entries}</feed>'
    monkeypatch.setattr("integrations.platforms.requests.get", lambda *args, **kwargs: FakeResponse(feed))

    result = YouTubeAdapter(settings={}).fetch_channel_videos_public("UCVIDEOS123", limit=50)

    assert result.ok
    assert len(result.data["videos"]) == 10


def test_tiktok_adapter_reads_first_complete_api_card_before_legacy_credentials():
    adapter = TikTokAdapter({
        "tiktok_api_cards": [
            {"id": "incomplete", "client_id": "only-id", "client_secret": ""},
            {"id": "ready", "client_id": "card-client", "client_secret": "card-secret"},
        ],
        "tiktok_client_key": "legacy-client",
        "tiktok_client_secret": "legacy-secret",
    })
    assert adapter.client_key == "card-client"
    assert adapter.client_secret == "card-secret"
    assert adapter.configured is True


def test_tiktok_adapter_keeps_legacy_credentials_when_cards_are_absent():
    adapter = TikTokAdapter({"tiktok_client_key": "legacy-client", "tiktok_client_secret": "legacy-secret"})
    assert adapter.client_key == "legacy-client"
    assert adapter.client_secret == "legacy-secret"
    assert adapter.configured is True
