import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from hermes_ui import media_generation
from hermes_ui.creative_generation import generate_ugc_segment_prompts
from hermes_ui.provider_routing import RoutedResponse


class InfluencerWorkflowTests(unittest.TestCase):
    def test_motion_image_limits_and_extensions(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "reference.jpg"
            path.write_bytes(b"image")
            info = media_generation.validate_motion_control_file(path, kind="imagem")
            self.assertEqual(info["extension"], ".jpg")
            invalid = Path(temp_dir) / "reference.webp"
            invalid.write_bytes(b"image")
            with self.assertRaisesRegex(media_generation.MediaGenerationError, "jpg"):
                media_generation.validate_motion_control_file(invalid, kind="imagem")

    def test_motion_video_duration_is_checked(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "motion.mp4"
            path.write_bytes(b"video")
            probe = Mock(stdout="12.5\n")
            with patch.object(media_generation.shutil, "which", return_value="/usr/bin/ffprobe"), patch.object(media_generation.subprocess, "run", return_value=probe):
                info = media_generation.validate_motion_control_file(path, kind="vídeo")
            self.assertEqual(info["duration_seconds"], 12.5)
            self.assertEqual(info["size_bytes"], 5)

    def test_motion_video_rejects_duration_outside_kie_range(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "motion.mp4"
            path.write_bytes(b"video")
            with patch.object(media_generation.shutil, "which", return_value="ffprobe"), patch.object(media_generation.subprocess, "run", return_value=Mock(stdout="2.0\n")):
                with self.assertRaisesRegex(media_generation.MediaGenerationError, "entre 3 e 30"):
                    media_generation.validate_motion_control_file(path, kind="vídeo")

    def test_upload_kie_file_uses_selected_card_and_returns_download_url(self):
        response = Mock(status_code=200)
        response.json.return_value = {"code": 200, "data": {"downloadUrl": "https://files.kie.ai/input.jpg"}}
        card = {"provider": "kie_ai", "api_key": "secret-card"}
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "input.jpg"
            path.write_bytes(b"image")
            with patch.object(media_generation.requests, "post", return_value=response) as post:
                url = media_generation.upload_kie_file(path, card)
        self.assertEqual(url, "https://files.kie.ai/input.jpg")
        self.assertEqual(post.call_args.args[0], media_generation.KIE_FILE_UPLOAD_ENDPOINT)
        self.assertEqual(post.call_args.kwargs["headers"]["Authorization"], "Bearer secret-card")
        self.assertEqual(post.call_args.kwargs["data"]["uploadPath"], "thunderbolt/influencers")

    def test_motion_payload_uses_kling_market_contract_and_polling(self):
        response = Mock(status_code=200)
        response.json.return_value = {"code": 200, "data": {"taskId": "motion-task"}}
        card = {"provider": "kie_ai", "api_key": "secret", "base_url": "https://api.kie.ai/api/v1"}
        def route(_settings, *, pool, cards, request):
            request(dict(cards[0]))
            return RoutedResponse(card=dict(cards[0]), payload=response.json.return_value, attempts=())
        with patch.object(media_generation.requests, "post", return_value=response) as post, patch.object(media_generation, "route_json_request", side_effect=route), patch.object(media_generation, "_poll_kie_task", return_value=["https://files.kie.ai/result.mp4"]), patch.object(media_generation, "_download_video_url", return_value=Path("result.mp4")):
            output, task_id = media_generation.generate_motion_control_video({}, card, image_url="https://files.kie.ai/image.jpg", video_url="https://files.kie.ai/motion.mp4", prompt="Aplicar o movimento")
        body = post.call_args.kwargs["json"]
        self.assertEqual(task_id, "motion-task")
        self.assertEqual(output, Path("result.mp4"))
        self.assertEqual(body["model"], "kling-2.6/motion-control")
        self.assertEqual(body["input"]["input_urls"], ["https://files.kie.ai/image.jpg"])
        self.assertEqual(body["input"]["video_urls"], ["https://files.kie.ai/motion.mp4"])
        self.assertEqual(body["input"]["character_orientation"], "video")
        self.assertNotIn("callback", json.dumps(body).lower())

    def test_veo_payload_uses_specific_endpoint_and_eight_second_segment(self):
        response = Mock(status_code=200)
        response.json.return_value = {"code": 200, "data": {"taskId": "veo-task"}}
        card = {"provider": "kie_ai", "api_key": "secret", "model": "veo3_fast", "base_url": "https://api.kie.ai/api/v1"}
        def route(_settings, *, pool, cards, request):
            request(dict(cards[0]))
            return RoutedResponse(card=dict(cards[0]), payload=response.json.return_value, attempts=())
        with tempfile.TemporaryDirectory() as temp_dir:
            destination = Path(temp_dir) / "segment.mp4"
            with patch.object(media_generation.requests, "post", return_value=response) as post, patch.object(media_generation, "route_json_request", side_effect=route), patch.object(media_generation, "_poll_kie_task", return_value=["https://files.kie.ai/segment.mp4"]), patch.object(media_generation, "_download_video_url", return_value=destination):
                output, task_id = media_generation.generate_ugc_segment({}, card, image_url="https://files.kie.ai/product.jpg", prompt="Mostrar a embalagem", output_path=destination)
        body = post.call_args.kwargs["json"]
        self.assertEqual(post.call_args.args[0], "https://api.kie.ai/api/v1/veo/generate")
        self.assertEqual(output, destination)
        self.assertEqual(task_id, "veo-task")
        self.assertEqual(body["imageUrls"], ["https://files.kie.ai/product.jpg"])
        self.assertEqual(body["model"], "veo3_fast")
        self.assertEqual(body["duration"], 8)
        self.assertEqual(body["resolution"], "720p")

    def test_ugc_generation_runs_two_segments_and_local_concat(self):
        card = {"provider": "kie_ai", "api_key": "secret", "model": "veo3_fast"}
        with tempfile.TemporaryDirectory() as temp_dir:
            output = Path(temp_dir) / "final.mp4"
            with patch.object(media_generation, "generate_ugc_segment", side_effect=[(Path("one.mp4"), "task-1"), (Path("two.mp4"), "task-2")]) as segment, patch.object(media_generation, "concatenate_video_files", return_value=output) as concat:
                result, task_ids = media_generation.generate_ugc_product_video({}, card, image_url="https://files.kie.ai/product.jpg", prompts=["primeiro", "segundo"], output_path=output)
        self.assertEqual(result, output)
        self.assertEqual(task_ids, ["task-1", "task-2"])
        self.assertEqual(segment.call_count, 2)
        self.assertEqual(concat.call_args.args[1], output)

    def test_explicit_two_part_script_avoids_llm_call(self):
        with patch("hermes_ui.creative_generation._chat_json") as chat:
            prompts = generate_ugc_segment_prompts({}, "Mostrar produto.\n---\nConcluir demonstração.")
        chat.assert_not_called()
        self.assertEqual(len(prompts), 2)
        self.assertIn("Mostrar produto", prompts[0])
        self.assertIn("Concluir demonstração", prompts[1])
        self.assertTrue(all("Sem texto" in item for item in prompts))


if __name__ == "__main__":
    unittest.main()
