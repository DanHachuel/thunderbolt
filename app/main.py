from __future__ import annotations

import json
import re
from datetime import date
import sys
from pathlib import Path

import requests
import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
try:
    APP_VERSION = json.loads((ROOT / "package.json").read_text(encoding="utf-8")).get("version", "")
except (OSError, json.JSONDecodeError):
    APP_VERSION = ""

from hermes_ui.domain import STAGES, create_batch, create_channel, create_tasks_for_batch, delete_channel, pipeline_summary, set_channel_defaults, transition_task, update_channel
from hermes_ui.storage import BLUEPRINTS, ensure_storage, list_blueprint_files, load_blueprint_file, now, read_json, write_json
from app.modules.niche_finder.core import NicheAnalysisError, run_niche_analysis
from app.modules.niche_finder.data_loader import DatasetError, download_kaggle_dataset, list_cached_datasets, load_dataframe, save_uploaded_csv
from hermes_ui.blueprints import create_blueprint_from_link, list_branding_files, save_generated_blueprint
from hermes_ui.metadata_cleaner import build_description, clean_video_metadata, list_edit_records, metadata_manifest, normalize_tags, save_edit_record, store_external_video
from hermes_ui.mcp import detect_local_service, install_skill_locally, load_integrations, load_server_config, read_packaged_skill, save_server_config, update_integration
from hermes_ui.mcp_server import server_status, start_server, stop_server
from hermes_ui.music import list_music_files, materialize_suno_audio, request_suno_generation, store_music_file
from hermes_ui.voice_preview import DEFAULT_SAMPLE, load_preview_file, synthesize_preview
from integrations.platforms import IntegrationResult, TikTokAdapter, YouTubeAdapter
from integrations.youtube_direct_upload import YouTubeDirectUploader
from integrations.local_runtime import MoneyPrinterRuntime
from integrations.moneyprinter_config import sync_moneyprinter_config

AI_STYLE_OPTIONS = [
    "Natural Realista",
    "Cocomelon style",
    "Retro 90s Cartoon",
    "Wool sculpture miniatures",
    "LEGO Style",
    "Paper cutout style",
    "Anime Style",
    "Studio Ghibli Style",
    "Stop Motion Style (Massinha)",
    "Ukiyo Style",
    "Pixel Animation",
    "Pixar Style",
]

WIDE_STYLE_OPTIONS = ["Pexels/Pixabay", "full_ia", "Apenas Música"]

VIDEO_LANGUAGE_OPTIONS = [
    "00 – Apenas Música de Fundo (Sem Falas)",
    "01 – Inglês",
    "02 – Norueguês",
    "03 – Dinamarquês",
    "04 – Sueco",
    "05 – Holandês",
    "06 – Alemão",
    "07 – Luxemburguês",
    "08 – Finlandês",
    "09 – Hebraico",
    "10 – Japonês",
    "11 – Árabe (Golfo)",
    "12 – Islandês",
    "13 – Espanhol (Espanha)",
    "14 – Francês",
    "15 – Italiano",
    "16 – Coreano",
    "16 – Irlandês",
    "17 – Estoniano",
    "18 – Grego",
    "19 – Esloveno",
    "20 – Polonês",
    "21 – Tcheco",
    "22 – Lituano",
    "23 – Português (Portugal)",
    "24 – Eslovaco",
    "25 – Letão",
    "26 – Ucraniano",
    "27 – Húngaro",
    "28 – Afrikaans",
    "29 – Turco",
    "30 – Romeno",
    "31 – Russo",
    "32 – Croata",
    "33 – Árabe (Magreb)",
    "34 – Sérvio",
    "35 – Búlgaro",
    "36 – Português (Brasil)",
    "37 – Cantonês",
    "38 – Persa (Farsi)",
    "39 – Mandarim",
    "40 – Malaio",
    "41 – Espanhol (LatAm)",
    "42 – Vietnamita",
    "43 – Filipino (Tagalog)",
    "44 – Indonésio",
    "45 – Malayalam",
    "46 – Tailandês",
    "47 – Télugo",
    "48 – Tamil",
    "49 – Bengali",
    "50 – Hausa",
]

ensure_storage()
st.set_page_config(page_title="Thunderbolt", page_icon="T", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
<style>
:root { --accent:#35a7ff; --bg:#0b1118; --card:#121b26; }
[data-testid="stAppViewContainer"] { background: radial-gradient(circle at top right, #13283b 0, #0b1118 42%); }
[data-testid="stSidebar"] { background:#091018; border-right:1px solid #1d3448; }
[data-testid="stSidebar"] .block-container { padding-top:0.28rem; padding-bottom:0.45rem; }
[data-testid="stSidebar"] > div:first-child { padding-top:0.28rem; }
[data-testid="stSidebar"] .tb-brand { display:flex; align-items:baseline; gap:0.42rem; margin:0 0 0.68rem 0; white-space:nowrap; }
[data-testid="stSidebar"] .tb-brand-name { color:#f4f8fb; font-size:1.38rem; line-height:1.15; font-weight:750; letter-spacing:-0.02em; }
[data-testid="stSidebar"] .tb-brand-version { color:#8ba6bb; font-size:0.92rem; line-height:1; font-weight:500; }
[data-testid="stSidebar"] [data-testid="stButton"] { margin:0.025rem 0 !important; }
[data-testid="stSidebar"] [data-testid="stButton"] button { min-height:1.72rem; height:1.72rem; justify-content:flex-start !important; text-align:left !important; padding:0.10rem 0.52rem; border-radius:7px; border:1px solid transparent; font-size:0.86rem; font-weight:550; }
[data-testid="stSidebar"] [data-testid="stButton"] button > div { width:100% !important; justify-content:flex-start !important; text-align:left !important; }
[data-testid="stSidebar"] [data-testid="stButton"] button [data-testid="stMarkdownContainer"] { flex:1 1 auto !important; width:100% !important; text-align:left !important; }
[data-testid="stSidebar"] [data-testid="stButton"] p { margin:0; line-height:1; width:100%; text-align:left !important; }
[data-testid="stSidebar"] [data-testid="stBaseButton-secondary"] { background:transparent; color:#e7edf2; }
[data-testid="stSidebar"] [data-testid="stBaseButton-secondary"]:hover { background:#1c252e; border-color:#2d3944; color:#ffffff; }
[data-testid="stSidebar"] [data-testid="stBaseButton-primary"] { background:#292929; color:#ffffff; border-color:#3a3a3a; }
[data-testid="stSidebar"] [data-testid="stBaseButton-primary"]:hover { background:#343434; color:#ffffff; }
[data-testid="stSidebar"] [data-testid="stBaseButton-primary"] span { color:#ffffff; }
[data-testid="stSidebar"] [data-testid="stBaseButton-secondary"] span { color:#e7edf2; }
[data-testid="stSidebar"] [data-testid="stExpander"] { border:0 !important; background:transparent !important; margin:0.02rem 0 !important; }
[data-testid="stSidebar"] [data-testid="stExpander"] details { border:0 !important; background:transparent !important; }
[data-testid="stSidebar"] [data-testid="stExpander"] summary { min-height:1.72rem; padding:0.10rem 0.52rem !important; border-radius:7px; color:#e7edf2; font-size:0.86rem; font-weight:650; }
[data-testid="stSidebar"] [data-testid="stExpander"] summary:hover { background:#1c252e; }
[data-testid="stSidebar"] [data-testid="stExpander"] summary p { margin:0; line-height:1; }
[data-testid="stSidebar"] [data-testid="stExpander"] > div { padding:0 0 0 0.42rem !important; }
[data-testid="stSidebar"] [data-testid="stExpander"] > div [data-testid="stButton"] button { padding-left:0.92rem; font-size:0.83rem; min-height:1.62rem; height:1.62rem; }
.content-card { padding: 1rem 1.1rem; border:1px solid #20384d; border-radius:14px; background:rgba(18,27,38,.92); min-height:110px; }
.content-label { color:#8ba6bb; font-size:.8rem; text-transform:uppercase; letter-spacing:.07em; }
.content-value { color:#f4f8fb; font-size:1.8rem; font-weight:700; margin-top:.3rem; }
.stage { border-left:3px solid #35a7ff; padding:.65rem .8rem; margin:.4rem 0; background:#101d2a; border-radius:8px; }
.small-muted { color:#8ba6bb; font-size:.85rem; }
/* Cores dos chips por identidade da plataforma, sem depender da ordem de selecção. */
[data-testid="stMultiSelectTagsContainer"] span[data-tag] { color:#ffffff !important; border:0 !important; font-weight:700 !important; }
[data-testid="stMultiSelectTagsContainer"] span[data-tag] span[title],
[data-testid="stMultiSelectTagsContainer"] span[data-tag] button,
[data-testid="stMultiSelectTagsContainer"] span[data-tag] svg { color:#ffffff !important; fill:#ffffff !important; }
[data-testid="stMultiSelectTagsContainer"] span[data-tag][aria-label="YouTube"] { background:#ff0000 !important; }
[data-testid="stMultiSelectTagsContainer"] span[data-tag][aria-label="TikTok"] { background:#000000 !important; }
[data-testid="stMultiSelectTagsContainer"] span[data-tag][aria-label="Instagram"] { background:#e1306c !important; }
[data-testid="stMultiSelectTagsContainer"] span[data-tag][aria-label="Facebook Pages"] { background:#1877f2 !important; }
/* Compatibilidade com versões BaseWeb que usam data-baseweb=tag. */
[data-testid="stMultiSelect"] [data-baseweb="tag"] { color:#ffffff !important; border:0 !important; font-weight:700 !important; }
[data-testid="stMultiSelect"] [data-baseweb="tag"]:has(button[aria-label*="YouTube"]) { background:#ff0000 !important; }
[data-testid="stMultiSelect"] [data-baseweb="tag"]:has(button[aria-label*="TikTok"]) { background:#000000 !important; }
[data-testid="stMultiSelect"] [data-baseweb="tag"]:has(button[aria-label*="Instagram"]) { background:#e1306c !important; }
[data-testid="stMultiSelect"] [data-baseweb="tag"]:has(button[aria-label*="Facebook Pages"]) { background:#1877f2 !important; }
[data-testid="stMultiSelect"] [data-baseweb="tag"] svg { color:#ffffff !important; fill:#ffffff !important; }
</style>
""", unsafe_allow_html=True)


def card(label: str, value: str | int, note: str = ""):
    st.markdown(f'<div class="content-card"><div class="content-label">{label}</div><div class="content-value">{value}</div><div class="small-muted">{note}</div></div>', unsafe_allow_html=True)


def channel_options() -> list[dict]:
    return [c for c in read_json("channels.json", []) if c.get("active", True)]


def blueprint_catalog() -> list[tuple[str, str]]:
    options = [("", "Sem Blueprint padrão")]
    for path in list_blueprint_files():
        try:
            data = load_blueprint_file(path)
            identifier = str(data.get("id") or path.stem)
            label = str(data.get("name") or path.stem)
            options.append((identifier, label))
        except (OSError, ValueError, json.JSONDecodeError):
            continue
    return options


def valid_hhmm(value: str) -> bool:
    return bool(re.fullmatch(r"(?:[01]\d|2[0-3]):[0-5]\d", str(value or "").strip()))


def voice_catalog(current: str = "") -> list[str]:
    voices = [""]
    voice_file = ROOT / "integrations" / "data" / "azure_voices.json"
    try:
        voice_data = json.loads(voice_file.read_text(encoding="utf-8"))
        voices.extend(f"{item.get('name', '')}-{item.get('gender', '')}" for item in voice_data if item.get("name"))
    except (OSError, json.JSONDecodeError):
        pass
    for candidate in (current, "en-US-AriaNeural-Female", "pt-BR-FranciscaNeural-Female", "pt-BR-AntonioNeural-Male"):
        if candidate and candidate not in voices:
            voices.append(candidate)
    return voices


def channel_default_options(channel: dict) -> tuple[list[str], dict[str, str], str, list[str], str]:
    """Return synchronised Blueprint and voice options for a channel editor."""
    blueprint_items = blueprint_catalog()
    blueprint_ids = [item[0] for item in blueprint_items]
    blueprint_labels = {item[0]: item[1] for item in blueprint_items}
    current_blueprint = str(channel.get("default_blueprint_id") or channel.get("blueprint_id") or "")
    if current_blueprint and current_blueprint not in blueprint_ids:
        blueprint_ids.append(current_blueprint)
        blueprint_labels[current_blueprint] = current_blueprint
    current_voice = str(channel.get("default_voice") or channel.get("voice") or "")
    voice_options = voice_catalog(current_voice)
    return blueprint_ids, blueprint_labels, current_blueprint, voice_options, current_voice


def render_dashboard():
    st.title("Thunderbolt")
    st.caption("Interface local para operação e automação de conteúdo faceless")
    summary = pipeline_summary()
    cols = st.columns(6)
    for col, (label, value, note) in zip(cols, [("Canais", summary["channels"], f'{summary["active_channels"]} activos'), ("Tarefas", summary["total_tasks"], "total registado"), ("A fazer", summary["pending"], "na pipeline"), ("Em execução", summary["doing"], "a decorrer"), ("Concluídos", summary["done"], "artefactos prontos"), ("Falhas", summary["failed"], "requerem atenção")]):
        with col:
            card(label, value, note)
    st.divider()
    st.subheader("Pipeline")
    st.caption("Filas locais e dependências da cascata")
    queues = read_json("queues.json", {})
    blueprint_count = len(list_blueprint_files())
    for row_start in range(0, len(STAGES), 3):
        queue_cols = st.columns(3)
        for col, stage in zip(queue_cols, STAGES[row_start:row_start + 3]):
            with col:
                if stage == "blueprint":
                    card("Blueprints", blueprint_count, f"na biblioteca · {len(queues.get(stage, []))} tarefa(s) na fila")
                else:
                    card(stage.title(), len(queues.get(stage, [])), "fila")


def render_blueprints():
    st.title("Blueprints")
    st.caption(f"Biblioteca local lida directamente de `{BLUEPRINTS}`")
    blueprint_tab, branding_tab = st.tabs(["Blueprints", "Brandings"])
    with blueprint_tab:
        st.subheader("Criar blueprint a partir de link")
        with st.form("create_blueprint_from_link"):
            source_url = st.text_input("Link do canal ou vídeo YouTube", placeholder="https://www.youtube.com/@canal ou https://youtu.be/video")
            channel_name = st.text_input("Nome do canal, se conhecido")
            niche = st.text_input("Nicho alvo", placeholder="Ex.: filosofia, história, finanças pessoais")
            language = st.selectbox("Idioma do blueprint", ["Português (pt-BR)", "English", "Español"])
            creation_type = st.radio("O que deseja criar?", ["Apenas Blueprint", "Blueprint + Branding completo"], horizontal=True)
            create_submitted = st.form_submit_button("Criar a partir do link", type="primary")
        if create_submitted:
            try:
                blueprint, branding = create_blueprint_from_link(source_url, niche, language, creation_type == "Blueprint + Branding completo", channel_name)
                blueprint_path, branding_path = save_generated_blueprint(blueprint, branding)
                st.success(f"Blueprint criado: {blueprint_path.name}")
                if branding_path:
                    st.success(f"Branding completo criado: {branding_path.name}")
                st.rerun()
            except ValueError as exc:
                st.error(str(exc))
        st.divider()
        st.subheader("Importar blueprint JSON")
        uploaded = st.file_uploader("Subir novo blueprint JSON", type=["json"], key="blueprint_upload")
        target_folder = st.selectbox("Pasta", ["importados", "canais", "nichos"], key="blueprint_target_folder")
        if uploaded and st.button("Guardar blueprint JSON", type="secondary"):
            try:
                data = json.loads(uploaded.getvalue().decode("utf-8"))
                if not isinstance(data, dict):
                    raise ValueError("O JSON raiz deve ser um objecto.")
                safe_name = Path(uploaded.name).stem.replace(" ", "-") + ".json"
                destination = BLUEPRINTS / target_folder / safe_name
                if destination.exists() and not st.checkbox("Confirmar substituição", key="confirm_blueprint_replace"):
                    st.warning("O ficheiro já existe. Confirme a substituição.")
                else:
                    destination.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
                    st.success(f"Blueprint guardado em {destination}")
                    st.rerun()
            except (UnicodeDecodeError, json.JSONDecodeError, ValueError) as exc:
                st.error(f"JSON inválido: {exc}")
        files = list_blueprint_files()
        st.subheader(f"Blueprints existentes ({len(files)})")
        search = st.text_input("Pesquisar blueprints", key="blueprint_search")
        if not files:
            st.info("Ainda não existem blueprints na pasta local.")
        for path in files:
            if search and search.lower() not in path.name.lower():
                continue
            try:
                data = load_blueprint_file(path)
                title = data.get("channel_name") or data.get("name") or data.get("title") or path.stem
                with st.expander(f"{title} — {path.relative_to(BLUEPRINTS)}"):
                    st.caption(f"Ficheiro: {path}")
                    st.json(data)
            except Exception as exc:
                with st.expander(f"Inválido — {path.name}"):
                    st.error(str(exc))
    with branding_tab:
        st.subheader("Brandings completos")
        st.caption(f"Brandings gerados ou importados da pasta `{BLUEPRINTS / 'brandings'}`")
        branding_upload = st.file_uploader("Subir Branding JSON", type=["json"], key="branding_upload")
        if branding_upload and st.button("Guardar Branding", type="secondary"):
            try:
                data = json.loads(branding_upload.getvalue().decode("utf-8"))
                if not isinstance(data, dict):
                    raise ValueError("O JSON raiz deve ser um objecto.")
                target = BLUEPRINTS / "brandings" / (Path(branding_upload.name).stem.replace(" ", "-") + ".json")
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
                st.success(f"Branding guardado em {target}")
                st.rerun()
            except (UnicodeDecodeError, json.JSONDecodeError, ValueError) as exc:
                st.error(f"Branding JSON inválido: {exc}")
        branding_files = list_branding_files()
        st.write(f"{len(branding_files)} branding(s) encontrado(s)")
        branding_search = st.text_input("Pesquisar brandings", key="branding_search")
        if not branding_files:
            st.info("Ainda não existem brandings na pasta local.")
        for path in branding_files:
            if branding_search and branding_search.lower() not in path.name.lower():
                continue
            try:
                data = load_blueprint_file(path)
                title = data.get("name") or data.get("identity", {}).get("channel_name") or path.stem
                with st.expander(f"{title} — {path.name}"):
                    st.caption(f"Blueprint associado: {data.get('blueprint_id') or 'não associado'}")
                    st.json(data)
            except Exception as exc:
                with st.expander(f"Inválido — {path.name}"):
                    st.error(str(exc))


def render_channels():
    st.title("Canais")
    st.caption("Escolha entre importar dados públicos do YouTube ou preencher o canal manualmente.")
    settings = read_json("settings.json", {})
    youtube = YouTubeAdapter(settings=settings)
    import_tab, manual_tab = st.tabs(["Importar do YouTube", "Cadastro manual"])

    with import_tab:
        st.caption("A pesquisa pública funciona sem API Key. A Data API é opcional e fica disponível numa opção separada para métricas oficiais.")
        source = st.text_input("URL, handle ou ID do canal", placeholder="https://youtube.com/@seucanal", key="youtube_channel_source")
        lookup_mode = st.radio("Método de consulta", ["Página pública — sem API Key", "YouTube Data API — API Key opcional"], horizontal=True, key="youtube_channel_lookup_mode")
        col1, col2 = st.columns([1, 1])
        with col1:
            if st.button("Buscar no YouTube", type="primary", use_container_width=True, key="youtube_channel_lookup"):
                if lookup_mode.startswith("Página pública"):
                    result = youtube.fetch_channel_public(source)
                elif not youtube.api_key:
                    result = IntegrationResult(False, "A YouTube Data API Key não está configurada. Escolha a opção Página pública — sem API Key ou configure a chave em Configurações.", {"status": "api_key_not_configured"})
                else:
                    result = youtube.fetch_channel(source)
                st.session_state["yt_import"] = result.data
                st.session_state["yt_message"] = result.message
                st.session_state["yt_ok"] = result.ok
        with col2:
            if st.button("Limpar importação", use_container_width=True, key="youtube_channel_clear"):
                for key in ("yt_import", "yt_message", "yt_ok"):
                    st.session_state.pop(key, None)
                st.rerun()
        if st.session_state.get("yt_message"):
            (st.success if st.session_state.get("yt_ok") else st.warning)(st.session_state["yt_message"])
        imported = st.session_state.get("yt_import", {}) if st.session_state.get("yt_ok") else {}
        blueprint_items = blueprint_catalog()
        blueprint_ids = [item[0] for item in blueprint_items]
        blueprint_labels = {item[0]: item[1] for item in blueprint_items}
        imported_blueprint = imported.get("default_blueprint_id") or imported.get("blueprint_id", "")
        if imported_blueprint not in blueprint_ids:
            blueprint_ids.append(imported_blueprint)
            blueprint_labels[imported_blueprint] = imported_blueprint or "Sem Blueprint padrão"
        if imported:
            st.caption("Dados encontrados. Reveja ou edite os campos antes de guardar.")
            with st.form("channel_import_form"):
                name = st.text_input("Nome do canal", value=imported.get("name", ""), key="yt_import_name")
                url = st.text_input("URL", value=imported.get("url", source if source.startswith("http") else ""), key="yt_import_url")
                handle = st.text_input("Handle", value=imported.get("handle", ""), key="yt_import_handle")
                language = st.selectbox("Idioma", ["Português", "English", "Español", "Français", "Deutsch"], index=0, key="yt_import_language")
                style = st.selectbox("Estilo wide", ["Pexels/Pixabay", "full_ia", "Apenas Música"], index=0, key="yt_import_style")
                blueprint = st.selectbox("Blueprint padrão do canal", blueprint_ids, index=blueprint_ids.index(imported_blueprint) if imported_blueprint in blueprint_ids else 0, format_func=lambda item: blueprint_labels.get(item, item or "Sem Blueprint padrão"), key="yt_import_blueprint")
                voice_options = voice_catalog(imported.get("default_voice") or imported.get("voice", ""))
                current_voice = imported.get("default_voice") or imported.get("voice", "")
                voice = st.selectbox("Voz padrão do canal", voice_options, index=voice_options.index(current_voice) if current_voice in voice_options else 0, format_func=lambda item: item or "Sem voz padrão", key="yt_import_voice")
                delegated_session_id = st.text_input("DELEGATED_SESSION_ID", value=imported.get("delegated_session_id", ""), type="password", key="yt_import_delegated_session_id")
                automation_on = st.toggle("Automação ON", value=bool(imported.get("automation_on", False)), key="yt_import_automation_on")
                automation_time = st.text_input("Horário diário (HH:MM)", value=imported.get("automation_time", "00:00"), key="yt_import_automation_time")
                description = st.text_area("Descrição", value=imported.get("description", ""), key="yt_import_description")
                metrics = st.columns(3)
                with metrics[0]: subscriber_count = st.number_input("Inscritos", min_value=0, value=int(imported.get("subscriber_count") or 0), key="yt_import_subscribers")
                with metrics[1]: video_count = st.number_input("Vídeos", min_value=0, value=int(imported.get("video_count") or 0), key="yt_import_videos")
                with metrics[2]: view_count = st.number_input("Visualizações", min_value=0, value=int(imported.get("view_count") or 0), key="yt_import_views")
                submitted = st.form_submit_button("Guardar canal importado", type="primary")
                if submitted:
                    if not name.strip():
                        st.error("Informe o nome do canal antes de guardar.")
                    elif not valid_hhmm(automation_time):
                        st.error("O horário diário deve estar no formato HH:MM, por exemplo 08:30.")
                    else:
                        metadata = {
                            **imported,
                            "handle": handle.strip(),
                            "description": description.strip(),
                            "language": language,
                            "style_wide": {"Pexels/Pixabay": "pexels", "full_ia": "full_ia", "Apenas Música": "music"}.get(style, style),
                            "blueprint_id": blueprint.strip(),
                            "default_blueprint_id": blueprint.strip(),
                            "default_voice": voice.strip(),
                            "voice": voice.strip(),
                            "delegated_session_id": delegated_session_id.strip(),
                            "automation_on": bool(automation_on),
                            "automation_time": automation_time.strip() if valid_hhmm(automation_time) else "00:00",
                            "subscriber_count": int(subscriber_count) or None,
                            "video_count": int(video_count) or None,
                            "view_count": int(view_count) or None,
                            "metrics_source": imported.get("metrics_source", "youtube_public_page"),
                        }
                        channel = create_channel(name, url, metadata)
                        st.success(f"Canal {channel['name']} guardado.")
                        st.rerun()
        else:
            st.info("Introduza um URL, handle ou ID e clique em Buscar no YouTube. Não é necessária API Key na opção pública.")

    with manual_tab:
        st.caption("Este fluxo não consulta o YouTube e não exige API Key. Preencha os dados que quiser e guarde o canal localmente.")
        with st.form("channel_manual_form"):
            name = st.text_input("Nome do canal", key="manual_channel_name")
            url = st.text_input("URL do canal", placeholder="https://youtube.com/@seucanal", key="manual_channel_url")
            handle = st.text_input("Handle", placeholder="@seucanal", key="manual_channel_handle")
            description = st.text_area("Descrição", key="manual_channel_description")
            language = st.selectbox("Idioma", ["Português", "English", "Español", "Français", "Deutsch"], index=0, key="manual_channel_language")
            style = st.selectbox("Estilo wide", ["Pexels/Pixabay", "full_ia", "Apenas Música"], index=0, key="manual_channel_style")
            manual_blueprint_items = blueprint_catalog()
            manual_blueprint_ids = [item[0] for item in manual_blueprint_items]
            manual_blueprint_labels = {item[0]: item[1] for item in manual_blueprint_items}
            blueprint = st.selectbox("Blueprint padrão do canal", manual_blueprint_ids, format_func=lambda item: manual_blueprint_labels.get(item, item or "Sem Blueprint padrão"), key="manual_channel_blueprint")
            voice_options = voice_catalog()
            voice = st.selectbox("Voz padrão do canal", voice_options, format_func=lambda item: item or "Sem voz padrão", key="manual_channel_voice")
            delegated_session_id = st.text_input("DELEGATED_SESSION_ID", type="password", key="manual_channel_delegated_session_id")
            automation_on = st.toggle("Automação ON", value=False, key="manual_channel_automation_on")
            automation_time = st.text_input("Horário diário (HH:MM)", value="00:00", key="manual_channel_automation_time")
            thumbnail_url = st.text_input("URL da imagem do canal", key="manual_channel_thumbnail")
            metrics = st.columns(3)
            with metrics[0]: subscriber_count = st.number_input("Inscritos", min_value=0, value=0, key="manual_channel_subscribers")
            with metrics[1]: video_count = st.number_input("Vídeos", min_value=0, value=0, key="manual_channel_videos")
            with metrics[2]: view_count = st.number_input("Visualizações", min_value=0, value=0, key="manual_channel_views")
            submitted = st.form_submit_button("Guardar canal manual", type="primary")
            if submitted:
                if not name.strip():
                    st.error("Informe o nome do canal.")
                elif not valid_hhmm(automation_time):
                    st.error("O horário diário deve estar no formato HH:MM, por exemplo 08:30.")
                else:
                    channel = create_channel(name, url, {
                        "handle": handle.strip(),
                        "description": description.strip(),
                        "language": language,
                        "style_wide": {"Pexels/Pixabay": "pexels", "full_ia": "full_ia", "Apenas Música": "music"}.get(style, style),
                        "blueprint_id": blueprint.strip(),
                        "default_blueprint_id": blueprint.strip(),
                        "default_voice": voice.strip(),
                        "voice": voice.strip(),
                        "delegated_session_id": delegated_session_id.strip(),
                        "automation_on": bool(automation_on),
                        "automation_time": automation_time.strip(),
                        "thumbnail_url": thumbnail_url.strip(),
                        "subscriber_count": int(subscriber_count) or None,
                        "video_count": int(video_count) or None,
                        "view_count": int(view_count) or None,
                        "metrics_source": "manual",
                    })
                    st.success(f"Canal {channel['name']} guardado manualmente.")
                    st.rerun()

    st.subheader("Canais cadastrados")
    channels = read_json("channels.json", [])
    if not channels:
        st.info("Nenhum canal cadastrado.")
        return
    for channel in channels:
        with st.container(border=True):
            cols = st.columns([0.6, 2.2, 1.2, 1.2, 1.2, 1])
            with cols[0]:
                if channel.get("thumbnail_url"):
                    st.image(channel["thumbnail_url"], width=54)
                else:
                    st.markdown("### YT")
            with cols[1]:
                st.write(f"**{channel.get('name', 'Sem nome')}**")
                st.caption(f"{channel.get('handle') or channel.get('url') or 'sem URL'} · {channel.get('metrics_source', 'manual')}")
            with cols[2]: st.metric("Inscritos", channel.get("subscriber_count") if channel.get("subscriber_count") is not None else "—")
            with cols[3]: st.metric("Vídeos", channel.get("video_count") if channel.get("video_count") is not None else "—")
            with cols[4]: st.metric("Backlog", channel.get("backlog_total", 0))
            with cols[5]:
                active = st.toggle("Activo", value=channel.get("active", True), key=f"active_{channel['id']}")
                if active != channel.get("active"):
                    update_channel(channel["id"], {"active": active})
                    st.rerun()
                delete_key = f"delete_pending_{channel['id']}"
                if not st.session_state.get(delete_key, False):
                    if st.button("Apagar canal", key=f"delete_{channel['id']}", use_container_width=True):
                        st.session_state[delete_key] = True
                        st.rerun()
                else:
                    st.warning("As tarefas, vídeos e artefactos relacionados serão preservados.")
                    confirm_col, cancel_col = st.columns(2)
                    with confirm_col:
                        if st.button("Confirmar apagar", key=f"confirm_delete_{channel['id']}", type="primary", use_container_width=True):
                            removed = delete_channel(channel["id"])
                            st.session_state.pop(delete_key, None)
                            if removed:
                                st.success(f"Canal {removed.get('name', 'seleccionado')} apagado.")
                            st.rerun()
                    with cancel_col:
                        if st.button("Cancelar", key=f"cancel_delete_{channel['id']}", use_container_width=True):
                            st.session_state.pop(delete_key, None)
                            st.rerun()
            blueprint_ids, blueprint_labels, current_blueprint, voice_options, current_voice = channel_default_options(channel)
            with st.expander("Definir Blueprint e voz padrão", expanded=False):
                editor_cols = st.columns(2)
                with editor_cols[0]:
                    channel_blueprint = st.selectbox(
                        "Blueprint padrão",
                        blueprint_ids,
                        index=blueprint_ids.index(current_blueprint) if current_blueprint in blueprint_ids else 0,
                        format_func=lambda item: blueprint_labels.get(item, item or "Sem Blueprint padrão"),
                        key=f"channel_default_blueprint_{channel['id']}",
                    )
                with editor_cols[1]:
                    channel_voice = st.selectbox(
                        "Voz padrão",
                        voice_options,
                        index=voice_options.index(current_voice) if current_voice in voice_options else 0,
                        format_func=lambda item: item or "Sem voz padrão",
                        key=f"channel_default_voice_{channel['id']}",
                    )
                if st.button("Guardar Blueprint e voz", key=f"save_channel_defaults_{channel['id']}", type="primary"):
                    set_channel_defaults(channel["id"], channel_blueprint, channel_voice)
                    st.success("Blueprint padrão e voz padrão guardados para este canal.")
                    st.rerun()


def render_new_video(page_title: str = "Criação de Vídeos"):
    st.title(page_title)
    create_tab, videos_tab = st.tabs(["Criar vídeo", "Vídeos"])
    with create_tab:
        channels = channel_options()
        if not channels:
            st.warning("Cadastre pelo menos um canal antes de criar vídeos.")
        else:
            mode_label = st.radio("Modo de criação", ["Canal específico", "Lote no mesmo canal", "Lote geral"], horizontal=True, key="new_video_mode")
            mode = {"Canal específico": "single", "Lote no mesmo canal": "same_channel", "Lote geral": "general"}[mode_label]
            if mode == "general":
                selected = st.multiselect("Canais incluídos", [c["id"] for c in channels], default=[c["id"] for c in channels], format_func=lambda cid: next(c["name"] for c in channels if c["id"] == cid), key="new_video_channels_general")
            else:
                selected_one = st.selectbox("Canal", channels, format_func=lambda c: c["name"], key="new_video_channel")
                selected = [selected_one["id"]]
            wide_style_label = st.selectbox("Estilo wide", WIDE_STYLE_OPTIONS, key="new_video_style_wide")
            style_ia = st.selectbox("Estilo IA", AI_STYLE_OPTIONS, key="new_video_style_ia") if wide_style_label == "full_ia" else ""
            music_path = ""
            music_source = ""
            if wide_style_label == "Apenas Música":
                st.caption("Apenas Música não gera Pexels/Pixabay nem fundo IA; o áudio musical será usado como elemento principal.")
                music_source = st.radio("Fonte da música", ["Ficheiro existente", "Carregar ficheiro", "Criar via Suno API"], horizontal=True, key="new_video_music_source")
                if music_source == "Ficheiro existente":
                    local_music = list_music_files()
                    if local_music:
                        selected_music = st.selectbox("Música local", local_music, format_func=lambda item: item.name, key="new_video_music_existing")
                        music_path = str(selected_music)
                    else:
                        st.warning("Ainda não existem músicas em storage/music. Escolha Carregar ficheiro ou Criar via Suno API.")
                elif music_source == "Carregar ficheiro":
                    uploaded_music = st.file_uploader("Carregar música", type=["mp3", "wav", "m4a", "aac", "flac", "ogg"], key="new_video_music_upload")
                    if uploaded_music and st.button("Guardar música local", key="new_video_music_store", use_container_width=True):
                        try:
                            stored_music = store_music_file(uploaded_music.name, uploaded_music.getvalue())
                            st.session_state["new_video_music_path"] = str(stored_music)
                            st.success(f"Música guardada em `{stored_music}`")
                        except (OSError, ValueError) as exc:
                            st.error(str(exc))
                    music_path = st.session_state.get("new_video_music_path", "")
                else:
                    suno_prompt = st.text_area("Prompt musical Suno", placeholder="Instrumental cinematográfico, calmo, sem voz...", key="new_video_suno_prompt")
                    suno_title = st.text_input("Título da música", value=topic if "topic" in locals() else "Thunderbolt music", key="new_video_suno_title")
                    if st.button("Solicitar música no Suno", key="new_video_suno_request", use_container_width=True):
                        suno_result = request_suno_generation(read_json("settings.json", {}), suno_prompt, suno_title)
                        (st.success if suno_result["ok"] else st.error)(suno_result["message"])
                        if suno_result["ok"]:
                            try:
                                generated = materialize_suno_audio(suno_result.get("data", {}), suno_title or "suno-generated.mp3")
                                if generated:
                                    st.session_state["new_video_music_path"] = str(generated)
                                    st.success(f"Música descarregada para `{generated}`")
                                else:
                                    st.info("O pedido foi aceite, mas o endpoint ainda não devolveu uma URL de áudio. Consulte o estado no serviço Suno e adicione o ficheiro quando estiver pronto.")
                            except (OSError, requests.RequestException, ValueError) as exc:
                                st.warning(f"Pedido criado, mas não foi possível descarregar o áudio: {exc}")
                    music_path = st.session_state.get("new_video_music_path", "")
            with st.form("new_video_form"):
                topic = st.text_area("Tópico ou briefing", placeholder="Ex.: A história pouco conhecida por trás de...")
                quantity = st.number_input("Quantidade", min_value=1, max_value=100, value=1, disabled=mode != "same_channel")
                legacy_language = st.session_state.get("video_language")
                legacy_language_map = {
                    "Português": "36 – Português (Brasil)",
                    "English": "01 – Inglês",
                    "Español": "41 – Espanhol (LatAm)",
                }
                if legacy_language not in VIDEO_LANGUAGE_OPTIONS:
                    st.session_state["video_language"] = legacy_language_map.get(legacy_language, VIDEO_LANGUAGE_OPTIONS[0])
                language = st.selectbox("Idioma", VIDEO_LANGUAGE_OPTIONS, key="video_language")
                fmt = st.selectbox("Formato", ["wide", "shorts", "music"])
                submitted = st.form_submit_button("Criar tarefas", type="primary")
            if submitted:
                if not topic.strip() or not selected:
                    st.error("Informe um tópico e seleccione pelo menos um canal.")
                else:
                    quantity = int(quantity if mode == "same_channel" else 1)
                    style = {"Pexels/Pixabay": "pexels", "full_ia": "full_ia", "Apenas Música": "music"}[wide_style_label]
                    if style == "music" and not music_path:
                        st.error("Escolha, carregue ou gere uma música antes de criar o vídeo Apenas Música.")
                        st.stop()
                    batch = create_batch(mode, selected, topic, quantity, {"language": language, "format": fmt, "style_wide": style, "style_ia": style_ia, "music_mode": style == "music", "background_mode": "none" if style == "music" else ("ai" if style == "full_ia" else "stock"), "music_path": music_path, "music_source": music_source})
                    tasks = create_tasks_for_batch(batch)
                    st.success(f"Lote {batch['id']} criado com {len(tasks)} tarefa(s). Abra a subaba Vídeos para acompanhar.")
    with videos_tab:
        render_videos()


def render_music_creation():
    """Expose the complete video-creation UI under the music-oriented navigation entry without changing the original page."""
    render_new_video(page_title="Criação de Músicas")


@st.cache_data(show_spinner=False)
def _cached_niche_dataset(path_str: str, modified_ns: int):
    return load_dataframe(path_str)


@st.cache_data(show_spinner=False)
def _cached_niche_download():
    return str(download_kaggle_dataset())


def _niche_tag_options(frame) -> list[str]:
    tags: set[str] = set()
    for value in frame.get("video_tags", []):
        text = str(value or "").replace('"', "").replace("'", "")
        for tag in re.split(r"[|,]", text.strip("[]")):
            tag = re.sub(r"\s+", " ", tag).strip().lower()
            if tag and tag not in {"nan", "none", "null"}:
                tags.add(tag)
    return sorted(tags)


def _niche_date_bounds(frame):
    dates = frame["publish_date"].dropna().astype(str)
    if dates.empty:
        return None, None
    return dates.min(), dates.max()


def render_niche_finder():
    st.title("Niche Finder")
    st.caption("Busca de nichos baseada no projecto open source Niche-Finder, integrada no processo Streamlit do Thunderbolt.")
    st.info("A análise é executada localmente, sem Flask ou segundo servidor. O dataset padrão é guardado em `storage/data/niches/` e pode ser substituído por um CSV próprio.")

    with st.sidebar:
        st.subheader("Fonte de dados")
        uploaded_file = st.file_uploader("Carregar CSV próprio", type=["csv"], key="niche_uploaded_csv")
        if st.button("Baixar Dataset Kaggle", use_container_width=True, key="niche_download_dataset"):
            try:
                downloaded = _cached_niche_download()
                st.session_state["niche_dataset_path"] = downloaded
                st.success("Dataset Kaggle guardado no storage local.")
                st.rerun()
            except DatasetError as exc:
                st.error(str(exc))
        cached = list_cached_datasets()
        if cached:
            labels = {str(path): path.relative_to(path.parents[2]).as_posix() if len(path.parents) > 2 else path.name for path in cached}
            current_path = st.session_state.get("niche_dataset_path", str(cached[0]))
            if current_path not in labels:
                current_path = str(cached[0])
            selected_path = st.selectbox("Dataset local", list(labels), index=list(labels).index(current_path), format_func=lambda item: labels[item], key="niche_dataset_selector")
            if selected_path != st.session_state.get("niche_dataset_path"):
                st.session_state["niche_dataset_path"] = selected_path
                st.session_state.pop("niche_results", None)
                st.rerun()
        if uploaded_file is not None and st.button("Usar CSV carregado", use_container_width=True, key="niche_use_uploaded"):
            try:
                uploaded_path = save_uploaded_csv(uploaded_file.getvalue(), uploaded_file.name)
                st.session_state["niche_dataset_path"] = str(uploaded_path)
                st.session_state.pop("niche_results", None)
                st.success(f"CSV guardado em `{uploaded_path}`.")
                st.rerun()
            except DatasetError as exc:
                st.error(str(exc))

    dataset_path = st.session_state.get("niche_dataset_path")
    frame = None
    if dataset_path:
        path = Path(dataset_path)
        if path.exists():
            try:
                frame = _cached_niche_dataset(str(path), path.stat().st_mtime_ns)
            except (DatasetError, OSError) as exc:
                st.error(str(exc))
        else:
            st.warning("O dataset seleccionado já não existe no storage local. Baixe-o novamente ou carregue um CSV.")
    if frame is None:
        st.subheader("Começar uma análise")
        st.write("Baixe o dataset público do Kaggle ou carregue um CSV com as colunas `title`, `publish_date`, `country`, `view_count`, `like_count` e `comment_count`.")
        return

    min_date, max_date = _niche_date_bounds(frame)
    countries = ["Todos"] + sorted(str(value) for value in frame["country"].dropna().unique())
    tag_options = _niche_tag_options(frame)
    with st.sidebar:
        st.subheader("Parâmetros")
        n_clusters = st.slider("Número de Clusters", 2, 10, 5, key="niche_n_clusters")
        min_support = st.slider("Suporte Mínimo", 0.01, 0.5, 0.05, 0.01, format="%.2f", key="niche_min_support")
        country = st.selectbox("País", countries, key="niche_country")
        engagement = st.selectbox("Engagement", ["Todos", "High", "Moderate", "Low"], key="niche_engagement")
        start_date = st.date_input("Data inicial", value=date.fromisoformat(min_date), min_value=date.fromisoformat(min_date), max_value=date.fromisoformat(max_date), key="niche_start_date") if min_date else None
        end_date = st.date_input("Data final", value=date.fromisoformat(max_date), min_value=date.fromisoformat(min_date), max_value=date.fromisoformat(max_date), key="niche_end_date") if max_date else None
        selected_tags = st.multiselect("Tags opcionais", tag_options, key="niche_tags")
        analyse = st.button("Analisar Nichos", type="primary", use_container_width=True, key="niche_analyse")

    if analyse:
        try:
            if start_date and end_date and start_date > end_date:
                raise NicheAnalysisError("A data inicial não pode ser posterior à data final.")
            with st.spinner("A analisar clusters e associações…"):
                results = run_niche_analysis(
                    str(dataset_path),
                    n_clusters=n_clusters,
                    min_support=min_support,
                    start_date=start_date.isoformat() if start_date else None,
                    end_date=end_date.isoformat() if end_date else None,
                    country=country,
                    engagement=engagement,
                    tags=selected_tags,
                )
            st.session_state["niche_results"] = results
        except (NicheAnalysisError, DatasetError, OSError) as exc:
            st.error(str(exc))

    results = st.session_state.get("niche_results")
    if not results:
        st.subheader("Dataset carregado")
        st.dataframe(frame.head(100), use_container_width=True, hide_index=True)
        st.caption(f"{len(frame):,} registos válidos carregados. Ajuste os parâmetros na barra lateral e clique em Analisar Nichos.")
        return

    summary = results.get("summary", {})
    metric_cols = st.columns(4)
    for col, (label, value) in zip(metric_cols, [("Registos filtrados", summary.get("rows_filtered", 0)), ("Clusters", summary.get("cluster_count", 0)), ("Itemsets frequentes", summary.get("frequent_item_count", 0)), ("Regras", summary.get("association_rule_count", 0))]):
        with col:
            card(label, value)

    cluster_table = results["clusters"]
    rules_table = results["association_rules"]
    items_table = results["frequent_items"]
    points = results["cluster_points"].copy()
    keyword = st.text_input("Filtrar palavras-chave nos clusters", key="niche_cluster_keyword", placeholder="Ex.: música, gaming, receitas")
    if keyword.strip():
        cluster_table = cluster_table[cluster_table["palavras"].str.contains(keyword.strip(), case=False, na=False)]
    tab_clusters, tab_rules, tab_data = st.tabs(["Clusters encontrados", "Regras de associação", "Dados filtrados"])
    with tab_clusters:
        st.dataframe(cluster_table, use_container_width=True, hide_index=True)
        if not points.empty:
            try:
                import plotly.express as px
                points["cluster"] = points["cluster_id"].astype(str)
                hover = [column for column in ["title", "channel_name", "country", "view_count", "engagement_rate"] if column in points.columns]
                figure = px.scatter(points, x="x", y="y", color="cluster", hover_data=hover, title="Distribuição dos clusters")
                figure.update_layout(legend_title_text="Cluster")
                st.plotly_chart(figure, use_container_width=True)
            except ImportError:
                st.warning("A visualização Plotly não está instalada. Execute a instalação incremental do Thunderbolt.")
    with tab_rules:
        if rules_table.empty:
            st.info("Não foram encontradas regras com o suporte e lift actuais. Reduza o suporte mínimo ou escolha outro filtro.")
        else:
            st.dataframe(rules_table, use_container_width=True, hide_index=True)
        if not items_table.empty:
            st.subheader("Itemsets frequentes")
            st.dataframe(items_table, use_container_width=True, hide_index=True)
    with tab_data:
        st.dataframe(results["raw_data"], use_container_width=True, hide_index=True)



def render_videos():
    st.subheader("Vídeos e backlog")
    st.caption("Acompanhamento dos vídeos criados, estados da pipeline e controlos de execução.")
    tasks = read_json("tasks.json", [])
    if not tasks:
        st.info("Nenhum vídeo criado.")
        return
    state_filter = st.selectbox("Filtrar por estado", ["Todos", "to_do", "doing", "blocked", "done", "failed", "cancelled"], key="videos_state_filter")
    for task in tasks:
        if state_filter != "Todos" and task.get("state") != state_filter:
            continue
        with st.container(border=True):
            cols = st.columns([2.2, 1, 1, 1.2, 1.8])
            with cols[0]:
                st.write(f"**{task.get('topic', 'Sem tópico')}**")
                st.caption(f"{task.get('channel_name')} · {task.get('id')}")
            with cols[1]: st.write(task.get("format", "wide"))
            with cols[2]: st.write(task.get("stage", "—"))
            with cols[3]: st.write(task.get("state", "—"))
            with cols[4]:
                a, b = st.columns(2)
                if task.get("state") in {"to_do", "blocked", "failed"} and a.button("Iniciar", key=f"start_{task['id']}"):
                    transition_task(task["id"], "doing")
                    st.rerun()
                if task.get("state") == "doing" and b.button("Parar", key=f"stop_{task['id']}"):
                    transition_task(task["id"], "blocked")
                    st.rerun()


def render_automation():
    st.title("Automação")
    st.caption("Agendamento diário da geração por canal. Esta versão configura e guarda a UI; não inicia gerações em segundo plano.")
    st.info("A geração só será executada quando existir um worker/agendador ligado à pipeline. Activar Automação ON não inicia um processo automaticamente nesta etapa.")
    channels = read_json("channels.json", [])
    if not channels:
        st.info("Nenhum canal cadastrado para configurar.")
    for channel in channels:
        channel_id = channel["id"]
        with st.container(border=True):
            cols = st.columns([0.55, 2.35, 1.35, 1.5, 1.35])
            with cols[0]:
                if channel.get("thumbnail_url"):
                    st.image(channel["thumbnail_url"], width=48)
                else:
                    st.markdown("### YT")
            with cols[1]:
                st.write(f"**{channel.get('name', 'Sem nome')}**")
                st.caption(channel.get("handle") or channel.get("url") or "sem URL")
                st.caption(f"Blueprint actual: {channel.get('default_blueprint_id') or channel.get('blueprint_id') or '—'} · Voz actual: {channel.get('default_voice') or channel.get('voice') or '—'}")
            blueprint_ids, blueprint_labels, current_blueprint, voice_options, current_voice = channel_default_options(channel)
            default_cols = st.columns(2)
            with default_cols[0]:
                automation_blueprint = st.selectbox(
                    "Blueprint padrão",
                    blueprint_ids,
                    index=blueprint_ids.index(current_blueprint) if current_blueprint in blueprint_ids else 0,
                    format_func=lambda item: blueprint_labels.get(item, item or "Sem Blueprint padrão"),
                    key=f"automation_blueprint_{channel_id}",
                )
            with default_cols[1]:
                automation_voice = st.selectbox(
                    "Voz padrão",
                    voice_options,
                    index=voice_options.index(current_voice) if current_voice in voice_options else 0,
                    format_func=lambda item: item or "Sem voz padrão",
                    key=f"automation_voice_{channel_id}",
                )
            with cols[2]:
                enabled = st.toggle("Automação ON", value=bool(channel.get("automation_on", False)), key=f"automation_on_{channel_id}")
            with cols[3]:
                schedule_time = st.text_input("Horário (HH:MM)", value=channel.get("automation_time", "00:00"), key=f"automation_time_{channel_id}")
            with cols[4]:
                if st.button("Guardar", key=f"automation_save_{channel_id}", use_container_width=True):
                    if not valid_hhmm(schedule_time):
                        st.error("Use o formato HH:MM, por exemplo 08:30.")
                    else:
                        update_channel(channel_id, {
                            "automation_on": bool(enabled),
                            "automation_time": schedule_time.strip(),
                        })
                        set_channel_defaults(channel_id, automation_blueprint, automation_voice)
                        st.success("Agendamento guardado.")
                        st.rerun()

    st.divider()
    st.subheader("Vídeos cadastrados")
    tasks = read_json("tasks.json", [])
    if not tasks:
        st.info("Ainda não existem vídeos cadastrados.")
    for task in tasks:
        with st.container(border=True):
            task_cols = st.columns([2.6, 1.3, 1.3, 1.5])
            with task_cols[0]:
                st.write(f"**{task.get('topic', 'Sem tópico')}**")
                st.caption(f"{task.get('channel_name', 'Canal')} · {task.get('id', '')}")
            with task_cols[1]:
                st.caption("Estado")
                st.write(task.get("state", "—"))
            with task_cols[2]:
                st.caption("Estilo")
                st.write(task.get("style_wide", "—"))
            with task_cols[3]:
                st.caption("Horário do canal")
                st.write(task.get("automation_time", "00:00"))


def render_upload_direct():
    st.subheader("Upload directo")
    st.caption("Upload interno baseado no YouTube-Video-Upload-Frontend-Api, sem usar a quota oficial da Data API. Este método requer cookies e tokens fornecidos manualmente pelo utilizador.")
    st.warning("Não cole cookies ou tokens em mensagens, issues ou Git. O Thunderbolt guarda-os apenas no storage local. A integração não extrai sessões automaticamente do navegador.")
    settings = read_json("settings.json", {})
    channels = read_json("channels.json", [])
    tasks = [task for task in read_json("tasks.json", []) if task.get("state") == "done" or task.get("artifacts", {}).get("video")]
    if not channels:
        st.info("Cadastre um canal e configure o DELEGATED_SESSION_ID antes de usar o upload directo.")
    if not tasks:
        st.info("Não há vídeos prontos para upload directo.")
        return
    channel_map = {channel.get("id"): channel for channel in channels}
    for task in tasks:
        channel = channel_map.get(task.get("channel_id"), {})
        video_path = (task.get("artifacts", {}) or {}).get("video", "")
        with st.container(border=True):
            st.write(f"**{task.get('topic', 'Sem tópico')}** — {task.get('channel_name', 'Canal')}")
            st.caption(video_path or "Sem caminho de vídeo registado")
            if not channel.get("delegated_session_id"):
                st.warning("Este canal não tem DELEGATED_SESSION_ID configurado na aba Canais.")
            direct_cols = st.columns([2.2, 1, 1])
            with direct_cols[0]:
                title = st.text_input("Título", value=task.get("topic", "Vídeo Thunderbolt"), key=f"direct_title_{task['id']}")
            with direct_cols[1]:
                privacy = st.selectbox("Privacidade", ["private", "unlisted", "public"], key=f"direct_privacy_{task['id']}")
            with direct_cols[2]:
                chunk_size = st.number_input("Chunk bytes", min_value=262144, step=262144, value=int(settings.get("direct_chunk_size", 262144)), key=f"direct_chunk_{task['id']}")
            description = st.text_area("Descrição", value=task.get("description", ""), key=f"direct_description_{task['id']}", height=90)
            if st.button("Enviar por Upload directo", type="primary", key=f"direct_upload_{task['id']}"):
                result = YouTubeDirectUploader(settings, channel).upload(video_path, title=title, description=description, visibility=privacy, chunk_size=int(chunk_size))
                record = {"task_id": task.get("id"), "channel_id": channel.get("id"), "destination": "YouTube direct frontend", "status": "published" if result.ok else "failed", "message": result.message, "data": result.data, "created_at": now()}
                uploads = read_json("uploads.json", [])
                uploads.append(record)
                write_json("uploads.json", uploads)
                (st.success if result.ok else st.error)(result.message)


def render_upload():
    st.title("Upload")
    upload_tab, direct_tab = st.tabs(["Upload convencional", "Upload directo"])
    with direct_tab:
        render_upload_direct()
    with upload_tab:
        render_upload_conventional()


def render_upload_conventional():
    st.title("Upload")
    settings = read_json("settings.json", {})
    youtube = YouTubeAdapter(settings=settings)
    tasks = [t for t in read_json("tasks.json", []) if t.get("state") == "done" or t.get("artifacts", {}).get("video")]
    destination = st.multiselect("Destinos", ["YouTube", "TikTok", "Instagram", "Facebook Pages"], default=["YouTube"], key="upload_destinations", placeholder="Seleccione os destinos")

    if "Instagram" in destination:
        st.info("Instagram está disponível no front end. A publicação real será ligada numa etapa de credenciais/API própria.")
    if "Facebook Pages" in destination:
        st.info("Facebook Pages está disponível no front end. A publicação real será ligada numa etapa de credenciais/API própria.")

    if "YouTube" in destination:
        st.markdown("**YouTube — youtube-automation-agent (principal)**")
        st.caption("O Thunderbolt executa internamente a lógica do PublishingSchedulingAgent: OAuth, upload resumível, metadados, thumbnail e legendas. O OAuth directo é usado apenas como redundância se o caminho principal falhar.")
        status = youtube.upload_status()
        status_cols = st.columns(2)
        with status_cols[0]:
            (st.success if status["agent"].ok else st.warning)(f"Agente: {status['agent'].message}")
            if st.button("Autorizar agente YouTube", key="youtube_authorize_agent", use_container_width=True):
                result = youtube.authorize_agent()
                (st.success if result.ok else st.error)(result.message)
                if result.ok:
                    st.rerun()
        with status_cols[1]:
            (st.info if status["fallback"].ok else st.caption)(f"Fallback OAuth: {status['fallback'].message}")
            if st.button("Autorizar fallback OAuth", key="youtube_authorize_fallback", use_container_width=True):
                result = youtube.authorize_fallback()
                (st.success if result.ok else st.error)(result.message)
                if result.ok:
                    st.rerun()
    if "TikTok" in destination:
        status = TikTokAdapter(settings).status()
        (st.success if status.ok else st.warning)(status.message)
    if not tasks:
        st.info("Não há vídeos prontos para upload.")
        return
    for task in tasks:
        with st.container(border=True):
            st.write(f"**{task.get('topic')}** — {task.get('channel_name')}")
            artifacts = task.get("artifacts", {}) or {}
            video_path = artifacts.get("video", "")
            thumbnail_path = artifacts.get("thumbnail") or artifacts.get("cover", "")
            captions_path = artifacts.get("captions") or artifacts.get("subtitle", "")
            st.caption(video_path or "Sem caminho de vídeo registado")
            if "YouTube" in destination:
                title = st.text_input("Título", value=task.get("topic", "Vídeo Thunderbolt"), key=f"yt_title_{task['id']}")
                description = st.text_area("Descrição", value=task.get("description", ""), key=f"yt_description_{task['id']}", height=100)
                tags_raw = st.text_input("Tags separadas por vírgula", value=task.get("tags", "") if isinstance(task.get("tags", ""), str) else ", ".join(task.get("tags", [])), key=f"yt_tags_{task['id']}")
                yt_cols = st.columns(3)
                with yt_cols[0]:
                    privacy_status = st.selectbox("Privacidade", ["private", "unlisted", "public"], key=f"yt_privacy_{task['id']}")
                with yt_cols[1]:
                    category_id = st.text_input("Category ID", value="22", key=f"yt_category_{task['id']}")
                with yt_cols[2]:
                    language = st.text_input("Idioma", value="pt-BR", key=f"yt_language_{task['id']}")
                if st.button("Publicar no YouTube", type="primary", key=f"upload_youtube_{task['id']}"):
                    tags = [tag.strip() for tag in tags_raw.split(",") if tag.strip()]
                    result = youtube.upload_video(
                        video_path,
                        title=title,
                        description=description,
                        tags=tags,
                        category_id=category_id,
                        language=language,
                        privacy_status=privacy_status,
                        thumbnail_path=thumbnail_path,
                        captions_path=captions_path,
                    )
                    record = {
                        "task_id": task.get("id"),
                        "destination": "YouTube",
                        "status": "published" if result.ok else "failed",
                        "message": result.message,
                        "data": result.data,
                        "created_at": now(),
                    }
                    uploads = read_json("uploads.json", [])
                    uploads.append(record)
                    write_json("uploads.json", uploads)
                    (st.success if result.ok else st.error)(result.message)
                    if result.data.get("attempts"):
                        with st.expander("Detalhes dos mecanismos de upload"):
                            st.json(result.data["attempts"])
            if "TikTok" in destination and st.button("Enviar para TikTok", key=f"upload_tiktok_{task['id']}"):
                result = TikTokAdapter(settings).upload_video(video_path, task.get("topic", ""))
                (st.success if result.ok else st.warning)(result.message)
            if "Instagram" in destination:
                st.button("Preparar Instagram", key=f"upload_instagram_{task['id']}", disabled=True, help="UI preparada; publicação Instagram ainda não está activa.")
            if "Facebook Pages" in destination:
                st.button("Preparar Facebook Pages", key=f"upload_facebook_{task['id']}", disabled=True, help="UI preparada; publicação Facebook Pages ainda não está activa.")


def render_settings():
    st.title("Configurações Técnicas")
    st.caption("Configuração do motor de vídeo e dos serviços usados pelo Thunderbolt. As credenciais ficam no storage local e não são enviadas para o GitHub.")
    settings = read_json("settings.json", {})

    def text_setting(label: str, key: str, *, secret: bool = False, help_text: str | None = None) -> str:
        return st.text_input(
            label,
            settings.get(key, ""),
            type="password" if secret else "default",
            help=help_text,
            key=f"settings_{key}",
        )

    with st.form("settings_form"):
        st.subheader("Execução local")
        port = st.number_input("Porta Streamlit", 1, 65535, int(settings.get("port", 3030)))
        moneyprinter_path = st.text_input("Pasta do motor de vídeo", settings.get("moneyprinter_path", ""), key="settings_moneyprinter_path")
        st.markdown("**YouTube — OAuth 2.0 e consulta pública**")
        st.caption("Para autorizar uploads, preencha apenas o YouTube OAuth Client ID e o YouTube OAuth Client Secret. Depois, autorize o agente na aba Upload. Estes dados identificam a aplicação OAuth; não são uma Data API Key nem um token de acesso.")
        youtube_cols = st.columns(2)
        with youtube_cols[0]:
            youtube_client_id = text_setting("YouTube OAuth Client ID", "youtube_client_id", help_text="Client ID do OAuth 2.0 criado no Google Cloud. É usado para iniciar a autorização da conta YouTube.")
        with youtube_cols[1]:
            youtube_client_secret = text_setting("YouTube OAuth Client Secret", "youtube_client_secret", secret=True, help_text="Client Secret do mesmo cliente OAuth 2.0. Não é uma API Key.")
        with st.expander("Consulta oficial de métricas — opcional"):
            st.caption("A YouTube Data API Key é uma credencial Google Cloud separada do OAuth. Só é necessária se escolher o método YouTube Data API para consultar métricas oficiais. Não é necessária para Página pública — sem API Key, para autorizar OAuth ou para fazer upload.")
            youtube_api_key = text_setting("YouTube Data API Key (opcional)", "youtube_api_key", secret=True, help_text="Credencial separada, criada em Google Cloud > APIs e serviços > Credenciais > Chave de API. Não cole aqui o Client ID nem o Client Secret.")

        with st.expander("Upload directo — sessão YouTube Frontend API"):
            st.caption("Campos usados apenas pelo método Upload directo. Não são necessários para o youtube-automation-agent nem para a Data API pública.")
            direct_cookie_cols = st.columns(3)
            with direct_cookie_cols[0]:
                direct_cookie_sid = text_setting("SID", "direct_cookie_sid", secret=True)
                direct_cookie_ssid = text_setting("SSID", "direct_cookie_ssid", secret=True)
            with direct_cookie_cols[1]:
                direct_cookie_hsid = text_setting("HSID", "direct_cookie_hsid", secret=True)
                direct_cookie_apisid = text_setting("APISID", "direct_cookie_apisid", secret=True)
            with direct_cookie_cols[2]:
                direct_cookie_sapisid = text_setting("SAPISID", "direct_cookie_sapisid", secret=True)
                direct_session_info = text_setting("sessionInfo token", "direct_session_info", secret=True)
            direct_innertube_api_key = text_setting("INNERTUBE_API_KEY", "direct_innertube_api_key", secret=True)
            direct_chunk_size = st.number_input("Chunk size (múltiplo de 262144)", min_value=262144, step=262144, value=int(settings.get("direct_chunk_size", 262144)))

        with st.expander("Serviço, materiais e rede"):
            cols = st.columns(2)
            with cols[0]:
                log_level = st.selectbox("Log level", ["DEBUG", "INFO", "WARNING", "ERROR"], index=["DEBUG", "INFO", "WARNING", "ERROR"].index(settings.get("log_level", "DEBUG")) if settings.get("log_level", "DEBUG") in ["DEBUG", "INFO", "WARNING", "ERROR"] else 0)
                listen_host = text_setting("API listen host", "listen_host")
                listen_port = st.number_input("API listen port", 1, 65535, int(settings.get("listen_port", 8080)))
                video_source = st.selectbox("Fonte de materiais", ["pexels", "pixabay", "coverr", "loomloom", "local"], index=["pexels", "pixabay", "coverr", "loomloom", "local"].index(settings.get("video_source", "pexels")) if settings.get("video_source", "pexels") in ["pexels", "pixabay", "coverr", "loomloom", "local"] else 0)
            with cols[1]:
                endpoint = text_setting("Endpoint público", "endpoint")
                proxy_http = text_setting("Proxy HTTP", "proxy_http")
                proxy_https = text_setting("Proxy HTTPS", "proxy_https")
                match_materials_to_script = st.checkbox("Alinhar materiais ao roteiro", bool(settings.get("match_materials_to_script", False)))

        with st.expander("LLM — providers e modelos", expanded=True):
            provider_options = ["moonshot", "shengsuanyun", "openai", "gemini", "deepseek", "qwen", "azure", "volcengine", "grok", "minimax", "mimo", "cloudflare", "modelscope", "aihubmix", "aimlapi", "evolink", "ollama", "oneapi", "litellm", "groq", "pollinations"]
            llm_provider = st.selectbox("LLM provider", provider_options, index=provider_options.index(settings.get("llm_provider", "moonshot")) if settings.get("llm_provider", "moonshot") in provider_options else 0)
            st.markdown("**OpenAI — API key, Base URL e modelo**")
            openai_cols = st.columns(3)
            with openai_cols[0]:
                openai_api_key = text_setting("OpenAI API key", "openai_api_key", secret=True)
            with openai_cols[1]:
                openai_base_url = text_setting("OpenAI Base URL", "openai_base_url", help_text="Opcional. Deixe vazio para a API oficial ou indique um endpoint compatível.")
            with openai_cols[2]:
                openai_model_name = text_setting("OpenAI model", "openai_model_name", help_text="Ex.: gpt-4o, gpt-4.1 ou o modelo disponibilizado pelo seu endpoint.")
            llm_fields = [
                ("Moonshot / Kimi", "moonshot", True), ("Shengsuan Cloud", "shengsuanyun", True),
                ("Google Gemini", "gemini", True), ("DeepSeek", "deepseek", True), ("Alibaba Qwen", "qwen", True),
                ("Azure OpenAI", "azure", True), ("VolcEngine Ark", "volcengine", True), ("xAI Grok", "grok", True),
                ("MiniMax", "minimax", True), ("Xiaomi MiMo", "mimo", True), ("Cloudflare AI Gateway", "cloudflare", True),
                ("ModelScope", "modelscope", True), ("AIHubMix", "aihubmix", True), ("AIML API", "aimlapi", True),
                ("EvoLink", "evolink", True), ("Ollama", "ollama", False), ("OneAPI", "oneapi", True),
                ("LiteLLM", "litellm", False), ("Groq", "groq", True), ("Pollinations AI", "pollinations", True),
            ]
            for label, prefix, has_key in llm_fields:
                st.markdown(f"**{label}**")
                cols = st.columns(3)
                with cols[0]:
                    if has_key:
                        settings[f"{prefix}_api_key"] = text_setting("API key", f"{prefix}_api_key", secret=True)
                    else:
                        settings[f"{prefix}_api_key"] = settings.get(f"{prefix}_api_key", "")
                with cols[1]:
                    settings[f"{prefix}_base_url"] = text_setting("Base URL", f"{prefix}_base_url")
                with cols[2]:
                    settings[f"{prefix}_model_name"] = text_setting("Model", f"{prefix}_model_name")

        with st.expander("Voz, TTS e música — Azure Speech, restantes serviços e Suno", expanded=True):
            cols = st.columns(2)
            with cols[0]:
                azure_speech_key = text_setting("Azure Speech key", "azure_speech_key", secret=True)
                azure_speech_region = text_setting("Azure Speech region", "azure_speech_region")
                siliconflow_tts_api_key = text_setting("SiliconFlow TTS API key", "siliconflow_tts_api_key", secret=True)
                minimax_tts_api_key = text_setting("MiniMax TTS API key", "minimax_tts_api_key", secret=True)
                minimax_tts_base_url = text_setting("MiniMax TTS Base URL", "minimax_tts_base_url")
                minimax_tts_model_id = text_setting("MiniMax TTS model", "minimax_tts_model_id")
                minimax_tts_voice_id = text_setting("MiniMax TTS voice ID", "minimax_tts_voice_id")
            with cols[1]:
                elevenlabs_api_key = text_setting("ElevenLabs API key", "elevenlabs_api_key", secret=True)
                elevenlabs_model_id = text_setting("ElevenLabs model", "elevenlabs_model_id")
                chatterbox_base_url = text_setting("Chatterbox Base URL", "chatterbox_base_url")
                chatterbox_api_key = text_setting("Chatterbox API key", "chatterbox_api_key", secret=True)
                chatterbox_model_id = text_setting("Chatterbox model", "chatterbox_model_id")
                sonilo_api_key = text_setting("Sonilo API key", "sonilo_api_key", secret=True)
                sonilo_base_url = text_setting("Sonilo Base URL", "sonilo_base_url")
                st.markdown("**Suno — agente musical opcional**")
                suno_api_key = text_setting("Suno API key", "suno_api_key", secret=True)
                suno_api_base_url = text_setting("Suno API Base URL", "suno_api_base_url", help_text="Use o endpoint compatível fornecido pelo seu acesso Suno; não é inventado pelo Thunderbolt.")
                suno_api_endpoint = text_setting("Suno API endpoint", "suno_api_endpoint", help_text="Ex.: /api/generate")

        with st.expander("Vídeo, materiais, Whisper e FFmpeg"):
            cols = st.columns(2)
            with cols[0]:
                pexels_api_keys = text_setting("Pexels API keys", "pexels_api_keys", secret=True, help_text="Separe várias chaves por vírgula para rotação.")
                pixabay_api_keys = text_setting("Pixabay API keys", "pixabay_api_keys", secret=True)
                coverr_api_keys = text_setting("Coverr API keys", "coverr_api_keys", secret=True)
                twelvelabs_api_keys = text_setting("TwelveLabs API keys", "twelvelabs_api_keys", secret=True)
                material_directory = text_setting("Pasta de materiais", "material_directory")
            with cols[1]:
                subtitle_provider = st.selectbox("Subtitle provider", ["edge", "whisper", ""], index=["edge", "whisper", ""].index(settings.get("subtitle_provider", "edge")) if settings.get("subtitle_provider", "edge") in ["edge", "whisper", ""] else 0)
                ffmpeg_path = text_setting("Caminho FFmpeg", "ffmpeg_path")
                video_codec = text_setting("Codec de vídeo", "video_codec")
                whisper_model_size = text_setting("Whisper model", "whisper_model_size")
                whisper_device = st.selectbox("Whisper device", ["cpu", "cuda"], index=0 if settings.get("whisper_device", "cpu") == "cpu" else 1)
                whisper_compute_type = text_setting("Whisper compute type", "whisper_compute_type")

        with st.expander("TikTok for Developers — Client ID e Client Secret", expanded=True):
            st.caption("Apenas as credenciais da aplicação ficam nesta UI. Redirect URI, scopes, autorização e tokens são geridos no TikTok for Developers Playground.")
            tiktok_client_key = text_setting("TikTok Client ID", "tiktok_client_key", secret=True)
            tiktok_client_secret = text_setting("TikTok Client Secret", "tiktok_client_secret", secret=True)

        with st.expander("Publicação através do Upload-Post"):
            upload_post_enabled = st.checkbox("Activar Upload-Post", bool(settings.get("upload_post_enabled", False)))
            upload_post_api_key = text_setting("Upload-Post API key", "upload_post_api_key", secret=True)
            upload_post_username = text_setting("Upload-Post username", "upload_post_username")
            upload_post_platforms = text_setting("Plataformas Upload-Post", "upload_post_platforms")
            upload_post_auto_upload = st.checkbox("Publicar automaticamente após gerar", bool(settings.get("upload_post_auto_upload", False)))

        if st.form_submit_button("Guardar configurações do Thunderbolt", type="primary"):
            settings.update({
                "port": port, "moneyprinter_path": moneyprinter_path, "youtube_api_key": youtube_api_key,
                "youtube_client_id": youtube_client_id, "youtube_client_secret": youtube_client_secret,
                "direct_cookie_sid": direct_cookie_sid, "direct_cookie_ssid": direct_cookie_ssid, "direct_cookie_hsid": direct_cookie_hsid, "direct_cookie_apisid": direct_cookie_apisid, "direct_cookie_sapisid": direct_cookie_sapisid, "direct_session_info": direct_session_info, "direct_innertube_api_key": direct_innertube_api_key, "direct_chunk_size": direct_chunk_size,
                "log_level": log_level, "listen_host": listen_host, "listen_port": listen_port, "video_source": video_source,
                "endpoint": endpoint, "proxy_http": proxy_http, "proxy_https": proxy_https, "match_materials_to_script": match_materials_to_script,
                "llm_provider": llm_provider, "openai_api_key": openai_api_key, "openai_base_url": openai_base_url, "openai_model_name": openai_model_name,
                "azure_speech_key": azure_speech_key, "azure_speech_region": azure_speech_region,
                "siliconflow_tts_api_key": siliconflow_tts_api_key, "minimax_tts_api_key": minimax_tts_api_key,
                "minimax_tts_base_url": minimax_tts_base_url, "minimax_tts_model_id": minimax_tts_model_id, "minimax_tts_voice_id": minimax_tts_voice_id,
                "elevenlabs_api_key": elevenlabs_api_key, "elevenlabs_model_id": elevenlabs_model_id,
                "pexels_api_keys": pexels_api_keys, "pixabay_api_keys": pixabay_api_keys, "coverr_api_keys": coverr_api_keys, "twelvelabs_api_keys": twelvelabs_api_keys,
                "chatterbox_base_url": chatterbox_base_url, "chatterbox_api_key": chatterbox_api_key, "chatterbox_model_id": chatterbox_model_id,
                "sonilo_api_key": sonilo_api_key, "sonilo_base_url": sonilo_base_url, "suno_api_key": suno_api_key, "suno_api_base_url": suno_api_base_url, "suno_api_endpoint": suno_api_endpoint, "subtitle_provider": subtitle_provider,
                "ffmpeg_path": ffmpeg_path, "video_codec": video_codec, "material_directory": material_directory,
                "whisper_model_size": whisper_model_size, "whisper_device": whisper_device, "whisper_compute_type": whisper_compute_type,
                "tiktok_client_key": tiktok_client_key, "tiktok_client_secret": tiktok_client_secret,
                "upload_post_enabled": upload_post_enabled, "upload_post_api_key": upload_post_api_key,
                "upload_post_username": upload_post_username, "upload_post_platforms": upload_post_platforms,
                "upload_post_auto_upload": upload_post_auto_upload,
            })
            write_json("settings.json", settings)
            try:
                synced = sync_moneyprinter_config(settings, moneyprinter_path)
                if synced:
                    st.success(f"Configurações guardadas e sincronizadas com {synced}")
                else:
                    st.success("Configurações guardadas localmente. Indique uma pasta válida do motor de vídeo para sincronizar config.toml.")
            except Exception as exc:
                st.warning(f"Configurações locais guardadas, mas não foi possível sincronizar config.toml: {exc}")

    st.divider()
    st.subheader("Teste de vozes")
    st.caption("Este painel é exclusivamente um preview. O áudio gerado não altera vídeos, tarefas, Blueprints ou a configuração da pipeline.")
    preview_cols = st.columns([1.1, 2.2, 1.2])
    with preview_cols[0]:
        preview_provider = st.selectbox("Provider", ["edge", "azure_speech", "elevenlabs", "minimax", "siliconflow", "gemini", "chatterbox"], index=0, key="voice_preview_provider")
    with preview_cols[1]:
        if preview_provider in {"edge", "azure_speech"}:
            preview_voice_options = voice_catalog(settings.get("voice_preview_voice", "en-US-AriaNeural-Female"))
            preview_voice = st.selectbox("Voz", preview_voice_options, index=preview_voice_options.index(settings.get("voice_preview_voice", "en-US-AriaNeural-Female")) if settings.get("voice_preview_voice", "en-US-AriaNeural-Female") in preview_voice_options else 0, format_func=lambda item: item or "Escolha uma voz", key="voice_preview_voice")
        else:
            preview_voice = st.text_input("Voice ID", value=settings.get("voice_preview_voice", ""), key="voice_preview_voice_text")
    with preview_cols[2]:
        preview_rate = st.selectbox("Velocidade", ["-20%", "-10%", "+0%", "+10%", "+20%"], index=2, key="voice_preview_rate")
    preview_text = st.text_area("Texto de teste", value=DEFAULT_SAMPLE, max_chars=1000, height=110, key="voice_preview_text")
    if st.button("Testar voz", type="primary", key="voice_preview_generate"):
        st.session_state.pop("voice_preview_path", None)
        try:
            preview_path = synthesize_preview(preview_text, preview_provider, preview_voice, settings, preview_rate)
            st.session_state["voice_preview_path"] = str(preview_path)
            st.success("Amostra de voz gerada. Este ficheiro é apenas um preview.")
        except Exception as exc:
            st.error(f"Não foi possível gerar o preview: {exc}")
    preview_value = str(st.session_state.get("voice_preview_path", "") or "").strip()
    loaded_preview = load_preview_file(preview_value)
    if loaded_preview:
        preview_path, preview_data = loaded_preview
        st.audio(preview_data, format="audio/mpeg")
        st.download_button("Descarregar amostra", data=preview_data, file_name=preview_path.name, mime="audio/mpeg", key="voice_preview_download")
    elif preview_value:
        st.session_state.pop("voice_preview_path", None)
        st.warning("A amostra de voz anterior não é um ficheiro de áudio legível e foi removida do estado local. Teste a voz novamente.")


def render_mcp():
    st.title("MCP")
    st.caption("Clientes externos, servidor MCP do Thunderbolt e a skill local ficam separados para evitar confundir funções diferentes.")

    client_tab, server_tab, skill_tab = st.tabs(["Client MCP", "Servidor MCP", "Skill"])

    with client_tab:
        st.subheader("Client MCP")
        st.info("Configure aqui os serviços MCP externos que o Thunderbolt pode detectar passivamente. Activar uma integração guarda apenas a preferência; não instala nem inicia processos externos.")
        integrations = load_integrations()
        for integration in integrations:
            integration_id = integration["id"]
            with st.container(border=True):
                header_cols = st.columns([2.6, 1.15, 1.65, 1.2])
                with header_cols[0]:
                    st.write(f"**{integration['name']}**")
                    st.caption(f"{integration['protocol']} · {integration['description']}")
                    st.markdown(f"[Abrir repositório oficial]({integration['repository']})")
                with header_cols[1]:
                    port = st.number_input(
                        "Porta",
                        min_value=1,
                        max_value=65535,
                        value=int(integration.get("port", 8000)),
                        step=1,
                        key=f"mcp_port_{integration_id}",
                    )
                with header_cols[2]:
                    status = detect_local_service({**integration, "port": port})
                    if status["available"]:
                        st.success("Disponível")
                    else:
                        st.caption("Não detectado")
                    st.caption(status["message"])
                with header_cols[3]:
                    active = st.toggle("Activo", value=bool(integration.get("active", False)), key=f"mcp_active_{integration_id}")
                    if active != bool(integration.get("active", False)):
                        update_integration(integration_id, active=active)
                        st.rerun()

                st.caption(integration.get("endpoint_note", "Porta editável para o serviço local."))
                if st.button("Guardar porta", key=f"mcp_save_port_{integration_id}", use_container_width=True):
                    update_integration(integration_id, port=int(port))
                    st.success(f"Porta de {integration['name']} guardada: {int(port)}")
                    st.rerun()

    with server_tab:
        st.subheader("Servidor MCP")
        st.caption("Servidor local do Thunderbolt para ser descoberto por um agente compatível com MCP. O endpoint usa JSON-RPC sobre HTTP POST em `/mcp`.")
        st.warning("Por segurança, o servidor inicia apenas quando o activar explicitamente. Por padrão fica acessível somente neste computador em 127.0.0.1:3031.")
        server_config = load_server_config()
        if server_config.get("enabled") and not server_status().get("running"):
            try:
                start_server(
                    str(server_config.get("host", "127.0.0.1")),
                    int(server_config.get("port", 3031)),
                    str(server_config.get("auth_token", "")),
                    bool(server_config.get("write_enabled", False)),
                )
            except Exception as exc:
                st.error(f"Não foi possível iniciar o Servidor MCP guardado: {exc}")

        server_cols = st.columns([1.3, 1.4, 1.4])
        with server_cols[0]:
            server_enabled = st.checkbox("Servidor MCP ON", value=bool(server_config.get("enabled", False)), key="mcp_server_enabled")
        with server_cols[1]:
            server_host = st.text_input("Host", value=str(server_config.get("host", "127.0.0.1")), key="mcp_server_host", help="Use 127.0.0.1 para acesso local. Um host externo exige token.")
        with server_cols[2]:
            server_port = st.number_input("Porta do servidor", min_value=1, max_value=65535, value=int(server_config.get("port", 3031)), step=1, key="mcp_server_port")
        server_token = st.text_input("Token de acesso MCP (opcional no localhost)", value=str(server_config.get("auth_token", "")), type="password", key="mcp_server_token")
        write_enabled = st.checkbox("Permitir ferramentas de escrita", value=bool(server_config.get("write_enabled", False)), key="mcp_server_write", help="Desactivado por padrão. Quando activo, o agente pode criar lotes de vídeos através de uma ferramenta MCP; leituras continuam disponíveis sem esta opção.")
        if str(server_host).strip() not in {"127.0.0.1", "localhost", "::1"} and not str(server_token).strip():
            st.error("Para expor o servidor fora do computador local, defina um token de acesso MCP.")

        action_label = "Guardar e iniciar Servidor MCP" if server_enabled else "Guardar e parar Servidor MCP"
        if st.button(action_label, type="primary", key="mcp_server_save", use_container_width=True):
            try:
                saved = save_server_config(enabled=server_enabled, host=server_host, port=int(server_port), auth_token=server_token, write_enabled=write_enabled)
                if saved["enabled"]:
                    status = start_server(saved["host"], saved["port"], saved["auth_token"], saved["write_enabled"])
                    st.success(f"Servidor MCP activo em `{status['endpoint']}`")
                else:
                    stop_server()
                    st.success("Servidor MCP parado.")
                st.rerun()
            except Exception as exc:
                st.error(f"Não foi possível guardar/iniciar o Servidor MCP: {exc}")

        runtime = server_status()
        if runtime.get("running"):
            st.success(f"Servidor MCP activo: `{runtime['endpoint']}`")
            st.code(
                json.dumps(
                    {
                        "endpoint": runtime["endpoint"],
                        "health": runtime["health_endpoint"],
                        "transport": "Streamable HTTP / JSON-RPC POST",
                        "write_tools": runtime["write_enabled"],
                    },
                    ensure_ascii=False,
                    indent=2,
                ),
                language="json",
            )
            st.caption("Use o endpoint `/mcp` na configuração do agente. O endpoint `/health` serve apenas para verificar se o servidor está activo. Não partilhe o token.")
        else:
            st.info("Servidor MCP parado. As configurações ficam guardadas localmente e só são usadas depois de clicar em Guardar e iniciar.")
        st.markdown("**Ferramentas disponibilizadas**")
        st.write("Leitura: estado da pipeline, canais, vídeos e Blueprints. Ferramentas de escrita: criação de lotes de vídeos, apenas quando a opção de escrita estiver activada pelo utilizador.")

    with skill_tab:
        st.subheader("Skill")
        st.caption("A skill anexada pode ser guardada na pasta local do Thunderbolt ou descarregada como ficheiro Markdown. Nenhum dos quatro repositórios externos é copiado para o pacote.")
        skill_cols = st.columns(2)
        with skill_cols[0]:
            if st.button("Guardar skill localmente", type="primary", use_container_width=True, key="mcp_install_mpt_skill"):
                try:
                    destination = install_skill_locally()
                    st.success(f"Skill guardada em `{destination}`")
                except (FileNotFoundError, OSError) as exc:
                    st.error(f"Não foi possível guardar a skill: {exc}")
        with skill_cols[1]:
            try:
                skill_data = read_packaged_skill()
            except FileNotFoundError:
                skill_data = None
            if skill_data is not None:
                st.download_button(
                    "Descarregar skill .md",
                    data=skill_data,
                    file_name="moneyprinterturbo-video.md",
                    mime="text/markdown",
                    use_container_width=True,
                    key="mcp_download_mpt_skill",
                )
            else:
                st.warning("A skill ainda não está disponível nesta instalação.")


def render_metadata_cleaner():
    st.title("Limpador de Metadados")
    st.caption("Limpeza e edição de metadados para vídeos de terceiros que já estão prontos.")
    st.warning("Esta área aceita exclusivamente vídeos externos. Vídeos criados na aba Novo vídeo não são listados nem processados aqui.")

    uploaded = st.file_uploader(
        "Subir vídeo de terceiro",
        type=["mp4", "mov", "mkv", "webm", "avi", "m4v", "mpeg", "mpg"],
        help="O sistema cria uma cópia separada em storage/metadata_cleaner/originals e nunca altera o ficheiro original enviado.",
        key="metadata_external_video_upload",
    )
    if uploaded and st.button("Carregar vídeo externo", type="primary", key="metadata_store_external_video"):
        try:
            source, digest = store_external_video(uploaded.name, uploaded.getvalue())
            st.session_state["metadata_external_source"] = str(source)
            st.session_state["metadata_external_digest"] = digest
            st.session_state["metadata_external_name"] = uploaded.name
            st.success("Vídeo externo carregado numa área separada do pipeline de vídeos.")
        except ValueError as exc:
            st.error(str(exc))

    source_value = st.session_state.get("metadata_external_source", "")
    source = Path(source_value) if source_value else None
    if not source or not source.exists():
        st.info("Suba um vídeo de terceiro para começar. Nenhum vídeo produzido pelo sistema é usado nesta página.")
    else:
        st.divider()
        cols = st.columns([2, 1, 1])
        with cols[0]:
            st.write(f"**Vídeo externo:** {st.session_state.get('metadata_external_name', source.name)}")
            st.caption(f"Cópia original preservada em `{source}`")
        with cols[1]:
            st.metric("Tamanho", f"{source.stat().st_size / 1024 / 1024:.1f} MB")
        with cols[2]:
            if st.button("Trocar vídeo", key="metadata_clear_external_source"):
                for key in ["metadata_external_source", "metadata_external_digest", "metadata_external_name", "metadata_last_record"]:
                    st.session_state.pop(key, None)
                st.rerun()

        st.subheader("Metadados para a versão limpa")
        st.caption("A descrição segue o formato do workflow YTB Metadata Generator: preview, links e timestamps. As tags são guardadas sem hashtags.")
        with st.form("metadata_cleaner_form"):
            title = st.text_input("Título", value=source.stem.replace("-", " "))
            preview = st.text_area("Preview / descrição curta", height=90, help="O workflow recomenda uma prévia envolvente de 100 a 200 caracteres, sem hashtags.")
            links = st.text_area("Links", height=90, placeholder="Website: https://exemplo.com\nInstagram: https://instagram.com/exemplo")
            timestamps = st.text_area("Timestamps / capítulos", height=120, placeholder="00:00 Introdução\n00:45 Contexto\n02:10 Conclusão")
            tags = st.text_input("Tags SEO", placeholder="palavra-chave, tema do vídeo, canal dark")
            left, right = st.columns(2)
            with left:
                language = st.text_input("Idioma", value="pt-BR")
                creator = st.text_input("Criador / canal", value="")
                genre = st.text_input("Género", value="")
            with right:
                category_options = ["Não definido", "Film & Animation", "Autos & Vehicles", "Education", "Entertainment", "Howto & Style", "People & Blogs", "Science & Technology", "News & Politics"]
                category = st.selectbox("Categoria para o manifesto de upload", category_options)
                copyright_text = st.text_input("Copyright", value="")
                comment = st.text_input("Comentário interno", value="")
            apply = st.form_submit_button("Limpar e guardar nova versão", type="primary")

        if len(preview.strip()) and not 100 <= len(preview.strip()) <= 200:
            st.caption(f"Prévia: {len(preview.strip())} caracteres. O workflow de referência recomenda entre 100 e 200.")
        if apply:
            selected_tags = normalize_tags(tags)
            description = build_description(preview, links, timestamps)
            metadata = {
                "title": title.strip(),
                "description": description,
                "preview": preview.strip(),
                "links": links.strip(),
                "timestamps": timestamps.strip(),
                "tags": selected_tags,
                "language": language.strip(),
                "creator": creator.strip(),
                "genre": genre.strip(),
                "category": "" if category == "Não definido" else category,
                "copyright": copyright_text.strip(),
                "comment": comment.strip(),
            }
            if not metadata["title"]:
                st.error("Informe um título antes de limpar os metadados.")
            else:
                try:
                    output, run_info = clean_video_metadata(source, metadata, ffmpeg_path=read_json("settings.json", {}).get("ffmpeg_path", ""))
                    record = save_edit_record(source, output, metadata, run_info)
                    st.session_state["metadata_last_record"] = record
                    st.success("Metadados removidos e nova cópia criada. O original continua preservado.")
                except (FileNotFoundError, RuntimeError, ValueError) as exc:
                    st.error(str(exc))

        record = st.session_state.get("metadata_last_record")
        if record and Path(record.get("output_path", "")).exists():
            output = Path(record["output_path"])
            st.subheader("Resultado")
            st.write(f"**Ficheiro limpo:** `{output.name}`")
            mime = "video/mp4" if output.suffix.lower() == ".mp4" else "video/*"
            st.download_button("Descarregar vídeo limpo", data=output.read_bytes(), file_name=output.name, mime=mime, use_container_width=True, key="metadata_download_video")
            st.download_button("Descarregar manifesto de upload (JSON)", data=metadata_manifest(record), file_name=f"{output.stem}-metadata.json", mime="application/json", use_container_width=True, key="metadata_download_manifest")
            with st.expander("Pré-visualizar metadados"):
                st.json(record["metadata"])

    st.divider()
    st.subheader("Histórico do Limpador de metadado")
    records = list_edit_records()
    if not records:
        st.caption("Ainda não há edições registadas.")
    for record in records[:10]:
        output = Path(record.get("output_path", ""))
        with st.container(border=True):
            st.write(f"**{record.get('metadata', {}).get('title') or record.get('output_name')}**")
            st.caption(f"Terceiro · {record.get('created_at', '—')} · {record.get('output_name', 'sem saída')}")
            if output.exists():
                st.download_button("Descarregar", data=output.read_bytes(), file_name=output.name, mime="video/*", key=f"metadata_history_{record.get('id')}")


def render_pipeline():
    st.title("Pipeline")
    st.caption("Estado das filas locais e dependências da cascata")
    queues = read_json("queues.json", {})
    blueprint_count = len(list_blueprint_files())
    cols = st.columns(len(STAGES))
    for col, stage in zip(cols, STAGES):
        with col:
            if stage == "blueprint":
                card("Blueprints", blueprint_count, f"na biblioteca · {len(queues.get(stage, []))} tarefa(s) na fila")
            else:
                card(stage.title(), len(queues.get(stage, [])), "fila")


def main():
    pipeline_items = [
        ("Criação de Vídeos", ":material/add_circle:", "Criação de Vídeos"),
        ("Criação de Músicas", ":material/music_note:", "Criação de Músicas"),
        ("Upload", ":material/cloud_upload:", "Upload"),
        ("Limpador de Metadados", ":material/edit_note:", "Limpador de Metadados"),
    ]
    settings_items = [
        ("Canais", ":material/ondemand_video:", "Canais"),
        ("Blueprints", ":material/library_books:", "Blueprints"),
        ("MCP", ":material/hub:", "MCP"),
        ("Configurações Técnicas", ":material/settings:", "Configurações Técnicas"),
    ]
    top_pages = [
        ("Início", ":material/home:", "Início"),
        ("Pipeline", ":material/account_tree:", "Pipeline"),
        ("Automação", ":material/schedule:", "Automação"),
        ("Niche Finder", ":material/search:", "Niche Finder"),
        ("Configurações", ":material/settings:", "Configurações"),
    ]
    aliases = {
        "Dashboard": "Início",
        "Novo vídeo": "Criação de Vídeos",
        "Vídeos": "Criação de Vídeos",
        "Limpador de metadado": "Limpador de Metadados",
        "Configurações Técnicas": "Configurações Técnicas",
    }
    current_page = aliases.get(st.session_state.get("page", "Início"), st.session_state.get("page", "Início"))
    if current_page not in {item[0] for item in top_pages + pipeline_items + settings_items}:
        current_page = "Início"
    st.session_state["page"] = current_page

    def navigate(target: str):
        st.session_state["page"] = target
        st.rerun()

    def render_nav_button(target: str, icon: str, label: str, *, child: bool = False):
        if st.button(label, key=f"nav_{target}", icon=icon, use_container_width=True, type="primary" if current_page == target else "secondary"):
            navigate(target)

    with st.sidebar:
        version_markup = f'<span class="tb-brand-version">{APP_VERSION}</span>' if APP_VERSION else ""
        st.markdown(f'<div class="tb-brand"><span class="tb-brand-name">Thunderbolt</span>{version_markup}</div>', unsafe_allow_html=True)
        for target, icon, label in top_pages:
            if target == "Pipeline":
                with st.expander("Pipeline", expanded=current_page in {item[0] for item in pipeline_items}, icon=":material/account_tree:"):
                    for child_target, child_icon, child_label in pipeline_items:
                        render_nav_button(child_target, child_icon, child_label, child=True)
            elif target == "Configurações":
                with st.expander("Configurações", expanded=current_page in {item[0] for item in settings_items}, icon=":material/settings:"):
                    for child_target, child_icon, child_label in settings_items:
                        render_nav_button(child_target, child_icon, child_label, child=True)
            else:
                render_nav_button(target, icon, label)

    renderers = {
        "Início": render_dashboard,
        "Criação de Vídeos": render_new_video,
        "Criação de Músicas": render_music_creation,
        "Automação": render_automation,
        "Niche Finder": render_niche_finder,
        "Upload": render_upload,
        "Limpador de Metadados": render_metadata_cleaner,
        "Canais": render_channels,
        "Blueprints": render_blueprints,
        "MCP": render_mcp,
        "Configurações Técnicas": render_settings,
    }
    renderers.get(current_page, render_dashboard)()

if __name__ == "__main__":
    main()
