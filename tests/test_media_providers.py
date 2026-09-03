from __future__ import annotations

import base64
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from hermes_ui import media_generation, media_providers
from hermes_ui.provider_routing import POOL_IMAGE, RoutedResponse


class MediaProvidersTests(unittest.TestCase):
    def test_catalog_contains_requested_current_providers_and_excludes_deprecated_names(self):
        codes = {item["code"] for item in media_providers.media_provider_catalog()}
        self.assertTrue({"nano_banana", "pollinations", "agnes", "huggingface", "cloudflare_workers_ai", "inferenceport", "alibaba_cloud", "kie_ai", "fal_ai", "heygen", "openrouter"}.issubset(codes))
        self.assertNotIn("nexaapi", codes)
        self.assertNotIn("openimagegen", codes)
        self.assertEqual(
            set(media_providers.FULL_IA_VIDEO_PROVIDER_CODES),
            {"fal_ai", "kie_ai", "agnes", "nano_banana", "replicate", "pollinations", "huggingface", "inferenceport", "heygen", "openrouter"},
        )

    def test_legacy_nano_settings_migrate_to_image_card(self):
        migrated, changed = media_providers.ensure_media_provider_cards(
            {
                "gemini_image_api_key": "secret",
                "gemini_image_model": "gemini-3.1-flash-image",
                "gemini_image_aspect_ratio": "16:9",
                "gemini_image_size": "1K",
            }
        )
        self.assertTrue(changed)
        self.assertEqual(migrated["media_provider_cards"][0]["provider"], "nano_banana")
        self.assertEqual(migrated["media_provider_cards"][0]["api_key"], "secret")
        self.assertEqual(migrated["media_image_active_card_id"], "media-nano-banana-default")

    def test_nano_card_defaults_are_internal_and_not_catalog_extra_fields(self):
        card = media_providers.normalize_media_card({"provider": "nano_banana"})
        definition = media_providers.media_provider_definition("nano_banana")
        self.assertEqual(card["aspect_ratio"], "16:9")
        self.assertEqual(card["image_size"], "1K")
        self.assertNotIn("aspect_ratio", definition.extra_fields)
        self.assertNotIn("image_size", definition.extra_fields)

    def test_pools_filter_capabilities_and_use_active_card_only_as_priority_tiebreaker(self):
        settings = {
            "media_provider_cards": [
                {"id": "video", "provider": "fal_ai", "model": "video-model", "supports_video": True, "supports_image": False, "enabled": True, "priority": 2},
                {"id": "active-image", "provider": "nano_banana", "model": "image-model", "supports_video": False, "supports_image": True, "enabled": True, "priority": 3},
                {"id": "priority-image", "provider": "pollinations", "model": "flux", "supports_video": False, "supports_image": True, "enabled": True, "priority": 1},
            ],
            "media_image_active_card_id": "active-image",
            "media_video_active_card_id": "video",
        }
        self.assertEqual([item["id"] for item in media_providers.media_cards_for_pool(settings, "image")], ["priority-image", "active-image"])
        self.assertEqual([item["id"] for item in media_providers.media_cards_for_pool(settings, "video")], ["video"])

    def test_media_cards_are_reordered_by_priority_when_migrated_or_saved(self):
        settings = {
            "media_provider_cards": [
                {"id": "second", "provider": "pollinations", "supports_image": True, "priority": 2},
                {"id": "first", "provider": "nano_banana", "supports_image": True, "priority": 1},
            ]
        }
        migrated, changed = media_providers.ensure_media_provider_cards(settings)
        self.assertTrue(changed)
        self.assertEqual([item["id"] for item in migrated[media_providers.MEDIA_CARDS_KEY]], ["first", "second"])

        saved = media_providers.apply_media_provider_cards_to_settings(
            {},
            [
                {"id": "third", "provider": "pollinations", "supports_image": True, "priority": 3},
                {"id": "first", "provider": "nano_banana", "supports_image": True, "priority": 1},
                {"id": "second", "provider": "agnes", "supports_image": True, "priority": 2},
            ],
        )
        self.assertEqual([item["id"] for item in saved[media_providers.MEDIA_CARDS_KEY]], ["first", "second", "third"])

    def test_openai_compatible_image_base64_is_saved(self):
        encoded = base64.b64encode(b"image").decode("ascii")
        card = {
            "id": "hf",
            "provider": "huggingface",
            "api_key": "secret",
            "model": "black-forest-labs/FLUX.1-dev",
            "base_url": "https://router.huggingface.co/v1",
            "api_style": "huggingface",
        }
        routed = RoutedResponse(card=card, payload={"data": [{"b64_json": encoded}]}, attempts=())
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch.object(media_generation, "STORAGE", Path(temp_dir)), patch.object(media_generation, "ensure_storage", lambda: None), patch.object(media_generation, "route_json_request", return_value=routed):
                output = media_generation.generate_image_for_card({}, card, "a clean image", topic="topic")
            self.assertEqual(output.read_bytes(), b"image")
            self.assertEqual(output.parent, Path(temp_dir) / "thumbnails")

    def test_openrouter_image_request_uses_dedicated_images_endpoint(self):
        response = Mock(status_code=200)
        card = {"provider": "openrouter", "api_style": "openrouter", "api_key": "secret", "base_url": "https://openrouter.ai/api/v1", "model": "openai/gpt-image-2"}
        with patch.object(media_generation.requests, "post", return_value=response) as post:
            media_generation._image_request(card, "clean image")
        self.assertEqual(post.call_args.args[0], "https://openrouter.ai/api/v1/images")
        self.assertEqual(post.call_args.kwargs["headers"]["Authorization"], "Bearer secret")
        body = post.call_args.kwargs["json"]
        self.assertEqual(body["model"], "openai/gpt-image-2")
        self.assertEqual(body["n"], 1)
        self.assertEqual(body["aspect_ratio"], "16:9")
        self.assertNotIn("response_format", body)

    def test_openrouter_video_request_uses_async_videos_endpoint(self):
        response = Mock(status_code=200)
        card = {"provider": "openrouter", "api_style": "openrouter", "api_key": "secret", "base_url": "https://openrouter.ai/api/v1", "model": "google/veo-3.1"}
        with patch.object(media_generation.requests, "post", return_value=response) as post:
            media_generation._video_request(card, "video prompt")
        self.assertEqual(post.call_args.args[0], "https://openrouter.ai/api/v1/videos")
        body = post.call_args.kwargs["json"]
        self.assertEqual(body["model"], "google/veo-3.1")
        self.assertEqual(body["aspect_ratio"], "16:9")
        self.assertEqual(body["resolution"], "1080p")

    def test_openrouter_video_polling_reads_unsigned_url(self):
        response = Mock(status_code=200)
        response.json.return_value = {"status": "completed", "unsigned_urls": ["https://files.openrouter.ai/video.mp4"]}
        card = {"provider": "openrouter", "api_style": "openrouter", "api_key": "secret", "base_url": "https://openrouter.ai/api/v1"}
        with patch.object(media_generation.requests, "get", return_value=response) as get:
            output = media_generation._poll_video(card, "job-123", attempts=1)
        self.assertEqual(output, "https://files.openrouter.ai/video.mp4")
        self.assertEqual(get.call_args.args[0], "https://openrouter.ai/api/v1/videos/job-123")

    def test_nano_card_delegates_to_existing_gemini_adapter(self):
        card = {"id": "nano", "provider": "nano_banana", "api_key": "secret", "model": "gemini-3.1-flash-image"}
        with patch.object(media_generation, "generate_thumbnail_image", return_value=Path("thumbnail.jpg")) as generator:
            output = media_generation.generate_image_for_card({}, card, "prompt", topic="topic", variant_index=2)
        self.assertEqual(output, Path("thumbnail.jpg"))
        self.assertEqual(generator.call_args.args[0]["gemini_image_api_key"], "secret")
        self.assertIn("16:9", generator.call_args.args[1])
        self.assertIn("1280x720 minimum", generator.call_args.args[1])
        self.assertEqual(generator.call_args.kwargs["variant_index"], 2)

    def test_pollinations_image_request_uses_landscape_size_parameter(self):
        response = Mock(status_code=200)
        card = {"provider": "pollinations", "model": "flux", "base_url": "https://gen.pollinations.ai/v1", "api_style": "openai_compatible"}
        with patch.object(media_generation.requests, "post", return_value=response) as post:
            media_generation._image_request(card, "clean image")
        prompt = post.call_args.kwargs["json"]["prompt"]
        self.assertIn("16:9", prompt)
        self.assertIn("1792x1024", prompt)
        self.assertEqual(post.call_args.kwargs["json"]["size"], "1792x1024")
        self.assertNotIn("aspect_ratio", post.call_args.kwargs["json"])

    def test_agnes_image_request_uses_documented_contract_and_timeout(self):
        response = Mock(status_code=200)
        card = {"provider": "agnes", "model": "agnes-image-2.1-flash", "base_url": "https://apihub.agnes-ai.com/v1", "api_style": "agnes"}
        with patch.object(media_generation.requests, "post", return_value=response) as post:
            media_generation._image_request(card, "clean image")
        body = post.call_args.kwargs["json"]
        self.assertEqual(post.call_args.args[0], "https://apihub.agnes-ai.com/v1/images/generations")
        self.assertEqual(body["model"], "agnes-image-2.1-flash")
        self.assertEqual(body["size"], "1K")
        self.assertEqual(body["ratio"], "16:9")
        self.assertTrue(body["return_base64"])
        self.assertEqual(body["extra_body"], {"response_format": "b64_json"})
        self.assertNotIn("response_format", body)
        self.assertEqual(post.call_args.kwargs["timeout"], media_generation.AGNES_IMAGE_TIMEOUT_SECONDS)

    def test_other_openai_compatible_image_request_does_not_receive_pollinations_size(self):
        response = Mock(status_code=200)
        card = {"provider": "huggingface", "model": "black-forest-labs/FLUX.1-dev", "base_url": "https://router.huggingface.co/v1", "api_style": "huggingface"}
        with patch.object(media_generation.requests, "post", return_value=response) as post:
            media_generation._image_request(card, "clean image")
        prompt = post.call_args.kwargs["json"]["prompt"]
        self.assertIn("16:9", prompt)
        self.assertIn("1280x720 minimum", prompt)
        self.assertNotIn("size", post.call_args.kwargs["json"])
        self.assertNotIn("aspect_ratio", post.call_args.kwargs["json"])

    def test_video_request_keeps_size_and_aspect_ratio_inside_prompt(self):
        response = Mock(status_code=200)
        card = {"provider": "pollinations", "model": "video-model", "base_url": "https://gen.pollinations.ai/v1", "api_style": "openai_compatible"}
        with patch.object(media_generation.requests, "post", return_value=response) as post:
            media_generation._video_request(card, "video prompt")
        prompt = post.call_args.kwargs["json"]["prompt"]
        self.assertIn("16:9", prompt)
        self.assertIn("1080p", prompt)
        self.assertNotIn("size", post.call_args.kwargs["json"])
        self.assertNotIn("aspect_ratio", post.call_args.kwargs["json"])

    def test_image_request_includes_mandatory_lettering_for_initial_generation(self):
        response = Mock(status_code=200)
        card = {"provider": "pollinations", "model": "flux", "base_url": "https://gen.pollinations.ai/v1", "api_style": "openai_compatible"}
        with patch.object(media_generation.requests, "post", return_value=response) as post:
            media_generation._image_request(card, "clean image", topic="A new topic", lettering_text="EXACT TEXT")
        prompt = post.call_args.kwargs["json"]["prompt"]
        self.assertIn("MANDATORY LETTERING LAYER", prompt)
        self.assertIn("EXACT HEADLINE TO RENDER: <<<EXACT TEXT>>>", prompt)

    def test_heygen_video_request_uses_v3_avatar_contract_and_api_key_header(self):
        response = Mock(status_code=200)
        card = {
            "provider": "heygen",
            "api_style": "heygen",
            "api_key": "heygen-secret",
            "base_url": "https://api.heygen.com",
            "avatar_id": "avatar-123",
            "voice_id": "voice-456",
        }
        with patch.object(media_generation.requests, "post", return_value=response) as post:
            media_generation._video_request(card, "script do vídeo")
        self.assertEqual(post.call_args.args[0], "https://api.heygen.com/v3/videos")
        self.assertEqual(post.call_args.kwargs["headers"]["X-Api-Key"], "heygen-secret")
        self.assertNotIn("Authorization", post.call_args.kwargs["headers"])
        body = post.call_args.kwargs["json"]
        self.assertEqual(body["type"], "avatar")
        self.assertEqual(body["avatar_id"], "avatar-123")
        self.assertEqual(body["voice_id"], "voice-456")
        self.assertEqual(body["aspect_ratio"], "16:9")
        self.assertEqual(body["output_format"], "mp4")
        self.assertIn("script do vídeo", body["script"])

    def test_heygen_polling_reads_completed_video_url_from_v3_data(self):
        response = Mock(status_code=200)
        response.json.return_value = {"data": {"status": "completed", "video_url": "https://files.heygen.ai/video.mp4"}}
        card = {"provider": "heygen", "api_style": "heygen", "api_key": "secret", "base_url": "https://api.heygen.com"}
        with patch.object(media_generation.requests, "get", return_value=response) as get:
            output = media_generation._poll_video(card, "video-123", attempts=1)
        self.assertEqual(output, "https://files.heygen.ai/video.mp4")
        self.assertEqual(get.call_args.args[0], "https://api.heygen.com/v3/videos/video-123")
        self.assertEqual(get.call_args.kwargs["headers"]["X-Api-Key"], "secret")

    def test_video_result_accepts_direct_url_or_task_id(self):
        self.assertEqual(media_generation._video_result({"url": "https://example/video.mp4"}), ("https://example/video.mp4", ""))
        self.assertEqual(media_generation._video_result({"task_id": "task-1"}), ("", "task-1"))

    def test_image_pool_fails_over_only_for_retryable_provider_errors(self):
        cards = [
            {"id": "first", "provider": "huggingface", "supports_image": True, "enabled": True},
            {"id": "second", "provider": "pollinations", "supports_image": True, "enabled": True},
        ]
        with patch.object(media_generation, "media_cards_for_pool", return_value=cards), patch.object(
            media_generation,
            "generate_image_for_card",
            side_effect=[media_generation.MediaGenerationError("HTTP 429 quota"), Path("fallback.jpg")],
        ) as generate:
            output = media_generation.generate_image_from_pool({}, "prompt")
        self.assertEqual(output, Path("fallback.jpg"))
        self.assertEqual(generate.call_count, 2)

    def test_image_pool_fails_over_for_http_402_quota_error(self):
        cards = [
            {"id": "first", "provider": "pollinations", "supports_image": True, "enabled": True},
            {"id": "second", "provider": "huggingface", "supports_image": True, "enabled": True},
        ]
        with patch.object(media_generation, "media_cards_for_pool", return_value=cards), patch.object(
            media_generation,
            "generate_image_for_card",
            side_effect=[media_generation.MediaGenerationError("Provider devolveu HTTP 402"), Path("fallback.jpg")],
        ) as generate:
            output = media_generation.generate_image_from_pool({}, "prompt")
        self.assertEqual(output, Path("fallback.jpg"))
        self.assertEqual(generate.call_count, 2)

    def test_image_pool_does_not_fail_over_for_invalid_payload(self):
        cards = [
            {"id": "first", "provider": "huggingface", "supports_image": True, "enabled": True},
            {"id": "second", "provider": "pollinations", "supports_image": True, "enabled": True},
        ]
        with patch.object(media_generation, "media_cards_for_pool", return_value=cards), patch.object(
            media_generation,
            "generate_image_for_card",
            side_effect=media_generation.MediaGenerationError("HTTP 400 invalid request"),
        ) as generate:
            with self.assertRaises(media_generation.MediaGenerationError):
                media_generation.generate_image_from_pool({}, "prompt")
        self.assertEqual(generate.call_count, 1)

    def test_image_pool_reports_each_provider_failure_when_all_fail(self):
        cards = [
            {"id": "first", "provider": "agnes", "supports_image": True, "enabled": True},
            {"id": "second", "provider": "nano_banana", "supports_image": True, "enabled": True},
        ]
        with patch.object(media_generation, "media_cards_for_pool", return_value=cards), patch.object(
            media_generation,
            "generate_image_for_card",
            side_effect=[media_generation.MediaGenerationError("timeout"), media_generation.MediaGenerationError("HTTP 429 quota")],
        ) as generate:
            with self.assertRaises(media_generation.MediaGenerationError) as raised:
                media_generation.generate_image_from_pool({}, "prompt")
        self.assertIn("agnes: timeout", str(raised.exception))
        self.assertIn("nano_banana: HTTP 429 quota", str(raised.exception))
        self.assertEqual(generate.call_count, 2)

    def test_video_pool_fails_over_for_transient_provider_error(self):
        cards = [
            {"id": "first", "provider": "fal_ai", "supports_video": True, "enabled": True},
            {"id": "second", "provider": "pollinations", "supports_video": True, "enabled": True},
        ]
        with patch.object(media_generation, "media_cards_for_pool", return_value=cards), patch.object(
            media_generation,
            "generate_video_for_card",
            side_effect=[media_generation.MediaGenerationError("timeout"), Path("fallback.mp4")],
        ) as generate:
            output = media_generation.generate_video_from_pool({}, "prompt")
        self.assertEqual(output, Path("fallback.mp4"))
        self.assertEqual(generate.call_count, 2)


if __name__ == "__main__":
    unittest.main()
