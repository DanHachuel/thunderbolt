import unittest
from pathlib import Path
from unittest.mock import patch

from hermes_ui.creative_generation import CreativeGenerationError, generate_video_keywords


ROOT = Path(__file__).resolve().parents[1]
MAIN_SOURCE = (ROOT / "app" / "main.py").read_text(encoding="utf-8")
PIPELINE_SOURCE = (ROOT / "hermes_ui" / "pipeline_worker.py").read_text(encoding="utf-8")
LANGUAGES_SOURCE = (ROOT / "hermes_ui" / "languages.py").read_text(encoding="utf-8")


class VideoCreationAITests(unittest.TestCase):
    def test_video_creation_has_one_subject_and_one_combined_generation_button(self):
        self.assertNotIn('"Tópico ou briefing"', MAIN_SOURCE)
        self.assertIn('"Video Subject"', MAIN_SOURCE)
        self.assertIn('key=f"{prefix}_generate_video_content"', MAIN_SOURCE)
        self.assertIn('on_click=generate_content_callback', MAIN_SOURCE)
        self.assertIn('generate_video_content_for_ui(', MAIN_SOURCE)
        self.assertIn('st.session_state[f"{prefix}_video_script"] = result["script"]', MAIN_SOURCE)
        self.assertIn('st.session_state[f"{prefix}_video_keywords"] = ", ".join(result["keywords"])', MAIN_SOURCE)
        self.assertIn('topic_value = str(generation_settings.get("video_subject") or "").strip()', MAIN_SOURCE)

    def test_channel_voice_is_synchronised_before_audio_selectbox(self):
        self.assertIn('channel_voice = str(channel.get("default_voice") or channel.get("voice") or "").strip()', MAIN_SOURCE)
        self.assertIn('st.session_state[f"{prefix}_voice"] = channel_voice', MAIN_SOURCE)
        self.assertIn('channel_state_key = f"{prefix}_voice_channel_id"', MAIN_SOURCE)
        self.assertIn('channel=selected_one', MAIN_SOURCE)

    def test_pipeline_uses_reviewed_script_and_keywords_when_present(self):
        self.assertIn('provided_script = str(generation_settings.get("video_script") or "").strip()', PIPELINE_SOURCE)
        self.assertIn('provided_keywords = generation_settings.get("video_keywords")', PIPELINE_SOURCE)
        self.assertIn('save_script_document(script)', PIPELINE_SOURCE)

    def test_keywords_are_normalised_and_bounded(self):
        with patch(
            "hermes_ui.creative_generation._chat_json",
            return_value={"keywords": ["#AI", "ai", "faceless video", "finance"]},
        ):
            result = generate_video_keywords(
                {},
                {"id": "channel-1", "name": "Brick by Brick Wealth"},
                "How AI changes investing",
                "A script about practical investing and artificial intelligence.",
            )
        self.assertEqual(result, ["AI", "faceless video", "finance"])
        self.assertLessEqual(len(result), 15)

    def test_keywords_require_subject_and_script(self):
        with self.assertRaises(CreativeGenerationError):
            generate_video_keywords({}, {}, "", "script")
        with self.assertRaises(CreativeGenerationError):
            generate_video_keywords({}, {}, "subject", "")

    def test_generation_button_is_translated_for_all_supported_languages(self):
        languages = ("pt", "en", "zh", "de", "vi", "tr", "ru", "es", "id", "it")
        source = LANGUAGES_SOURCE.split("VIDEO_GENERATION_TRANSLATIONS", 1)[1]
        for language in languages:
            block = source.split(f'    "{language}": {{', 1)[1].split("    },", 1)[0]
            self.assertIn('Gerar tópico, roteiro e palavras-chave com IA', block)


if __name__ == "__main__":
    unittest.main()
