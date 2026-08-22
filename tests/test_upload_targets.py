from pathlib import Path


SOURCE = Path(__file__).parents[1].joinpath("app", "main.py").read_text(encoding="utf-8")


def test_upload_destinations_render_a_target_selector_for_each_platform():
    assert 'st.markdown("**Onde enviar**")' in SOURCE
    assert 'render_upload_destination_target(target_destination, channels, settings)' in SOURCE
    assert 'key=f"upload_target_{destination_key}"' in SOURCE


def test_youtube_upload_uses_the_explicitly_selected_channel():
    assert 'selected_youtube_channel = upload_targets.get("YouTube")' in SOURCE
    assert 'channel = selected_youtube_channel or channel_map.get' in SOURCE
    assert 'disabled=not selected_youtube_channel' in SOURCE


def test_future_platform_target_lists_are_reserved_in_settings():
    assert '"TikTok": "tiktok_accounts"' in SOURCE
    assert 'settings.get("tiktok_profiles", [])' in SOURCE
    assert '"Instagram": "instagram_profiles"' in SOURCE
    assert '"Facebook Pages": "facebook_pages"' in SOURCE
    assert 'A lista de {destination} será ligada numa etapa própria de credenciais/API.' in SOURCE
