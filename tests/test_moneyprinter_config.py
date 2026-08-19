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
    assert payload["app"]["pexels_api_keys"] == ["p1", "p2"]
    assert payload["azure"]["speech_region"] == "westeurope"
    assert payload["elevenlabs"]["api_key"] == "eleven-secret"
    assert payload["whisper"]["model_size"] == "small"


def test_tiktok_settings_are_not_added_to_mpt_config():
    payload = build_moneyprinter_config({"tiktok_client_key": "client", "tiktok_client_secret": "secret"})
    text = str(payload)
    assert "redirect_uri" not in text
    assert "tiktok_client_key" not in text
