from hermes_ui.media_generation import MediaGenerationError, format_media_generation_error


def test_format_translates_authentication_error():
    message = format_media_generation_error(
        MediaGenerationError(
            "Todos os providers do pool de imagem falharam.",
            provider_errors=["openai: HTTP 401: invalid api key"],
        ),
        operation="refazer o lettering da thumbnail",
    )
    assert "IMG_AUTH_HTTP_401" in message
    assert "API key está ausente, inválida ou sem permissão" in message
    assert "refazer o lettering da thumbnail" in message


def test_format_translates_missing_provider_configuration():
    message = format_media_generation_error(MediaGenerationError("Não existem providers activos no pool de imagem."))
    assert "IMG_NO_ACTIVE_PROVIDER" in message
    assert "active um cartão" in message
