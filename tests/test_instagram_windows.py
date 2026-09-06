import unittest
from unittest.mock import patch

from integrations import instagram_public


class InstagramWindowsRegressionTests(unittest.TestCase):
    def test_country_from_bio_is_only_a_fallback_pattern(self):
        self.assertEqual(instagram_public._country_from_bio_fallback("Creator based in Brazil"), "Brazil")
        self.assertEqual(instagram_public._country_from_bio_fallback("Criador de Portugal"), "Portugal")
        self.assertEqual(instagram_public._country_from_bio_fallback("Creator and photographer"), "")

    def test_profile_data_preserves_following_and_bio(self):
        data = instagram_public._profile_data_from_api(
            {
                "id": "42",
                "username": "conta",
                "biography": "Creator from Brazil",
                "edge_followed_by": {"count": 1200},
                "edge_follow": {"count": 340},
                "edge_owner_to_timeline_media": {"count": 18, "edges": []},
            },
            {"username": "conta", "handle": "@conta", "url": "https://www.instagram.com/conta/"},
        )
        self.assertEqual(data["bio"], "Creator from Brazil")
        self.assertEqual(data["subscriber_count"], 1200)
        self.assertEqual(data["following_count"], 340)
        self.assertEqual(data["country"], "Brazil")

    def test_windows_missing_curl_is_logged_and_does_not_crash(self):
        with patch.object(instagram_public.os, "name", "nt"), \
             patch.object(instagram_public, "_WINDOWS_PLAYWRIGHT_CHECKED", True), \
             patch.object(instagram_public.shutil, "which", return_value=None), \
             patch.object(instagram_public, "_fetch_web_profile_user", return_value=None), \
             patch.object(instagram_public.requests, "get", side_effect=instagram_public.requests.RequestException("offline")) as request:
            result = instagram_public.fetch_public_instagram_profile("@conta")
        self.assertFalse(result.ok)
        request.assert_called_once()

    def test_windows_uses_public_mode_when_environment_is_empty(self):
        with patch.object(instagram_public.os, "name", "nt"), \
             patch.dict(instagram_public.os.environ, {}, clear=True):
            cookies = instagram_public._instagram_cookies()
        self.assertEqual(cookies, {})

    def test_windows_profile_skips_requests_and_curl(self):
        expected = {"username": "conta", "biography": "Bio"}
        with patch.object(instagram_public.platform, "system", return_value="Windows"), \
             patch.object(instagram_public, "_fetch_profile_with_playwright", return_value=expected) as playwright, \
             patch.object(instagram_public.requests, "get", side_effect=AssertionError("HTTP não permitido no Windows")), \
             patch.object(instagram_public.shutil, "which", side_effect=AssertionError("curl não permitido no Windows")):
            result = instagram_public._fetch_web_profile_user("conta")
        self.assertEqual(result, expected)
        playwright.assert_called_once()

    def test_windows_posts_skip_profile_requests_and_curl(self):
        expected = [{"id": "post-1", "url": "https://www.instagram.com/p/post-1/"}]
        with patch.object(instagram_public.platform, "system", return_value="Windows"), \
             patch.object(instagram_public, "_fetch_posts_with_playwright", return_value=expected) as playwright, \
             patch.object(instagram_public, "_fetch_web_profile_user", side_effect=AssertionError("perfil HTTP não permitido")), \
             patch.object(instagram_public.requests, "get", side_effect=AssertionError("HTTP não permitido no Windows")):
            result = instagram_public.fetch_public_instagram_posts("@conta", limit=10)
        self.assertTrue(result.ok)
        self.assertEqual(result.data["posts"], expected)
        playwright.assert_called_once()

    def test_shared_data_profile_preserves_bio_metrics_and_posts(self):
        document = '''<script>window._sharedData = {"entry_data":{"ProfilePage":[{"graphql":{"user":{
            "username":"conta","biography":"Bio real com seguidores e seguindo",
            "edge_followed_by":{"count":1200},"edge_follow":{"count":340},
            "edge_owner_to_timeline_media":{"count":2,"edges":[
                {"node":{"id":"1","shortcode":"ABC","display_url":"https://img/1.jpg","edge_media_to_caption":{"edges":[{"node":{"text":"Legenda"}}]}}}
            ]}}}]}};</script>'''
        users = instagram_public._profile_users_from_document(document)
        self.assertEqual(len(users), 1)
        data = instagram_public._profile_data_from_api(users[0], {"username": "conta", "handle": "@conta", "url": "https://www.instagram.com/conta/"})
        self.assertEqual(data["bio"], "Bio real com seguidores e seguindo")
        self.assertEqual(data["subscriber_count"], 1200)
        self.assertEqual(data["following_count"], 340)
        self.assertEqual(data["post_count"], 2)

    def test_windows_profile_failure_does_not_fallback_to_requests(self):
        with patch.object(instagram_public.platform, "system", return_value="Windows"), \
             patch.object(instagram_public, "_fetch_profile_with_playwright", return_value=None), \
             patch.object(instagram_public, "fetch_profile_instaloader", return_value=None), \
             patch.object(instagram_public.requests, "get", side_effect=AssertionError("HTTP não permitido no Windows")):
            result = instagram_public.fetch_public_instagram_profile("@conta")
        self.assertFalse(result.ok)

    def test_windows_profile_uses_instaloader_when_playwright_is_empty(self):
        expected = {"username": "conta", "biography": "Bio fallback", "follower_count": 12, "following_count": 3, "_instagram_source": "instaloader"}
        with patch.object(instagram_public.platform, "system", return_value="Windows"), \
             patch.object(instagram_public, "_fetch_profile_with_playwright", return_value=None), \
             patch.object(instagram_public, "fetch_profile_instaloader", return_value=expected) as fallback:
            result = instagram_public._fetch_web_profile_user("conta")
        self.assertEqual(result, expected)
        fallback.assert_called_once_with("conta")

    def test_windows_posts_use_instaloader_when_playwright_is_empty(self):
        expected = [{"id": "post-1", "shortcode": "ABC", "image_url": "https://img/1.jpg"}]
        with patch.object(instagram_public.platform, "system", return_value="Windows"), \
             patch.object(instagram_public, "_fetch_posts_with_playwright", return_value=[]), \
             patch.object(instagram_public, "fetch_posts_instaloader", return_value=expected) as fallback:
            result = instagram_public.fetch_public_instagram_posts("@conta", limit=10)
        self.assertTrue(result.ok)
        self.assertEqual(result.data["posts"], expected)
        fallback.assert_called_once_with("conta", 10)


if __name__ == "__main__":
    unittest.main()
