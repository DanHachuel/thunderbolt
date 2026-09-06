from unittest.mock import Mock, patch

from app.social_networks_ui import _api_card_status, _instagram_profiles, _normalise_api_cards
from hermes_ui.domain import create_channel
from integrations.instagram_public import fetch_public_instagram_posts, fetch_public_instagram_profile
from integrations.meta_social import test_facebook_pages_api_card as run_facebook_pages_api_test, test_instagram_api_card as run_instagram_api_test


def test_meta_cards_report_missing_key_and_missing_configuration_separately():
    assert _api_card_status({"access_token": ""}, "instagram") == ("missing", "Missing key")
    assert _api_card_status({"access_token": "token"}, "instagram") == ("missing", "Missing configuration")
    assert _api_card_status({"access_token": "token", "account_id": "123"}, "instagram") == ("ready", "Configured")
    assert _api_card_status({"access_token": "token", "page_id": "456"}, "facebook_pages") == ("ready", "Configured")


def test_meta_api_tests_do_not_call_network_without_required_fields():
    assert run_instagram_api_test({"access_token": ""})["status"] == "missing"
    assert run_facebook_pages_api_test({"access_token": "token"})["status"] == "missing"


def test_legacy_single_account_settings_are_normalised_to_multi_account_cards(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    settings = {"instagram_api_key": "token", "instagram_account_id": "123"}
    cards = _normalise_api_cards(settings, "instagram")
    assert cards == [{"id": "instagram-api-1", "label": "Conta 1", "account_id": "123", "access_token": "token"}]


def test_public_instagram_parser_keeps_posts_following_and_followers():
    response = Mock(status_code=200, text='<meta property="og:title" content="Creator (@creator)"><meta property="og:description" content=\"123 followers, 456 following and 78 posts\"><meta property="og:image" content="https://img.example/avatar.jpg">')
    with patch("integrations.instagram_public.requests.get", return_value=response):
        result = fetch_public_instagram_profile("@creator")
    assert result.ok is True
    assert result.data["subscriber_count"] == 123
    assert result.data["following_count"] == 456
    assert result.data["post_count"] == 78


def test_public_instagram_parser_reads_structured_following_counter():
    response = Mock(
        status_code=200,
        text=(
            '<meta property="og:title" content="Creator (@creator)">'
            '<meta property="og:description" content="Creator profile">'
            '<script>"edge_followed_by":{"count":123},'
            '"edge_follow":{"count":456},'
            '"edge_owner_to_timeline_media":{"count":78}</script>'
        ),
    )
    with patch("integrations.instagram_public.requests.get", return_value=response):
        result = fetch_public_instagram_profile("@creator")
    assert result.ok is True
    assert result.data["subscriber_count"] == 123
    assert result.data["following_count"] == 456
    assert result.data["post_count"] == 78


def test_public_instagram_parser_reads_following_alias_with_nested_payload():
    response = Mock(
        status_code=200,
        text='<meta property="og:title" content="Creator (@creator)"><script>"following":{"reel":true,"count":987}</script>',
    )
    with patch("integrations.instagram_public.requests.get", return_value=response):
        result = fetch_public_instagram_profile("@creator")
    assert result.ok is True
    assert result.data["following_count"] == 987


def test_instagram_ui_uses_canonical_language_selector():
    from app import social_networks_ui

    source = open(social_networks_ui.__file__, encoding="utf-8").read()
    assert 'st.selectbox("Idioma", list(LANGUAGE_CODES)' in source
    assert 'st.text_input("Idioma"' not in source


def test_instagram_card_renders_profile_bio_next_to_identity():
    from app import social_networks_ui

    source = open(social_networks_ui.__file__, encoding="utf-8").read()
    assert 'bio = _clean(profile.get("bio"))' in source
    assert 'st.caption(f"Bio: {bio}")' in source


def test_create_channel_keeps_social_metadata_for_instagram_accounts():
    saved = []

    with patch("hermes_ui.domain.read_json", return_value=[]), patch(
        "hermes_ui.domain.write_json", side_effect=lambda _name, data: saved.append(data)
    ):
        channel = create_channel(
            "Creator",
            "https://www.instagram.com/creator/",
            {"platform": "instagram", "social_network": "Instagram", "following_count": 456},
        )

    assert channel["platform"] == "instagram"
    assert channel["social_network"] == "Instagram"
    assert channel["following_count"] == 456
    assert saved[-1][0]["platform"] == "instagram"


def test_instagram_profiles_include_legacy_records_by_public_url():
    with patch(
        "app.social_networks_ui.read_json",
        return_value=[
            {"id": "legacy", "url": "https://www.instagram.com/creator/"},
            {"id": "youtube", "url": "https://www.youtube.com/@creator"},
        ],
    ):
        profiles = _instagram_profiles()
    assert [profile["id"] for profile in profiles] == ["legacy"]


def test_public_instagram_posts_extracts_media_and_caption_from_embedded_json():
    response = Mock(
        status_code=200,
        text=(
            '<script type="application/json">{"items":['
            '{"id":"p1","code":"ABC","display_url":"https://img.example/1.jpg","caption":{"text":"Primeiro"}},'
            '{"id":"p2","code":"DEF","display_url":"https://img.example/2.jpg","caption":{"text":"Segundo"}}]}'
            '</script>'
        ),
    )
    with patch("integrations.instagram_public.requests.get", return_value=response):
        result = fetch_public_instagram_posts("@creator", limit=10)
    assert result.ok is True
    assert [post["id"] for post in result.data["posts"]] == ["p1", "p2"]
    assert result.data["posts"][0]["caption"] == "Primeiro"


def test_instagram_card_contains_posts_expander_controls():
    from app import social_networks_ui

    source = open(social_networks_ui.__file__, encoding="utf-8").read()
    assert 'with st.expander("Últimos posts do Instagram", expanded=False):' in source
    assert 'st.button("Actualizar tudo"' in source
    assert 'st.download_button("Baixar todos"' in source
    assert 'st.button("Mostrar + 10"' in source
