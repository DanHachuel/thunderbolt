from unittest.mock import Mock, patch

from integrations import instagram_public


HTML = '''
<meta property="og:title" content="Creator (@creator)">
<meta property="og:description" content="123 followers, 456 following and 2 posts">
<meta property="og:image" content="https://img.example/avatar.jpg">
<script type="application/json">
{"edge_followed_by":{"count":123},"edge_follow":{"count":456},"edge_owner_to_timeline_media":{"count":2,"edges":[{"node":{"id":"post-1","shortcode":"ABC","display_url":"https://img.example/post.jpg","edge_media_to_caption":{"edges":[{"node":{"text":"Legenda"}}]}}}]}}
</script>
'''


def test_windows_profile_tries_requests_then_uses_playwright_html_parser():
    with patch.object(instagram_public.platform, "system", return_value="Windows"), \
         patch.object(instagram_public.requests, "get", side_effect=instagram_public.requests.RequestException("HTML instead of JSON")), \
         patch.object(instagram_public.shutil, "which", return_value=None), \
         patch.object(instagram_public, "_fetch_instagram_html_with_playwright", return_value=HTML) as playwright:
        result = instagram_public._fetch_web_profile_user("creator")

    assert result["biography"] == "123 followers, 456 following and 2 posts"
    assert result["edge_followed_by"]["count"] == 123
    assert result["edge_follow"]["count"] == 456
    assert result["edge_owner_to_timeline_media"]["edges"][0]["node"]["shortcode"] == "ABC"
    playwright.assert_called_once_with("https://www.instagram.com/creator/", "creator")


def test_windows_posts_use_the_same_html_parser_after_profile_fallback():
    with patch.object(instagram_public.platform, "system", return_value="Windows"), \
         patch.object(instagram_public, "_fetch_web_profile_user", return_value={}), \
         patch.object(instagram_public, "_fetch_instagram_html_with_playwright", return_value=HTML) as playwright:
        result = instagram_public.fetch_public_instagram_posts("@creator", limit=10)

    assert result.ok is True
    assert result.data["posts"][0]["id"] == "post-1"
    assert result.data["posts"][0]["caption"] == "Legenda"
    playwright.assert_called_once_with("https://www.instagram.com/creator/", "creator")


def test_playwright_failure_returns_empty_html_without_generic_data_fallback():
    with patch.dict("sys.modules", {"playwright": None}):
        # The public helper must keep the original empty-result contract on errors.
        with patch.object(instagram_public, "print") as output:
            result = instagram_public._fetch_instagram_html_with_playwright("https://www.instagram.com/creator/", "creator")
    assert result == ""
    output.assert_called_once()


def test_bio_preserves_metric_words_and_real_text():
    value = "606 seguidores, seguindo 3,432, 278 posts — Veja as fotos"
    assert instagram_public.normalize_instagram_bio(value) == value


def test_linux_html_path_remains_requests_based():
    response = Mock(status_code=200, text='<meta property="og:title" content="Creator"><meta property="og:description" content="Bio real">')
    with patch.object(instagram_public.platform, "system", return_value="Linux"), patch.object(instagram_public.requests, "get", return_value=response) as request:
        result = instagram_public.fetch_public_instagram_profile("@creator")
    assert result.ok is True
    assert result.data["bio"] == "Bio real"
    request.assert_called()
