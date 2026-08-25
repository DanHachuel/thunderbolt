import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from hermes_ui.thumbnails import list_thumbnail_tasks, normalize_thumbnail_task, regenerate_thumbnail


class ThumbnailPipelineTests(unittest.TestCase):
    def test_normalize_prefers_title_and_artifact_fallback(self):
        task = {
            "id": "video-1",
            "topic": "Tema de fallback",
            "channel_name": "Canal Teste",
            "thumbnail_status": "generated",
            "thumbnail_prompt": "A cinematic thumbnail",
            "artifacts": {"thumbnail": "missing.jpg"},
        }
        normalized = normalize_thumbnail_task(task)
        self.assertEqual(normalized["title"], "Tema de fallback")
        self.assertEqual(normalized["prompt"], "A cinematic thumbnail")
        self.assertEqual(normalized["task_id"], "video-1")

    def test_list_includes_prompt_only_and_generated_tasks_but_not_unrelated_tasks(self):
        tasks = [
            {"id": "with-prompt", "title": "Com prompt", "thumbnail_prompt": "prompt", "thumbnail_status": "prompt_ready"},
            {"id": "with-image", "title": "Com imagem", "artifacts": {"thumbnail": "thumb.jpg"}, "thumbnail_status": "generated"},
            {"id": "unrelated", "title": "Sem thumbnail"},
        ]
        with patch("hermes_ui.thumbnails.read_json", return_value=tasks):
            records = list_thumbnail_tasks()
        self.assertEqual([record["task_id"] for record in records], ["with-prompt", "with-image"])

    def test_regenerate_updates_task_without_removing_other_fields(self):
        tasks = [{
            "id": "video-1",
            "title": "Título do vídeo",
            "topic": "Tema",
            "thumbnail_prompt": "new prompt",
            "thumbnail_status": "prompt_ready",
            "thumbnail_variant": {"image_prompt": "new prompt", "overlay_text": "Texto"},
            "thumbnail_variants": [{"image_prompt": "new prompt"}],
            "artifacts": {"script": "/tmp/script.txt"},
            "state": "doing",
        }]
        captured = {}
        with tempfile.TemporaryDirectory() as directory:
            generated_path = Path(directory) / "new-thumbnail.jpg"

            def fake_generate(settings, prompt, *, topic, variant_index):
                captured.update({"settings": settings, "prompt": prompt, "topic": topic, "variant_index": variant_index})
                return generated_path

            with patch("hermes_ui.thumbnails.read_json", return_value=tasks), patch("hermes_ui.thumbnails.write_json", side_effect=lambda _name, value: captured.update({"saved": value})), patch("hermes_ui.thumbnails.generate_thumbnail_image", side_effect=fake_generate):
                task, image_path = regenerate_thumbnail("video-1", {"gemini_image_api_key": "key"})

        self.assertEqual(image_path, generated_path)
        self.assertEqual(captured["prompt"], "new prompt")
        self.assertEqual(captured["topic"], "Título do vídeo")
        self.assertEqual(captured["variant_index"], 0)
        self.assertEqual(task["state"], "doing")
        self.assertEqual(task["thumbnail_status"], "generated")
        self.assertEqual(task["artifacts"]["script"], "/tmp/script.txt")
        self.assertEqual(task["artifacts"]["thumbnail"], str(generated_path))
        self.assertEqual(task["thumbnail_variant"]["image_path"], str(generated_path))
        self.assertEqual(captured["saved"][0]["thumbnail_status"], "generated")

    def test_regenerate_requires_prompt(self):
        tasks = [{"id": "video-2", "title": "Sem prompt", "thumbnail_status": "not_generated"}]
        with patch("hermes_ui.thumbnails.read_json", return_value=tasks), self.assertRaisesRegex(RuntimeError, "não tem um prompt"):
            regenerate_thumbnail("video-2", {})


if __name__ == "__main__":
    unittest.main()

