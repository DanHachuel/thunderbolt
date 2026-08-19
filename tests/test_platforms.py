import json

from integrations.platforms import YouTubeAdapter, _extract_json_assignment, _parse_public_count


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


def test_api_lookup_reports_optional_key_instead_of_blocking_public_flow():
    result = YouTubeAdapter(settings={}).fetch_channel("@canalpublico")
    assert not result.ok
    assert "YOUTUBE_API_KEY" in result.message
