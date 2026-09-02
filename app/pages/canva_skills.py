from __future__ import annotations

import json

import streamlit as st

from hermes_ui.media_providers import MEDIA_CARDS_KEY, ensure_media_provider_cards
from hermes_ui.storage import read_json
from app.modules.canva_skills import brand, bulk, edit, feedback, resize
from app.modules.canva_skills.client import client_from_card


st.set_page_config(page_title="Canva Skills", layout="wide")
st.title("Canva Skills — automação criativa")
st.caption("Execução REST directa. Autofill exige Canva Enterprise; operações de edição avançada permanecem manuais quando a Connect API não as expõe.")
settings = read_json("settings.json", {})
migrated, _ = ensure_media_provider_cards(settings)
canva_cards = [card for card in migrated.get(MEDIA_CARDS_KEY, []) if card.get("provider") == "canva"]
if not canva_cards:
    st.warning("Configure e autorize um card Canva em Configuração API > API Keys > Imagem e Video IA.")
    st.stop()
card = canva_cards[0]
client = client_from_card(card)
skill = st.sidebar.selectbox("Skill", ["Resize for Social Media", "Bulk Create", "Design Feedback", "Edit Design", "Brand Check"])

if skill == "Resize for Social Media":
    st.subheader("Redimensionar para redes sociais")
    design_id = st.text_input("ID do design Canva")
    platforms = st.multiselect("Plataformas", list(resize.PLATFORM_DIMENSIONS), default=["youtube_thumbnail"])
    if st.button("Criar variantes") and design_id:
        try:
            st.json(resize.resize_for_social_media(design_id, platforms, client=client))
        except Exception as exc:
            st.error(str(exc))
elif skill == "Bulk Create":
    st.subheader("Criação em massa")
    template_id = st.text_input("Brand Template ID")
    rows = st.text_area("Dados JSON — uma lista de objectos", value='[{"titulo": "Exemplo"}]')
    if st.button("Criar thumbnails em lote"):
        try:
            result = bulk.bulk_create_thumbnails(template_id, json.loads(rows), client=client)
            st.json(result)
        except Exception as exc:
            st.error(str(exc))
elif skill == "Design Feedback":
    st.subheader("Feedback estruturado")
    design_id = st.text_input("ID do design Canva")
    if st.button("Analisar design") and design_id:
        try:
            st.json(feedback.get_design_feedback(design_id, client=client))
        except Exception as exc:
            st.error(str(exc))
elif skill == "Edit Design":
    st.subheader("Edição segura")
    design_id = st.text_input("ID do design Canva")
    changes = st.text_area("Alterações JSON", value='{"texts": []}')
    approved = st.checkbox("Aprovar preparação da alteração")
    if st.button("Preparar edição") and design_id:
        try:
            st.json(edit.edit_design(design_id, json.loads(changes), client=client, auto_commit=approved))
        except Exception as exc:
            st.error(str(exc))
else:
    if skill == "Brand Check":
        st.subheader("Verificação de marca")
        design_id = st.text_input("ID do design Canva")
        if st.button("Listar Brand Templates"):
            try:
                st.session_state["canva_brand_templates"] = brand.list_brand_kits(client=client)
            except Exception as exc:
                st.error(str(exc))
        templates = st.session_state.get("canva_brand_templates", [])
        selected = st.selectbox("Brand Template", templates, format_func=lambda item: item.get("title", item.get("id", ""))) if templates else None
        if st.button("Verificar conformidade") and design_id and selected:
            try:
                st.json(brand.check_brand_compliance(design_id, selected["id"], client=client))
            except Exception as exc:
                st.error(str(exc))
