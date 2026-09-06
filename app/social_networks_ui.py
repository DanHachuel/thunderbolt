from __future__ import annotations

import uuid
from typing import Any, Callable, Mapping

import streamlit as st

from hermes_ui.domain import create_channel, update_channel
from hermes_ui.influencers import InfluencerBackendError, STANDALONE_CONTENT_INFLUENCER_ID, get_repository
from hermes_ui.storage import read_json, write_json
from hermes_ui.languages import LANGUAGE_CODES, language_code, language_label
from integrations.instagram_public import fetch_public_instagram_profile
from integrations.meta_social import test_facebook_pages_api_card, test_instagram_api_card


def _clean(value: Any) -> str:
    return str(value or "").strip()


def _metric(value: Any) -> str:
    if value in (None, ""):
        return "—"
    try:
        return f"{int(value):,}".replace(",", ".")
    except (TypeError, ValueError):
        return _clean(value) or "—"


def _language_index(value: Any) -> int:
    code = language_code(value)
    return list(LANGUAGE_CODES).index(code) if code in LANGUAGE_CODES else list(LANGUAGE_CODES).index("pt")


def _api_card_defaults(kind: str) -> tuple[str, list[str], Callable[[Mapping[str, Any]], dict[str, Any]]]:
    if kind == "instagram":
        return "instagram_api_cards", ["id", "label", "account_id", "access_token"], test_instagram_api_card
    return "facebook_pages_api_cards", ["id", "label", "page_id", "access_token"], test_facebook_pages_api_card


def _normalise_api_cards(settings: dict[str, Any], kind: str) -> list[dict[str, str]]:
    key, fields, _ = _api_card_defaults(kind)
    raw = settings.get(key)
    cards: list[dict[str, str]] = []
    if isinstance(raw, list):
        for index, item in enumerate(raw):
            if not isinstance(item, dict):
                continue
            card = {field: _clean(item.get(field)) for field in fields}
            card["id"] = card["id"] or f"{kind}-api-{index + 1}"
            cards.append(card)
    if not cards:
        legacy_key = "instagram_api_key" if kind == "instagram" else "facebook_pages_api_key"
        legacy_id = "instagram_account_id" if kind == "instagram" else "facebook_page_id"
        token = _clean(settings.get(legacy_key))
        identifier = _clean(settings.get(legacy_id))
        if token or identifier:
            cards = [{"id": f"{kind}-api-1", "label": "Conta 1", "account_id" if kind == "instagram" else "page_id": identifier, "access_token": token}]
    if cards and not isinstance(raw, list):
        settings[key] = cards
        write_json("settings.json", settings)
    return cards


def _persist_api_cards(settings: dict[str, Any], kind: str, cards: list[dict[str, Any]]) -> None:
    key, fields, _ = _api_card_defaults(kind)
    clean_cards: list[dict[str, str]] = []
    for index, item in enumerate(cards):
        card = {field: _clean(item.get(field)) for field in fields}
        card["id"] = card["id"] or f"{kind}-api-{index + 1}"
        clean_cards.append(card)
    settings[key] = clean_cards
    if kind == "instagram":
        first = next((item for item in clean_cards if item.get("account_id") and item.get("access_token")), clean_cards[0] if clean_cards else {})
        settings["instagram_account_id"] = first.get("account_id", "")
        settings["instagram_api_key"] = first.get("access_token", "")
    else:
        first = next((item for item in clean_cards if item.get("page_id") and item.get("access_token")), clean_cards[0] if clean_cards else {})
        settings["facebook_page_id"] = first.get("page_id", "")
        settings["facebook_pages_api_key"] = first.get("access_token", "")
    write_json("settings.json", settings)


def _api_card_status(card: Mapping[str, Any], kind: str) -> tuple[str, str]:
    identifier = _clean(card.get("account_id" if kind == "instagram" else "page_id"))
    token = _clean(card.get("access_token"))
    if not token:
        return "missing", "Missing key"
    if not identifier:
        return "missing", "Missing configuration"
    return "ready", "Configured"


def render_meta_api_cards(settings: dict[str, Any], kind: str) -> None:
    is_instagram = kind == "instagram"
    title = "API Instagram" if is_instagram else "API Facebook Pages"
    entity_label = "Instagram Account ID" if is_instagram else "Facebook Page ID"
    key, _, tester = _api_card_defaults(kind)
    cards = _normalise_api_cards(settings, kind)
    if not cards:
        st.info(f"Ainda não existe nenhuma conta {title.replace('API ', '')} configurada. Use o botão abaixo para criar o primeiro card.")
    for index, card in enumerate(cards):
        card_id = _clean(card.get("id"))
        status_kind, status_label = _api_card_status(card, kind)
        with st.container(border=True):
            header_cols = st.columns([3.2, 1.2])
            with header_cols[0]:
                st.subheader(f"{title} {index + 1}")
                st.caption("Cada card representa uma conta independente; o token é guardado apenas no storage local.")
            with header_cols[1]:
                st.markdown(
                    f'<span class="tb-api-status tb-api-status--{status_kind}">{"✓" if status_kind == "ready" else "!"} {status_label}</span>',
                    unsafe_allow_html=True,
                )
            with st.form(f"{kind}_api_card_form_{card_id}"):
                label = st.text_input("Nome da conta", value=_clean(card.get("label")) or f"Conta {index + 1}", key=f"{kind}_api_{card_id}_label")
                identifier = st.text_input(entity_label, value=_clean(card.get("account_id" if is_instagram else "page_id")), key=f"{kind}_api_{card_id}_identifier")
                token = st.text_input("Access Token", value=_clean(card.get("access_token")), type="password", key=f"{kind}_api_{card_id}_token")
                action_cols = st.columns(3)
                with action_cols[0]:
                    test_clicked = st.form_submit_button("Teste chamada API", use_container_width=True)
                with action_cols[1]:
                    save_clicked = st.form_submit_button("Guardar Card", type="primary", use_container_width=True)
                with action_cols[2]:
                    delete_clicked = st.form_submit_button("Apagar Card", use_container_width=True)
            edited = {
                "id": card_id,
                "label": label.strip(),
                "access_token": token.strip(),
                ("account_id" if is_instagram else "page_id"): identifier.strip(),
            }
            if test_clicked:
                cards[index] = edited
                _persist_api_cards(settings, kind, cards)
                result = tester(edited)
                if result.get("status") == "success":
                    st.success(result.get("message") or "Chamada API concluída.")
                elif result.get("status") == "missing":
                    st.warning(result.get("message") or "Missing configuration")
                else:
                    st.error(result.get("message") or "A chamada API falhou.")
            elif save_clicked:
                cards[index] = edited
                _persist_api_cards(settings, kind, cards)
                st.success(f"{title} guardada.")
                st.rerun()
            elif delete_clicked:
                cards = [item for item in cards if _clean(item.get("id")) != card_id]
                _persist_api_cards(settings, kind, cards)
                st.success(f"{title} apagada.")
                st.rerun()
    if st.button("Adicionar nova API", type="primary", use_container_width=True, key=f"add_{kind}_api_card"):
        identifier_key = "account_id" if is_instagram else "page_id"
        cards.append({"id": f"{kind}-api-{uuid.uuid4().hex[:10]}", "label": f"Conta {len(cards) + 1}", identifier_key: "", "access_token": ""})
        _persist_api_cards(settings, kind, cards)
        st.success(f"Novo card {title} criado.")
        st.rerun()


def _instagram_profiles() -> list[dict[str, Any]]:
    records = read_json("channels.json", [])
    profiles: list[dict[str, Any]] = []
    for item in records:
        if not isinstance(item, dict):
            continue
        platform = _clean(item.get("platform")).lower()
        network = _clean(item.get("social_network")).lower()
        url = _clean(item.get("url")).lower()
        if platform == "instagram" or network == "instagram" or "instagram.com/" in url:
            profiles.append(item)
    return profiles


def _characters(settings: Mapping[str, Any]) -> tuple[list[dict[str, Any]], Any | None]:
    try:
        repository = get_repository(settings)
        items = [item for item in repository.list_influencers() if _clean(item.get("id")) != STANDALONE_CONTENT_INFLUENCER_ID]
        return items, repository
    except (InfluencerBackendError, Exception):
        return [], None


def _save_public_profile(data: Mapping[str, Any], *, country: str, language: str, character_id: str = "") -> dict[str, Any]:
    name = _clean(data.get("name")) or _clean(data.get("username")) or "Conta Instagram"
    url = _clean(data.get("url"))
    metadata = {
        **dict(data),
        "platform": "instagram",
        "social_network": "Instagram",
        "name": name,
        "url": url,
        "handle": _clean(data.get("handle")),
        "country": country.strip(),
        "language": language.strip(),
        "post_count": data.get("post_count"),
        "subscriber_count": data.get("subscriber_count"),
        "following_count": data.get("following_count"),
        "character_id": character_id.strip(),
        "active": True,
        "metrics_source": "instagram_public_page",
    }
    return create_channel(name, url, metadata)


def _render_instagram_card(profile: dict[str, Any], characters: list[dict[str, Any]], settings: Mapping[str, Any]) -> None:
    profile_id = _clean(profile.get("id"))
    edit_key = f"edit_instagram_profile_{profile_id}"
    with st.container(border=True):
        header_cols = st.columns([0.7, 3.1, 1.25, 1.25, 1.25, 1.65])
        with header_cols[0]:
            if _clean(profile.get("avatar_url")):
                st.image(profile["avatar_url"], width=64)
            else:
                st.markdown("### IG")
        with header_cols[1]:
            st.write(f"**{_clean(profile.get('name')) or 'Sem nome'}**")
            st.caption(f"{_clean(profile.get('handle')) or _clean(profile.get('url')) or 'sem handler'}")
            bio = _clean(profile.get("bio"))
            if bio:
                st.caption(f"Bio: {bio}")
            st.caption(f"{_clean(profile.get('country')) or 'País não definido'} · {_clean(profile.get('language')) or 'Idioma não definido'}")
        with header_cols[2]:
            st.metric("posts", _metric(profile.get("post_count")))
        with header_cols[3]:
            st.metric("Seguidores", _metric(profile.get("subscriber_count")))
        with header_cols[4]:
            st.metric("seguindo", _metric(profile.get("following_count")))
        with header_cols[5]:
            refresh_col, edit_col = st.columns(2)
            with refresh_col:
                if st.button("↻", help="Actualizar posts, seguidores e seguindo", key=f"refresh_instagram_{profile_id}"):
                    result = fetch_public_instagram_profile(_clean(profile.get("url")) or _clean(profile.get("handle")))
                    if result.ok:
                        update_channel(profile_id, {**result.data, "platform": "instagram", "country": profile.get("country", ""), "language": profile.get("language", ""), "character_id": profile.get("character_id", "")})
                        st.success("Métricas Instagram actualizadas.")
                        st.rerun()
                    st.warning(result.message)
            with edit_col:
                if st.button("Editar", key=f"edit_instagram_button_{profile_id}", use_container_width=True):
                    st.session_state[edit_key] = True
                    st.rerun()
            url = _clean(profile.get("url"))
            if url:
                st.link_button("Abrir Instagram", url, use_container_width=True)

        if st.session_state.get(edit_key):
            with st.form(f"edit_instagram_profile_form_{profile_id}"):
                edit_cols = st.columns(2)
                with edit_cols[0]:
                    name = st.text_input("Nome", value=_clean(profile.get("name")), key=f"instagram_edit_name_{profile_id}")
                    handle = st.text_input("handler", value=_clean(profile.get("handle")), key=f"instagram_edit_handle_{profile_id}")
                    country = st.text_input("País", value=_clean(profile.get("country")), key=f"instagram_edit_country_{profile_id}")
                    language = st.selectbox("Idioma", list(LANGUAGE_CODES), index=_language_index(profile.get("language")), format_func=language_label, key=f"instagram_edit_language_{profile_id}")
                with edit_cols[1]:
                    posts = st.number_input("posts", min_value=0, value=int(profile.get("post_count") or 0), key=f"instagram_edit_posts_{profile_id}")
                    followers = st.number_input("Seguidores", min_value=0, value=int(profile.get("subscriber_count") or 0), key=f"instagram_edit_followers_{profile_id}")
                    following = st.number_input("seguindo", min_value=0, value=int(profile.get("following_count") or 0), key=f"instagram_edit_following_{profile_id}")
                save_edit = st.form_submit_button("Guardar alterações", type="primary", use_container_width=True)
            if save_edit:
                update_channel(profile_id, {"name": name.strip(), "handle": handle.strip(), "country": country.strip(), "language": language, "post_count": int(posts), "subscriber_count": int(followers), "following_count": int(following)})
                st.session_state.pop(edit_key, None)
                st.success("Conta Instagram actualizada.")
                st.rerun()
        else:
            block_cols = st.columns(4, gap="small")
            with block_cols[0]:
                st.markdown(f"**Nome**\n\n{_clean(profile.get('name')) or '—'}")
            with block_cols[1]:
                st.markdown(f"**handler**\n\n{_clean(profile.get('handle')) or '—'}")
            with block_cols[2]:
                st.markdown(f"**País**\n\n{_clean(profile.get('country')) or '—'}")
            with block_cols[3]:
                st.markdown(f"**Idioma**\n\n{_clean(profile.get('language')) or '—'}")

        character_options = [""] + [_clean(item.get("id")) for item in characters if _clean(item.get("id"))]
        character_labels = {"": "Sem personagem associado"} | {_clean(item.get("id")): _clean(item.get("name")) or _clean(item.get("id")) for item in characters}
        current_character = _clean(profile.get("character_id"))
        selected_character = st.selectbox("Personagem", character_options, index=character_options.index(current_character) if current_character in character_options else 0, format_func=lambda value: character_labels.get(value, value), key=f"instagram_character_{profile_id}")
        if st.button("Atrelar Personagem", key=f"attach_instagram_character_{profile_id}", use_container_width=True):
            update_channel(profile_id, {"character_id": selected_character})
            st.success("Personagem associado à conta Instagram.")
            st.rerun()


def render_social_networks(settings: dict[str, Any]) -> None:
    st.title("Redes Sociais")
    st.caption("Cadastre contas Instagram através de pesquisa pública e associe cada conta a um Personagem de AI Influencers.")
    search_tab, accounts_tab = st.tabs(["Pesquisa pública Instagram", "Contas Instagram"])
    with search_tab:
        st.caption("A pesquisa consulta apenas a página pública do Instagram. API Key não é necessária para cadastrar o perfil.")
        source = st.text_input("URL pública ou @handler Instagram", placeholder="https://www.instagram.com/conta/ ou @conta", key="social_instagram_source")
        search_cols = st.columns(2)
        with search_cols[0]:
            search_clicked = st.button("Pesquisar conta pública", type="primary", use_container_width=True, key="social_instagram_search")
        with search_cols[1]:
            if st.button("Limpar pesquisa", use_container_width=True, key="social_instagram_clear"):
                for key in ("social_instagram_result", "social_instagram_ok", "social_instagram_message"):
                    st.session_state.pop(key, None)
                st.rerun()
        if search_clicked:
            result = fetch_public_instagram_profile(source)
            st.session_state["social_instagram_result"] = result.data if isinstance(result.data, dict) else {}
            st.session_state["social_instagram_ok"] = result.ok
            st.session_state["social_instagram_message"] = result.message
        if st.session_state.get("social_instagram_message"):
            (st.success if st.session_state.get("social_instagram_ok") else st.warning)(st.session_state["social_instagram_message"])
        data = st.session_state.get("social_instagram_result", {}) if st.session_state.get("social_instagram_ok") else {}
        if data:
            characters, _ = _characters(settings)
            with st.container(border=True):
                st.subheader("Conta Instagram encontrada")
                preview_cols = st.columns([0.8, 2.2, 1.2, 1.2, 1.2])
                with preview_cols[0]:
                    if _clean(data.get("avatar_url")):
                        st.image(data["avatar_url"], width=72)
                with preview_cols[1]:
                    st.write(f"**{_clean(data.get('name')) or _clean(data.get('username'))}**")
                    st.caption(_clean(data.get("handle")))
                with preview_cols[2]:
                    st.metric("posts", _metric(data.get("post_count")))
                with preview_cols[3]:
                    st.metric("Seguidores", _metric(data.get("subscriber_count")))
                with preview_cols[4]:
                    st.metric("seguindo", _metric(data.get("following_count")))
                with st.form("social_instagram_save_public_profile"):
                    form_cols = st.columns(2)
                    with form_cols[0]:
                        name = st.text_input("Nome", value=_clean(data.get("name")), key="social_instagram_result_name")
                        country = st.text_input("País", value=_clean(data.get("country")), key="social_instagram_result_country")
                        language = st.selectbox("Idioma", list(LANGUAGE_CODES), index=_language_index(data.get("language")), format_func=language_label, key="social_instagram_result_language")
                    with form_cols[1]:
                        posts = st.number_input("posts", min_value=0, value=int(data.get("post_count") or 0), key="social_instagram_result_posts")
                        followers = st.number_input("Seguidores", min_value=0, value=int(data.get("subscriber_count") or 0), key="social_instagram_result_followers")
                        following = st.number_input("seguindo", min_value=0, value=int(data.get("following_count") or 0), key="social_instagram_result_following")
                    character_options = [""] + [_clean(item.get("id")) for item in characters if _clean(item.get("id"))]
                    character_labels = {"": "Sem personagem associado"} | {_clean(item.get("id")): _clean(item.get("name")) or _clean(item.get("id")) for item in characters}
                    selected_character = st.selectbox("Personagem", character_options, format_func=lambda value: character_labels.get(value, value), key="social_instagram_result_character")
                    save_profile = st.form_submit_button("Cadastrar conta Instagram", type="primary", use_container_width=True)
                if save_profile:
                    profile_data = dict(data)
                    profile_data.update({"name": name, "post_count": int(posts), "subscriber_count": int(followers), "following_count": int(following)})
                    _save_public_profile(profile_data, country=country, language=language, character_id=selected_character)
                    st.success("Conta Instagram cadastrada em Redes Sociais.")
                    for key in ("social_instagram_result", "social_instagram_ok", "social_instagram_message"):
                        st.session_state.pop(key, None)
                    st.rerun()
    with accounts_tab:
        profiles = _instagram_profiles()
        if not profiles:
            st.info("Ainda não existem contas Instagram cadastradas. Use a pesquisa pública para adicionar a primeira conta.")
        characters, _ = _characters(settings)
        for profile in profiles:
            _render_instagram_card(profile, characters, settings)
