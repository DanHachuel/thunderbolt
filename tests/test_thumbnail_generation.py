import base64
import json
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

from hermes_ui import thumbnail_generation



def test_thumbnail_requires_a_dedicated_gemini_image_key():
    try:
        thumbnail_generation.generate_thumbnail_image({}, "A thumbnail prompt")
    except thumbnail_generation.ThumbnailGenerationError as exc:
        assert "Configuração API > API Keys > Serviços e modelos" in str(exc)
    else:
        raise AssertionError("A geração deveria exigir a API key Nano Banana")



def test_thumbnail_uses_interactions_api_and_saves_inline_image():
    image_bytes = b"fake-jpeg-bytes"
    encoded = base64.b64encode(image_bytes).decode("ascii")
    response = Mock(status_code=200)
    response.json.return_value = {
        "status": "completed",
        "steps": [{"type": "model_output", "content": [{"type": "image", "data": encoded, "mime_type": "image/jpeg"}]}],
    }
    with tempfile.TemporaryDirectory() as temp_dir:
        original_storage = thumbnail_generation.STORAGE
        thumbnail_generation.STORAGE = Path(temp_dir)
        try:
            with patch.object(thumbnail_generation.requests, "post", return_value=response) as post:
                output = thumbnail_generation.generate_thumbnail_image(
                    {
                        "gemini_image_api_key": "secret-key",
                        "gemini_image_model": "gemini-3.1-flash-image",
                        "gemini_image_aspect_ratio": "16:9",
                        "gemini_image_size": "1K",
                    },
                    "A cinematic thumbnail prompt",
                    topic="A topic",
                    variant_index=1,
                )
            assert output.read_bytes() == image_bytes
            assert output.suffix == ".jpg"
            assert output.parent == Path(temp_dir) / "thumbnails"
            request = post.call_args.kwargs
            assert request["headers"]["x-goog-api-key"] == "secret-key"
            assert request["json"]["model"] == "gemini-3.1-flash-image"
            assert request["json"]["response_format"] == {
                "type": "image",
                "mime_type": "image/jpeg",
                "aspect_ratio": "16:9",
                "image_size": "1K",
            }
            assert "secret-key" not in json.dumps(request["json"])
        finally:
            thumbnail_generation.STORAGE = original_storage
