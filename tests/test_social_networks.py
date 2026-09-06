from subprocess import CompletedProcess
from unittest.mock import Mock, patch

from app.social_networks_ui import _api_card_status, _instagram_profiles, _load_instagram_posts, _merge_instagram_refresh, _normalise_api_cards, _normalise_country, _refresh_instagram_profile, _save_public_profile
from hermes_ui.domain import create_channel
from integrations.instagram_public import _country_from_bloks, _fetch_web_profile_user, extract_public_instagram_country, fetch_public_instagram_posts, fetch_public_instagram_profile, normalize_instagram_bio, normalize_instagram_metric
from integrations.meta_social import test_facebook_pages_api_card as run_facebook_pages_api_test, test_instagram_api_card as run_instagram_api_test
from hermes_ui.countries import COUNTRY_OPTIONS


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


def test_public_instagram_parser_reads_json_metric_aliases():
    response = Mock(
        status_code=200,
        text='<script type="application/json">{"followers":{"value":321},"followingCount":654}</script>',
    )
    with patch("integrations.instagram_public.requests.get", return_value=response):
        result = fetch_public_instagram_profile("@creator")
    assert result.data["subscriber_count"] == 321
    assert result.data["following_count"] == 654


def test_public_instagram_parser_reads_direct_profile_following_counter():
    api_response = Mock(
        status_code=200,
        json=lambda: {"data": {"user": {"username": "creator", "edge_follow": {"count": 4321}}}},
    )
    page_response = Mock(status_code=200, text='<meta property="og:title" content="Creator (@creator)">')
    with patch("integrations.instagram_public.requests.get", side_effect=[page_response, api_response]):
        result = fetch_public_instagram_profile("@creator")
    assert result.ok is True
    assert result.data["following_count"] == 4321


def test_public_instagram_endpoint_uses_curl_fallback_after_http_429():
    payload = '{"data":{"user":{"username":"creator","edge_follow":{"count":4321}}}}'
    blocked = Mock(status_code=429)
    with patch("integrations.instagram_public.requests.get", return_value=blocked), patch(
        "integrations.instagram_public.shutil.which", return_value="/usr/bin/curl"
    ), patch(
        "integrations.instagram_public.subprocess.run",
        return_value=CompletedProcess([], 0, stdout=payload, stderr=""),
    ) as run:
        user = _fetch_web_profile_user("creator")
    assert user["edge_follow"]["count"] == 4321
    assert run.called
    assert run.call_args.kwargs["encoding"] == "utf-8"
    assert run.call_args.kwargs["errors"] == "replace"


def test_public_instagram_endpoint_prefers_complete_http_payload_over_curl():
    api_response = Mock(status_code=200, json=lambda: {"data": {"user": {
        "username": "creator", "biography": "Bio real", "edge_follow": {"count": 456},
        "edge_followed_by": {"count": 123}, "edge_owner_to_timeline_media": {"count": 78},
    }}})
    with patch("integrations.instagram_public.requests.get", return_value=api_response), patch("integrations.instagram_public.shutil.which", return_value="/usr/bin/curl"), patch("integrations.instagram_public.subprocess.run") as run:
        user = _fetch_web_profile_user("creator")
    assert user["biography"] == "Bio real"
    assert user["edge_follow"]["count"] == 456
    run.assert_not_called()


def test_private_profile_keeps_bio_and_following_metrics_from_profile_endpoint():
    api_response = Mock(
        status_code=200,
        json=lambda: {"data": {"user": {
            "username": "private_creator", "full_name": "Private Creator", "is_private": True,
            "biography": "Linha um\nLinha dois", "edge_follow": {"count": 2468},
            "edge_followed_by": {"count": 1357}, "edge_owner_to_timeline_media": {"count": 42, "edges": []},
        }}},
    )
    with patch("integrations.instagram_public.requests.get", return_value=api_response), patch("integrations.instagram_public.shutil.which", return_value=None):
        result = fetch_public_instagram_profile("@private_creator")
    assert result.data["bio"] == "Linha um\nLinha dois"
    assert result.data["bio_raw"] == "Linha um\nLinha dois"
    assert result.data["following_count"] == 2468
    assert result.data["is_private"] is True


def test_public_profile_keeps_account_country_from_transparency_payload():
    api_response = Mock(
        status_code=200,
        json=lambda: {"data": {"user": {
            "username": "creator", "biography": "Brasil na bio não é a origem",
            "country_of_registration": "Portugal", "edge_follow": {"count": 12},
        }}},
    )
    with patch("integrations.instagram_public.requests.get", return_value=api_response), patch("integrations.instagram_public.shutil.which", return_value=None):
        result = fetch_public_instagram_profile("@creator")
    assert result.data["country"] == "Portugal"


def test_country_extractor_ignores_bio_and_uses_only_explicit_account_country():
    assert extract_public_instagram_country({"biography": "Brasil", "account_country": "Portugal"}) == "Portugal"
    assert extract_public_instagram_country({"business_address_json": {"country": "Brasil"}, "account_transparency": {"country_name": "Portugal"}}) == "Portugal"
    assert extract_public_instagram_country({"biography": "Brasil"}) == ""


def test_bloks_about_parser_reads_account_country_without_using_bio_or_business_address():
    payload = {"layout": {"bloks_payload": {"data": [{"data": {"key": "about_this_account_country", "initial_lispy": '(bk.action.array.Make, "Portugal")'}}]}}}
    assert _country_from_bloks(payload) == "Portugal"
    assert _country_from_bloks({"biography": "Brasil", "business_address_json": {"country": "Brasil"}}) == ""


def test_authenticated_about_country_is_merged_into_real_profile_result(monkeypatch):
    profile_response = Mock(status_code=200, json=lambda: {"data": {"user": {"id": "123", "username": "creator", "biography": "Bio real", "edge_follow": {"count": 456}}}})
    about_response = Mock(status_code=200, json=lambda: {"data": {"about_this_account_country": "Portugal"}})
    monkeypatch.setenv("INSTAGRAM_SESSIONID", "session-value")
    with patch("integrations.instagram_public.requests.get", return_value=profile_response), patch("integrations.instagram_public.requests.post", return_value=about_response), patch("integrations.instagram_public.shutil.which", return_value=None):
        result = fetch_public_instagram_profile("@creator")
    assert result.data["bio"] == "Bio real"
    assert result.data["following_count"] == 456
    assert result.data["country"] == "Portugal"


def test_private_profile_posts_return_authentication_message():
    api_response = Mock(
        status_code=200,
        json=lambda: {"data": {"user": {"username": "private_creator", "is_private": True, "edge_owner_to_timeline_media": {"edges": []}}}},
    )
    with patch("integrations.instagram_public.requests.get", return_value=api_response):
        result = fetch_public_instagram_posts("@private_creator")
    assert result.ok is False
    assert "conta é privada" in result.message


def test_instagram_metric_normalization_keeps_unknown_distinct_from_zero():
    assert normalize_instagram_metric({"count": "12.345"}) == 12345
    assert normalize_instagram_metric("8,765") == 8765
    assert normalize_instagram_metric(None) is None


def test_public_profile_save_persists_real_bio_and_following():
    saved = []
    with patch("app.social_networks_ui.create_channel", side_effect=lambda name, url, metadata: saved.append(metadata) or metadata):
        _save_public_profile(
            {"name": "Creator", "url": "https://www.instagram.com/creator/", "handle": "@creator", "bio": "Criadora de viagens", "following_count": 4321},
            country="Brasil", language="pt", character_id="character_1",
        )
    assert saved[0]["bio"] == "Criadora de viagens"
    assert saved[0]["following_count"] == 4321
    assert saved[0]["country"] == "Brasil"


def test_instagram_refresh_preserves_existing_bio_and_following_when_response_omits_them():
    merged = _merge_instagram_refresh(
        {"bio": "Bio antiga", "following_count": 4321, "subscriber_count": 99},
        {"bio": "", "following_count": None, "subscriber_count": 100},
    )
    assert merged["bio"] == "Bio antiga"
    assert merged["following_count"] == 4321
    assert merged["subscriber_count"] == 100


def test_instagram_refresh_preserves_internal_channel_id_and_country():
    merged = _merge_instagram_refresh(
        {"id": "channel_internal", "country": "Brasil", "bio": "Bio antiga"},
        {"id": "instagram_creator", "country": "", "bio": "Bio nova"},
    )
    assert merged["id"] == "channel_internal"
    assert merged["country"] == "Brasil"


def test_refresh_button_function_returns_canonical_updated_profile():
    result = Mock(ok=True, message="ok", data={"bio": "Bio nova", "following_count": 765, "subscriber_count": 1234})
    with patch("app.social_networks_ui.fetch_public_instagram_profile", return_value=result) as fetch:
        ok, message, refreshed = _refresh_instagram_profile({"url": "https://www.instagram.com/creator/", "bio": "Bio antiga", "following_count": 4})
    assert ok is True
    assert message == "ok"
    assert refreshed["bio"] == "Bio nova"
    assert refreshed["following_count"] == 765
    fetch.assert_called_once_with("https://www.instagram.com/creator/")


def test_country_normalization_only_normalizes_explicit_form_values():
    assert _normalise_country("Brazil") == "Brasil"
    assert _normalise_country("Brasil") == "Brasil"
    assert _normalise_country("Brasil/ SP") == ""


def test_load_posts_button_function_uses_saved_profile_url_and_returns_posts():
    result = Mock(ok=True, message="Posts públicos encontrados.", data={"posts": [{"id": "p1"}]})
    with patch("app.social_networks_ui.fetch_public_instagram_posts", return_value=result) as fetch:
        ok, message, posts = _load_instagram_posts({"url": "https://www.instagram.com/creator/"}, limit=10)
    assert ok is True
    assert message == "Posts públicos encontrados."
    assert posts == [{"id": "p1"}]
    fetch.assert_called_once_with("https://www.instagram.com/creator/", limit=10)


def test_instagram_bio_preserves_complete_text():
    assert normalize_instagram_bio("606 seguidores, seguindo 3,432, 278 posts — Veja as fotos") == "606 seguidores, seguindo 3,432, 278 posts — Veja as fotos"
    assert normalize_instagram_bio("🇧🇷🇪🇸\n♊ Gemini\n📍 LA / Madrid") == "🇧🇷🇪🇸\n♊ Gemini\n📍 LA / Madrid"
    assert normalize_instagram_bio("Treinos 5x por semana\nSigo posts de viagens") == "Treinos 5x por semana\nSigo posts de viagens"


def test_instagram_ui_uses_canonical_language_selector():
    from app import social_networks_ui

    source = open(social_networks_ui.__file__, encoding="utf-8").read()
    assert 'st.selectbox("Idioma", list(LANGUAGE_CODES)' in source
    assert 'st.text_input("Idioma"' not in source


def test_instagram_country_catalog_contains_attachment_values():
    assert "Brasil" in COUNTRY_OPTIONS
    assert "Estados Unidos" in COUNTRY_OPTIONS
    assert "Zimbábue" in COUNTRY_OPTIONS
    assert len(COUNTRY_OPTIONS) == 203


def test_instagram_card_renders_profile_bio_next_to_identity():
    from app import social_networks_ui

    source = open(social_networks_ui.__file__, encoding="utf-8").read()
    assert 'def _render_instagram_bio(value: Any) -> None:' in source
    assert 'st.caption(f"Bio: {bio}")' not in source
    assert 'st.text(bio)' in source
    assert 'st.selectbox("País", _country_options()' in source
    assert 'delete_channel(profile_id)' in source
    assert '_profile_bio(data)' in source
    assert '"bio_raw": _clean(data.get("bio_raw"))' in source
    assert 'placeholder="Não encontrado"' in source


def test_create_channel_keeps_social_metadata_for_instagram_accounts():
    saved = []

    with patch("hermes_ui.domain.read_json", return_value=[]), patch(
        "hermes_ui.domain.write_json", side_effect=lambda _name, data: saved.append(data)
    ):
        channel = create_channel(
            "Creator",
            "https://www.instagram.com/creator/",
            {"platform": "instagram", "social_network": "Instagram", "bio": "Bio persistida", "following_count": 456},
        )

    assert channel["platform"] == "instagram"
    assert channel["social_network"] == "Instagram"
    assert channel["bio"] == "Bio persistida"
    assert channel["following_count"] == 456
    assert channel["bio_raw"] == ""
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


def test_public_instagram_posts_uses_web_profile_info_json_endpoint():
    api_response = Mock(
        status_code=200,
        json=lambda: {"data": {"user": {"edge_owner_to_timeline_media": {"edges": [
            {"node": {"id": "p1", "shortcode": "ABC", "display_url": "https://img.example/1.jpg", "edge_media_to_caption": {"edges": [{"node": {"text": "Legenda"}}]}}}
        ]}}}},
    )
    with patch("integrations.instagram_public.requests.get", return_value=api_response) as request:
        result = fetch_public_instagram_posts("@creator", limit=10)
    assert result.ok is True
    assert result.data["posts"][0]["caption"] == "Legenda"
    assert "web_profile_info" in request.call_args.args[0]


def test_instagram_card_contains_posts_expander_controls():
    from app import social_networks_ui

    source = open(social_networks_ui.__file__, encoding="utf-8").read()
    assert 'with st.expander("Últimos posts do Instagram", expanded=False):' in source
    assert 'st.button("Actualizar tudo"' in source
    assert 'st.download_button("Baixar todos"' in source
    assert 'st.button("Mostrar + 10"' in source


def test_instagram_card_preserves_existing_metrics_when_refresh_has_no_values():
    from app import social_networks_ui

    source = open(social_networks_ui.__file__, encoding="utf-8").read()
    assert 'def _merge_instagram_refresh(existing: Mapping[str, Any], refreshed: Mapping[str, Any])' in source
    assert '_profile_metric(profile, "subscriber_count", "followers_count", "follower_count")' in source
    assert '_profile_metric(profile, "following_count", "following", "follows")' in source
