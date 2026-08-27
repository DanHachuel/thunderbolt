from integrations.moneyprinter_config import build_moneyprinter_config


def test_moneyprinter_config_preserves_existing_and_maps_services():
    settings = {
        "llm_provider": "openai",
        "openai_api_key": "secret",
        "openai_model_name": "gpt-test",
        "pexels_api_keys": "p1,p2",
        "azure_speech_key": "speech-secret",
        "azure_speech_region": "westeurope",
        "elevenlabs_api_key": "eleven-secret",
        "whisper_model_size": "small",
    }
    payload = build_moneyprinter_config(settings, {"custom": {"keep": True}})
    assert payload["custom"]["keep"] is True
    assert payload["app"]["llm_provider"] == "openai"
    assert payload["app"]["openai_api_key"] == "secret"
    assert payload["app"]["openai_model_name"] == "gpt-test"
    assert payload["app"]["edge_tts_timeout"] == 90
    assert payload["app"]["pexels_api_keys"] == ["p1", "p2"]
    assert payload["azure"]["speech_region"] == "westeurope"
    assert payload["elevenlabs"]["api_key"] == "eleven-secret"
    assert payload["whisper"]["model_size"] == "small"


def test_tiktok_settings_are_not_added_to_mpt_config():
    payload = build_moneyprinter_config({"tiktok_client_key": "client", "tiktok_client_secret": "secret"})
    text = str(payload)
    assert "redirect_uri" not in text
    assert "tiktok_client_key" not in text


def test_moneyprinter_config_exports_canonical_multi_key_sources_as_arrays():
    settings = {
        "video_source": "pixabay",
        "material_api_keys": {
            "pexels": ["pexels-1", "pexels-1", "pexels-2"],
            "pixabay": ["pixabay-1", "pixabay-2"],
            "wavespeed": ["wave-1"],
            "loomloom": ["loom-1", "loom-2"],
            "twelvelabs": ["labs-1"],
        },
    }
    payload = build_moneyprinter_config(settings)
    app = payload["app"]
    assert app["video_source"] == "pixabay"
    assert app["pexels_api_keys"] == ["pexels-1", "pexels-2"]
    assert app["pixabay_api_keys"] == ["pixabay-1", "pixabay-2"]
    assert app["wavespeed_api_keys"] == ["wave-1"]
    assert app["loomloom_api_keys"] == ["loom-1", "loom-2"]
    assert app["twelvelabs_api_keys"] == ["labs-1"]


def test_moneyprinter_config_accepts_local_source_and_legacy_fallback():
    payload = build_moneyprinter_config({"video_source": "local", "pixabay_api_keys": "legacy-a, legacy-b"})
    assert payload["app"]["video_source"] == "local"
    assert payload["app"]["pixabay_api_keys"] == ["legacy-a", "legacy-b"]
