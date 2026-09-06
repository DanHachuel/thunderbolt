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


if __name__ == "__main__":
    unittest.main()
