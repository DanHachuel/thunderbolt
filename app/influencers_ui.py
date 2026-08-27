"""Streamlit UI for the AI Influencers domain."""

from __future__ import annotations

import base64
import io
import json
from pathlib import Path
from typing import Any, Mapping

import streamlit as st

from hermes_ui.influencers import (
    BACKEND_OPTIONS,
    InfluencerBackendError,
    backend_name,
    backend_status,
    get_repository,
    test_backend,
)
from hermes_ui.media_generation import MediaGenerationError, generate_image_for_card, generate_video_for_card
from hermes_ui.media_providers import media_cards_for_pool, media_provider_definition
from hermes_ui.notifications import record_notification


CONTENT_STATES = {
    "queued": "Na fila",
    "running": "Em execução",
    "completed": "Concluído",
    "failed": "Falha",
    "cancelled": "Cancelado",
    "blocked": "Bloqueado",
}
PLATFORM_OPTIONS = ["Instagram", "TikTok", "YouTube Shorts", "Facebook"]


def _repository(settings: Mapping[str, Any]):
    try:
        return get_repository(settings)
    except InfluencerBackendError as exc:
        st.warning(str(exc))
        return None


def _influencer_options(items: list[dict[str, Any]]) -> list[str]:
    return [str(item.get("id") or "") for item in items if str(item.get("id") or "").strip()]


def _influencer_label(items: list[dict[str, Any]], value: str) -> str:
    item = next((item for item in items if str(item.get("id") or "") == str(value)), None)
    return str(item.get("name") or value) if item else value


def _asset_label(asset: Mapping[str, Any]) -> str:
    kind = "Imagem" if str(asset.get("asset_type") or "") == "image" else "Documento"
    return f"{kind} · {asset.get('original_name') or 'asset'}"


def _local_asset_path(asset: Mapping[str, Any]) -> Path | None:
    raw = str(asset.get("stored_path") or "").strip()
    path = Path(raw).expanduser() if raw else None
    return path if path and path.is_file() else None


def _image_input(asset: Mapping[str, Any]) -> str:
    """Create a provider-safe URL/data URL for local image-to-video inputs."""
    public_url = str(asset.get("public_url") or "").strip()
    if public_url.startswith(("http://", "https://")):
        return public_url
    path = _local_asset_path(asset)
    if not path:
        return ""
    data = path.read_bytes()
    mime = str(asset.get("mime_type") or "image/jpeg")
    if len(data) > 220 * 1024:
        try:
            from PIL import Image
            image = Image.open(io.BytesIO(data)).convert("RGB")
            for quality in (78, 68, 58, 48):
                buffer = io.BytesIO()
                image.thumbnail((1600, 1600))
                image.save(buffer, format="JPEG", quality=quality, optimize=True)
                if buffer.tell() <= 220 * 1024:
                    data = buffer.getvalue()
                    mime = "image/jpeg"
                    break
        except Exception:
            return ""
    if len(data) > 256 * 1024:
        return ""
    return f"data:{mime};base64,{base64.b64encode(data).decode('ascii')}"


def _provider_options(settings: Mapping[str, Any], pool: str) -> tuple[list[dict[str, Any]], list[str]]:
    cards = media_cards_for_pool(settings, pool)
    return cards, [str(card.get("id") or "") for card in cards]


def _provider_label(card: Mapping[str, Any]) -> str:
    definition = media_provider_definition(card.get("provider"))
    model = str(card.get("model") or "modelo não configurado").strip()
    return f"{definition.label} · {model}"


def render_ai_influencers_api_status(settings: dict[str, Any]) -> None:
    """Show the effective backend status after selector and credentials are loaded."""
    status = backend_status(settings)
    cols = st.columns(3)
    with cols[0]:
        st.metric("Backend activo", status["backend"])
    with cols[1]:
        st.metric("Configurado", "Sim" if status["configured"] else "Não")
    with cols[2]:
        st.metric("Schema", "Verificar" if status["backend"] == "Supabase" else "Automático")
    if status["configured"]:
        st.info(f"{status['message']} Destino: `{status['target']}`")
    else:
        st.warning(status["message"])
    st.markdown("A migração SQL idempotente está disponível em `seed/references/ai_influencers_schema.sql`. No Supabase, aplique-a no SQL Editor e confirme as políticas RLS.")
    if st.button("Testar backend AI Influencers", key="influencers_api_status_test"):
        result = test_backend(settings)
        if result.get("ok"):
            st.success(result.get("message") or "Backend disponível.")
        else:
            st.error(result.get("message") or "O backend não está disponível.")


def render_ai_influencer_characters(
    settings: dict[str, Any],
    *,
    language_options: list[str] | None = None,
    language_formatter: Any = None,
    language_normalizer: Any = None,
) -> None:
    st.title("Personagens")
    language_options = list(language_options or ["pt"])
    language_formatter = language_formatter or (lambda value: value)
    language_normalizer = language_normalizer or (lambda value, default="pt": str(value or default))

    def language_index(value: Any) -> int:
        try:
            normalized = language_normalizer(value, default="pt")
        except TypeError:
            normalized = language_normalizer(value)
        if normalized in language_options:
            return language_options.index(normalized)
        return language_options.index("pt") if "pt" in language_options else 0

    st.caption("Crie personagens virtuais com várias imagens de referência e documentos Markdown/JSON. Os assets ficam associados ao personagem e não são enviados para IA sem uma acção de geração.")
    repository = _repository(settings)
    if repository is None:
        return

    new_character_tab, created_characters_tab = st.tabs(["Novo personagem", "Personagens criados"])

    with new_character_tab:
        with st.form("influencer_create_form", clear_on_submit=True):
            st.subheader("Novo personagem")
            cols = st.columns(3)
            with cols[0]:
                name = st.text_input("Nome do personagem", key="influencer_new_name")
            with cols[1]:
                language = st.selectbox(
                    "Idioma",
                    language_options,
                    index=language_index(st.session_state.get("influencer_new_language", "pt")),
                    format_func=language_formatter,
                    key="influencer_new_language",
                )
            with cols[2]:
                instagram_id = st.text_input("Instagram Business ID (opcional)", key="influencer_new_instagram_id")
            bio = st.text_area("Biografia e instruções", height=130, key="influencer_new_bio")
            files = st.file_uploader(
                "Imagens e documentos de referência",
                type=[item.lstrip(".") for item in sorted({".png", ".jpg", ".jpeg", ".webp", ".gif", ".md", ".json"})],
                accept_multiple_files=True,
                key="influencer_new_assets",
                help="Pode seleccionar várias imagens e ficheiros .md/.json no mesmo upload.",
            )
            create = st.form_submit_button("Guardar personagem", type="primary", use_container_width=True)
        if create:
            try:
                record = repository.create_influencer({"name": name, "bio": bio, "language": language, "instagram_business_id": instagram_id})
                saved_assets = 0
                for uploaded in files or []:
                    repository.save_asset(record["id"], uploaded.name, uploaded.getvalue())
                    saved_assets += 1
                st.session_state["influencer_selected_id"] = record["id"]
                st.success(f"Personagem guardado com {saved_assets} asset(s) de referência.")
                st.rerun()
            except (ValueError, InfluencerBackendError) as exc:
                st.error(str(exc))
            except Exception:
                st.error("Não foi possível guardar o personagem ou os assets seleccionados.")

    with created_characters_tab:
        try:
            influencers = repository.list_influencers()
        except Exception:
            st.error("Não foi possível consultar os personagens no backend seleccionado.")
            return
        if not influencers:
            st.info("Ainda não existem personagens. Crie o primeiro na subaba Novo personagem.")
            return

        options = _influencer_options(influencers)
        current = str(st.session_state.get("influencer_selected_id") or options[0])
        selected_id = st.selectbox("Personagem seleccionado", options, index=options.index(current) if current in options else 0, format_func=lambda value: _influencer_label(influencers, value), key="influencer_selected_id")
        selected = next(item for item in influencers if str(item.get("id")) == selected_id)

        with st.expander(f"Card do personagem · {selected.get('name') or selected_id}", expanded=False):
            with st.form(f"influencer_edit_form_{selected_id}"):
                edit_name = st.text_input("Nome", value=str(selected.get("name") or ""), key=f"influencer_edit_name_{selected_id}")
                edit_language = st.selectbox(
                    "Idioma",
                    language_options,
                    index=language_index(selected.get("language") or "pt"),
                    format_func=language_formatter,
                    key=f"influencer_edit_language_{selected_id}",
                )
                edit_instagram = st.text_input("Instagram Business ID", value=str(selected.get("instagram_business_id") or ""), key=f"influencer_edit_instagram_{selected_id}")
                edit_bio = st.text_area("Biografia e instruções", value=str(selected.get("bio") or ""), height=130, key=f"influencer_edit_bio_{selected_id}")
                save_edit = st.form_submit_button("Guardar alterações", type="primary")
            if save_edit:
                try:
                    repository.update_influencer(selected_id, {"name": edit_name, "language": edit_language, "instagram_business_id": edit_instagram, "bio": edit_bio})
                    st.success("Perfil do personagem actualizado.")
                    st.rerun()
                except Exception as exc:
                    st.error(str(exc))

            with st.form(f"influencer_append_assets_form_{selected_id}"):
                more_files = st.file_uploader(
                    "Adicionar imagens/documentos de referência",
                    type=[item.lstrip(".") for item in sorted({".png", ".jpg", ".jpeg", ".webp", ".gif", ".md", ".json"})],
                    accept_multiple_files=True,
                    key=f"influencer_append_assets_{selected_id}",
                )
                append_assets = st.form_submit_button("Adicionar assets ao personagem", use_container_width=True)
            if append_assets:
                try:
                    saved_assets = 0
                    for uploaded in more_files or []:
                        repository.save_asset(selected_id, uploaded.name, uploaded.getvalue())
                        saved_assets += 1
                    st.success(f"{saved_assets} asset(s) adicionado(s).")
                    st.rerun()
                except Exception as exc:
                    st.error(str(exc))

            try:
                assets = repository.list_assets(selected_id)
            except Exception:
                assets = []
            st.subheader(f"Assets de referência · {selected.get('name') or selected_id}")
            if not assets:
                st.info("Este personagem ainda não tem imagens ou documentos de referência.")
            else:
                cols = st.columns(min(4, max(1, len(assets))))
                for index, asset in enumerate(assets):
                    with cols[index % len(cols)]:
                        st.caption(_asset_label(asset))
                        path = _local_asset_path(asset)
                        if str(asset.get("asset_type") or "") == "image" and path:
                            st.image(str(path), use_container_width=True)
                        elif str(asset.get("asset_type") or "") == "document":
                            raw = str(asset.get("document_json") or "")
                            try:
                                preview = json.loads(raw) if raw else {}
                                st.json(preview, expanded=False)
                            except (TypeError, json.JSONDecodeError):
                                st.code(raw[:1600], language="markdown")
                        st.caption(f"{asset.get('size_bytes', 0)} bytes · {asset.get('mime_type') or 'unknown'}")


def _render_content_history(repository: Any, influencer_id: str = "") -> None:
    try:
        records = repository.list_content(influencer_id, limit=50)
    except Exception:
        records = []
    if not records:
        return
    st.subheader("Conteúdos gerados")
    rows = []
    for item in records:
        rows.append({
            "Tipo": str(item.get("content_type") or "").capitalize(),
            "Estado": CONTENT_STATES.get(str(item.get("state") or ""), str(item.get("state") or "—")),
            "Provider": f"{item.get('provider') or '—'} · {item.get('model') or '—'}",
            "Plataforma": item.get("platform") or "—",
            "Artefacto": item.get("artifact_path") or item.get("error") or "—",
            "Criado": item.get("created_at") or "—",
        })
    st.dataframe(rows, use_container_width=True, hide_index=True)
    latest = records[0]
    artifact = Path(str(latest.get("artifact_path") or ""))
    if artifact.is_file() and latest.get("state") == "completed":
        if latest.get("content_type") == "image":
            st.image(str(artifact), caption="Última imagem gerada", use_container_width=True)
        elif latest.get("content_type") == "video":
            st.video(str(artifact))


def render_ai_influencer_content(settings: dict[str, Any]) -> None:
    st.title("Geração de Conteúdo IA")
    st.caption("Gere conteúdos para redes sociais a partir de um personagem e dos seus assets. A publicação permanece separada e exige uma acção explícita.")
    repository = _repository(settings)
    if repository is None:
        return
    try:
        influencers = repository.list_influencers()
    except Exception:
        st.error("Não foi possível consultar os personagens.")
        return
    images_tab, videos_tab, motion_tab = st.tabs(["Imagens", "Vídeos", "Motion Control"])

    with images_tab:
        st.subheader("Gerar imagem para redes sociais")
        if not influencers:
            st.info("Crie um personagem em AI Influencers > Personagens antes de gerar conteúdo.")
        else:
            options = _influencer_options(influencers)
            current = str(st.session_state.get("influencer_selected_id") or options[0])
            cards, provider_options = _provider_options(settings, "image")
            if not cards:
                st.warning("Não existem providers activos no pool de imagem. Configure um provider em Configuração API > API Keys > Imagem e Video IA.")
            with st.form("influencer_image_content_form"):
                influencer_id = st.selectbox("Personagem", options, index=options.index(current) if current in options else 0, format_func=lambda value: _influencer_label(influencers, value), key="content_image_influencer")
                assets = repository.list_assets(influencer_id)
                image_assets = [item for item in assets if str(item.get("asset_type") or "") == "image"]
                asset_options = [""] + [str(item.get("id") or "") for item in image_assets]
                reference_id = st.selectbox("Imagem de referência (opcional)", asset_options, format_func=lambda value: "Sem imagem base" if not value else next((_asset_label(item) for item in image_assets if str(item.get("id")) == value), value), key="content_image_reference")
                prompt = st.text_area("Prompt da imagem", height=130, placeholder="Descreva a cena, pose, ambiente e estilo do personagem…", key="content_image_prompt")
                caption = st.text_area("Legenda/caption (opcional)", height=90, key="content_image_caption")
                platforms = st.multiselect("Redes sociais de destino", PLATFORM_OPTIONS, default=["Instagram"], key="content_image_platforms")
                provider_id = st.selectbox("Provider / modelo", provider_options, format_func=lambda value: _provider_label(next(card for card in cards if str(card.get("id")) == value)), key="content_image_provider") if cards else ""
                generate = st.form_submit_button("Gerar imagem", type="primary", use_container_width=True)
            if generate:
                if not prompt.strip():
                    st.error("Informe o prompt da imagem.")
                elif not platforms:
                    st.error("Seleccione pelo menos uma rede social de destino.")
                elif not provider_id:
                    st.error("Configure e active um provider de imagem antes de gerar.")
                else:
                    card = next(card for card in cards if str(card.get("id")) == provider_id)
                    reference = next((item for item in image_assets if str(item.get("id")) == reference_id), None)
                    reference_path = _local_asset_path(reference) if reference else None
                    record = repository.create_content({"influencer_id": influencer_id, "content_type": "image", "prompt": prompt, "caption": caption, "provider": card.get("provider"), "model": card.get("model"), "platform": ", ".join(platforms), "state": "running", "metadata": {"reference_asset_id": reference_id}})
                    with st.spinner("A gerar a imagem…"):
                        try:
                            output = generate_image_for_card(settings, card, prompt, topic=_influencer_label(influencers, influencer_id), reference_image=reference_path)
                            repository.update_content(record["id"], {"state": "completed", "artifact_path": str(output)})
                            record_notification("influencer_content_completed", "Conteúdo de Influencer concluído", f"A imagem de {_influencer_label(influencers, influencer_id)} foi gerada e guardada.", metadata={"content_id": record["id"], "content_type": "image", "provider": card.get("provider")}, dedupe_key=f"influencer-content:{record['id']}:completed")
                            st.success(f"Imagem gerada por {media_provider_definition(card.get('provider')).label}.")
                        except Exception as exc:
                            repository.update_content(record["id"], {"state": "failed", "error": str(exc)[:1000]})
                            record_notification("influencer_content_failed", "Conteúdo de Influencer falhou", f"A imagem de {_influencer_label(influencers, influencer_id)} falhou. Consulte o histórico para ver o erro.", metadata={"content_id": record["id"], "content_type": "image", "provider": card.get("provider")}, dedupe_key=f"influencer-content:{record['id']}:failed")
                            st.error(f"Não foi possível gerar a imagem: {exc}")
                    _render_content_history(repository, influencer_id)
            else:
                selected_id = str(st.session_state.get("content_image_influencer") or options[0])
                _render_content_history(repository, selected_id)

    with videos_tab:
        st.subheader("Gerar vídeo para redes sociais")
        if not influencers:
            st.info("Crie um personagem em AI Influencers > Personagens antes de gerar conteúdo.")
        else:
            options = _influencer_options(influencers)
            current = str(st.session_state.get("influencer_selected_id") or options[0])
            cards, provider_options = _provider_options(settings, "video")
            if not cards:
                st.warning("Não existem providers activos no pool de vídeo. Configure KIE AI, Replicate, FAL AI ou outro provider compatível em Configuração API > API Keys > Imagem e Video IA.")
            with st.form("influencer_video_content_form"):
                influencer_id = st.selectbox("Personagem", options, index=options.index(current) if current in options else 0, format_func=lambda value: _influencer_label(influencers, value), key="content_video_influencer")
                assets = repository.list_assets(influencer_id)
                image_assets = [item for item in assets if str(item.get("asset_type") or "") == "image"]
                asset_options = [str(item.get("id") or "") for item in image_assets]
                reference_id = st.selectbox("Imagem inicial", asset_options, format_func=lambda value: next((_asset_label(item) for item in image_assets if str(item.get("id")) == value), value), key="content_video_reference") if image_assets else ""
                prompt = st.text_area("Prompt de movimento", height=130, placeholder="Descreva movimento de câmara, expressão, gesto e ambiente…", key="content_video_prompt")
                caption = st.text_area("Legenda/caption (opcional)", height=90, key="content_video_caption")
                platforms = st.multiselect("Redes sociais de destino", PLATFORM_OPTIONS, default=["Instagram", "TikTok"], key="content_video_platforms")
                provider_id = st.selectbox("Provider / modelo de vídeo", provider_options, format_func=lambda value: _provider_label(next(card for card in cards if str(card.get("id")) == value)), key="content_video_provider") if cards else ""
                generate = st.form_submit_button("Gerar vídeo", type="primary", use_container_width=True)
            if generate:
                if not prompt.strip():
                    st.error("Informe o prompt de movimento.")
                elif not reference_id:
                    st.error("Seleccione uma imagem inicial para a conversão image-to-video.")
                elif not platforms:
                    st.error("Seleccione pelo menos uma rede social de destino.")
                elif not provider_id:
                    st.error("Configure e active um provider de vídeo antes de gerar.")
                else:
                    card = next(card for card in cards if str(card.get("id")) == provider_id)
                    reference = next((item for item in image_assets if str(item.get("id")) == reference_id), None)
                    image_url = _image_input(reference or {})
                    if not image_url:
                        st.error("A imagem inicial local deve ter até 256 KB ou ter um URL público no backend para ser enviada ao provider de vídeo.")
                    else:
                        record = repository.create_content({"influencer_id": influencer_id, "content_type": "video", "prompt": prompt, "caption": caption, "provider": card.get("provider"), "model": card.get("model"), "platform": ", ".join(platforms), "state": "running", "metadata": {"reference_asset_id": reference_id}})
                        with st.spinner("A gerar e descarregar o vídeo…"):
                            try:
                                output = generate_video_for_card(settings, card, prompt, image_url=image_url)
                                repository.update_content(record["id"], {"state": "completed", "artifact_path": str(output)})
                                record_notification("influencer_content_completed", "Conteúdo de Influencer concluído", f"O vídeo de {_influencer_label(influencers, influencer_id)} foi gerado e guardado.", metadata={"content_id": record["id"], "content_type": "video", "provider": card.get("provider")}, dedupe_key=f"influencer-content:{record['id']}:completed")
                                st.success(f"Vídeo gerado por {media_provider_definition(card.get('provider')).label}.")
                            except Exception as exc:
                                repository.update_content(record["id"], {"state": "failed", "error": str(exc)[:1000]})
                                record_notification("influencer_content_failed", "Conteúdo de Influencer falhou", f"O vídeo de {_influencer_label(influencers, influencer_id)} falhou. Consulte o histórico para ver o erro.", metadata={"content_id": record["id"], "content_type": "video", "provider": card.get("provider")}, dedupe_key=f"influencer-content:{record['id']}:failed")
                                st.error(f"Não foi possível gerar o vídeo: {exc}")
                        _render_content_history(repository, influencer_id)
            else:
                selected_id = str(st.session_state.get("content_video_influencer") or options[0])
                _render_content_history(repository, selected_id)

    with motion_tab:
        st.subheader("Motion Control")
        st.info("A subaba Motion Control foi preparada para a próxima evolução. Nenhuma operação é executada nesta versão.")


__all__ = [
    "render_ai_influencer_characters",
    "render_ai_influencer_content",
    "render_ai_influencers_api_status",
]
