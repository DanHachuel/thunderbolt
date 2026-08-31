from pathlib import Path
import unittest

from integrations.youtube_update import YOUTUBE_UPDATE_VIDEO, YouTubeVideoUpdater


class YouTubeUpdateTests(unittest.TestCase):
    def test_operation_is_explicit_and_channel_id_is_resolved(self):
        updater = YouTubeVideoUpdater({}, Path("/tmp/thunderbolt-test-storage"))
        result = updater.list_videos({"id": "channel-1", "youtube_id": "UC123456"})
        self.assertEqual(result.data["operation"], YOUTUBE_UPDATE_VIDEO)
        self.assertFalse(result.ok)
        self.assertEqual(result.data["videos"], [])

    def test_empty_title_is_rejected_without_api_call(self):
        updater = YouTubeVideoUpdater({}, Path("/tmp/thunderbolt-test-storage"))
        result = updater.update_video({"id": "video-1", "title": "Título actual", "description": "Descrição", "category_id": "22"}, title="", description="Descrição")
        self.assertFalse(result.ok)
        self.assertIn("título", result.message.lower())
        self.assertEqual(result.data["operation"], YOUTUBE_UPDATE_VIDEO)


if __name__ == "__main__":
    unittest.main()
