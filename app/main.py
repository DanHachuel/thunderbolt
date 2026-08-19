from __future__ import annotations

import json
import sys
from pathlib import Path

import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from hermes_ui.domain import STAGES, create_batch, create_channel, create_tasks_for_batch, pipeline_summary, transition_task, update_channel
from hermes_ui.storage import BLUEPRINTS, ensure_storage, list_blueprint_files, load_blueprint_file, now, read_json, write_json
from hermes_ui.blueprints import create_blueprint_from_link, list_branding_files, save_generated_blueprint
from hermes_ui.metadata_cleaner import build_description, clean_video_metadata, list_edit_records, metadata_manifest, normalize_tags, save_edit_record, store_external_video
from integrations.platforms import TikTokAdapter, YouTubeAdapter
from integrations.local_runtime import MoneyPrinterRuntime
from integrations.moneyprinter_config import sync_moneyprinter_config

ensure_storage()
st.set_page_config(page_title="MoneyPrinterTurbo UI", page_icon="M", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
<style>
:root { --accent:#35a7ff; --bg:#0b1118; --card:#121b26; }
[data-testid="stAppViewContainer"] { background: radial-gradient(circle at top right, #13283b 0, #0b1118 42%); }
[data-testid="stSidebar"] { background:#091018; border-right:1px solid #1d3448; }
[data-testid="stSidebar"] [data-testid="stButton"] { margin:0.18rem 0; }
[data-testid="stSidebar"] [data-testid="stButton"] button { min-height:2.55rem; justify-content:flex-start; text-align:left; padding:0.55rem 0.85rem; border-radius:10px; border:1px solid transparent; font-weight:600; }
[data-testid="stSidebar"] [data-testid="stBaseButton-secondary"] { background:transparent; color:#e7edf2; }
[data-testid="stSidebar"] [data-testid="stBaseButton-secondary"]:hover { background:#1c252e; border-color:#2d3944; color:#ffffff; }
[data-testid="stSidebar"] [data-testid="stBaseButton-primary"] { background:#292929; color:#ffffff; border-color:#3a3a3a; }
[data-testid="stSidebar"] [data-testid="stBaseButton-primary"]:hover { background:#343434; color:#ffffff; }
[data-testid="stSidebar"] [data-testid="stBaseButton-primary"] span { color:#ffffff; }
[data-testid="stSidebar"] [data-testid="stBaseButton-secondary"] span { color:#e7edf2; }
.content-card { padding: 1rem 1.1rem; border:1px solid #20384d; border-radius:14px; background:rgba(18,27,38,.92); min-height:110px; }
.content-label { color:#8ba6bb; font-size:.8rem; text-transform:uppercase; letter-spacing:.07em; }
.content-value { color:#f4f8fb; font-size:1.8rem; font-weight:700; margin-top:.3rem; }
.stage { border-left:3px solid #35a7ff; padding:.65rem .8rem; margin:.4rem 0; background:#101d2a; border-radius:8px; }
.small-muted { color:#8ba6bb; font-size:.85rem; }
/* Identidade visual dos destinos de upload: YouTube vermelho, TikTok preto. */
[data-testid="stMultiSelect"] [data-baseweb="tag"] { color:#ffffff !important; border:0 !important; font-weight:700 !important; }
[data-testid="stMultiSelect"] [data-baseweb="tag"] svg { color:#ffffff !important; fill:#ffffff !important; }
[data-testid="stMultiSelect"] [data-baseweb="tag"]:nth-child(1) { background:#ff4b4b !important; }
[data-testid="stMultiSelect"] [data-baseweb="tag"]:nth-child(2) { background:#000000 !important; }
</style>
""", unsafe_allow_html=True)


def card(label: str, value: str | int, note: str = ""):
    st.markdown(f'<div class="content-card"><div class="content-label">{label}</div><div class="content-value">{value}</div><div class="small-muted">{note}</div></div>', unsafe_allow_html=True)


def channel_options() -> list[dict]:
    return [c for c in read_json("channels.json", []) if c.get("active", True)]


def render_dashboard():
    st.title("MoneyPrinterTurbo UI")
    st.caption("Interface local para operação e automação de conteúdo faceless")
    summary = pipeline_summary()
    cols = st.columns(6)
    for col, (label, value, note) in zip(cols, [("Canais", summary["channels"], f'{summary["active_channels"]} activos'), ("Tarefas", summary["total_tasks"], "total registado"), ("A fazer", summary["pending"], "na pipeline"), ("Em execução", summary["doing"], "a decorrer"), ("Concluídos", summary["done"], "artefactos prontos"), ("Falhas", summary["failed"], "requerem atenção")]):
        with col:
            card(label, value, note)
    st.divider()
    left, right = st.columns([1.5, 1])
    with left:
        st.subheader("Pipeline")
        tasks = read_json("tasks.json", [])
        counts = {stage: sum(1 for t in tasks if t.get("stage") == stage and t.get("state") not in {"done", "cancelled"}) for stage in STAGES}
        for stage in STAGES:
            st.markdown(f'<div class="stage"><strong>{stage.title()}</strong> <span class="small-muted">{counts[stage]} tarefa(s)</span></div>', unsafe_allow_html=True)
    with right:
        st.subheader("Acções rápidas")
        if st.button("Criar novo vídeo", use_container_width=True):
            st.session_state["page"] = "Novo vídeo"
            st.rerun()
        if st.button("Importar canal", use_container_width=True):
            st.session_state["page"] = "Canais"
            st.rerun()
        if st.button("Abrir Blueprints", use_container_width=True):
            st.session_state["page"] = "Blueprints"
            st.rerun()
        if st.button("Abrir Upload", use_container_width=True):
            st.session_state["page"] = "Upload"
            st.rerun()


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
    st.caption("Importação do YouTube com edição manual e armazenamento local")
    with st.expander("Criar ou importar novo canal", expanded=True):
        source = st.text_input("Nome, URL, handle ou ID do canal", placeholder="https://youtube.com/@seucanal")
        col1, col2 = st.columns([1, 1])
        with col1:
            if st.button("Buscar no YouTube", type="primary", use_container_width=True):
                result = YouTubeAdapter(read_json("settings.json", {}).get("youtube_api_key", "")).fetch_channel(source)
                st.session_state["yt_import"] = result.data
                st.session_state["yt_message"] = result.message
                st.session_state["yt_ok"] = result.ok
        with col2:
            if st.button("Limpar importação", use_container_width=True):
                st.session_state.pop("yt_import", None)
        if st.session_state.get("yt_message"):
            (st.success if st.session_state.get("yt_ok") else st.warning)(st.session_state["yt_message"])
        imported = st.session_state.get("yt_import", {})
        with st.form("channel_form"):
            name = st.text_input("Nome do canal", value=imported.get("name", ""))
            url = st.text_input("URL", value=source if source.startswith("http") else imported.get("url", ""))
            handle = st.text_input("Handle", value=imported.get("handle", ""))
            language = st.selectbox("Idioma", ["Português", "English", "Español", "Français", "Deutsch"], index=0)
            style = st.selectbox("Estilo wide", ["pexels", "full_ia"], index=0)
            blueprint = st.text_input("Blueprint associado", value="")
            submitted = st.form_submit_button("Guardar canal", type="primary")
            if submitted:
                if not name.strip():
                    st.error("Informe o nome do canal.")
                else:
                    metadata = {"handle": handle, "language": language, "style_wide": style, "blueprint_id": blueprint, **imported}
                    channel = create_channel(name, url, metadata)
                    st.success(f"Canal {channel['name']} guardado.")
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
                st.caption(f"{channel.get('handle') or channel.get('url') or 'sem URL'}")
            with cols[2]: st.metric("Inscritos", channel.get("subscriber_count") if channel.get("subscriber_count") is not None else "—")
            with cols[3]: st.metric("Vídeos", channel.get("video_count") if channel.get("video_count") is not None else "—")
            with cols[4]: st.metric("Backlog", channel.get("backlog_total", 0))
            with cols[5]:
                active = st.toggle("Activo", value=channel.get("active", True), key=f"active_{channel['id']}")
                if active != channel.get("active"):
                    update_channel(channel["id"], {"active": active})


def render_new_video():
    st.title("Novo vídeo")
    channels = channel_options()
    if not channels:
        st.warning("Cadastre pelo menos um canal antes de criar vídeos.")
        return
    mode_label = st.radio("Modo de criação", ["Canal específico", "Lote no mesmo canal", "Lote geral"], horizontal=True)
    mode = {"Canal específico": "single", "Lote no mesmo canal": "same_channel", "Lote geral": "general"}[mode_label]
    if mode == "general":
        selected = st.multiselect("Canais incluídos", [c["id"] for c in channels], default=[c["id"] for c in channels], format_func=lambda cid: next(c["name"] for c in channels if c["id"] == cid))
    else:
        selected_one = st.selectbox("Canal", channels, format_func=lambda c: c["name"])
        selected = [selected_one["id"]]
    with st.form("new_video_form"):
        topic = st.text_area("Tópico ou briefing", placeholder="Ex.: A história pouco conhecida por trás de...")
        quantity = st.number_input("Quantidade", min_value=1, max_value=100, value=1, disabled=mode != "same_channel")
        language = st.selectbox("Idioma", ["Português", "English", "Español"], key="video_language")
        fmt = st.selectbox("Formato", ["wide", "shorts", "music"])
        style = st.selectbox("Estilo wide", ["pexels", "full_ia"])
        submitted = st.form_submit_button("Criar tarefas", type="primary")
    if submitted:
        if not topic.strip() or not selected:
            st.error("Informe um tópico e seleccione pelo menos um canal.")
        else:
            quantity = int(quantity if mode == "same_channel" else 1)
            batch = create_batch(mode, selected, topic, quantity, {"language": language, "format": fmt, "style_wide": style})
            tasks = create_tasks_for_batch(batch)
            st.success(f"Lote {batch['id']} criado com {len(tasks)} tarefa(s).")


def render_videos():
    st.title("Vídeos e backlog")
    tasks = read_json("tasks.json", [])
    if not tasks:
        st.info("Nenhum vídeo criado.")
        return
    state_filter = st.selectbox("Filtrar por estado", ["Todos", "to_do", "doing", "blocked", "done", "failed", "cancelled"])
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


def render_upload():
    st.title("Upload")
    tasks = [t for t in read_json("tasks.json", []) if t.get("state") == "done" or t.get("artifacts", {}).get("video")]
    destination = st.multiselect("Destinos", ["YouTube", "TikTok"], default=["YouTube"])
    if "TikTok" in destination:
        status = TikTokAdapter(read_json("settings.json", {})).status()
        (st.success if status.ok else st.warning)(status.message)
    if not tasks:
        st.info("Não há vídeos prontos para upload.")
        return
    for task in tasks:
        with st.container(border=True):
            st.write(f"**{task.get('topic')}** — {task.get('channel_name')}")
            video_path = task.get("artifacts", {}).get("video", "")
            st.caption(video_path or "Sem caminho de vídeo registado")
            if st.button("Preparar upload", key=f"upload_{task['id']}"):
                if "TikTok" in destination:
                    result = TikTokAdapter(read_json("settings.json", {})).upload_video(video_path, task.get("topic", ""))
                    (st.success if result.ok else st.warning)(result.message)
                else:
                    st.info("Upload YouTube preparado; configure o uploader local para executar a publicação.")


def render_settings():
    st.title("Configurações do MoneyPrinterTurbo")
    st.caption("Área compatível com config.toml do MoneyPrinterTurbo. As credenciais ficam no storage local e não são enviadas para o GitHub.")
    settings = read_json("settings.json", {})

    def text_setting(label: str, key: str, *, secret: bool = False, help_text: str | None = None) -> str:
        return st.text_input(label, settings.get(key, ""), type="password" if secret else "default", help=help_text)

    with st.form("settings_form"):
        st.subheader("Execução local")
        port = st.number_input("Porta Streamlit", 1, 65535, int(settings.get("port", 3030)))
        moneyprinter_path = st.text_input("Pasta MoneyPrinterTurbo", settings.get("moneyprinter_path", ""))
        youtube_api_key = st.text_input("YouTube Data API key", settings.get("youtube_api_key", ""), type="password")

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
            llm_fields = [
                ("Moonshot / Kimi", "moonshot", True), ("Shengsuan Cloud", "shengsuanyun", True), ("OpenAI", "openai", True),
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

        with st.expander("Voz, TTS e música"):
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

        with st.expander("TikTok for Developers"):
            st.caption("Apenas as credenciais da aplicação ficam nesta UI. Redirect URI, scopes, autorização e tokens são geridos no TikTok for Developers Playground.")
            tiktok_client_key = text_setting("TikTok Client ID", "tiktok_client_key", secret=True)
            tiktok_client_secret = text_setting("TikTok Client Secret", "tiktok_client_secret", secret=True)

        with st.expander("Publicação através do Upload-Post"):
            upload_post_enabled = st.checkbox("Activar Upload-Post", bool(settings.get("upload_post_enabled", False)))
            upload_post_api_key = text_setting("Upload-Post API key", "upload_post_api_key", secret=True)
            upload_post_username = text_setting("Upload-Post username", "upload_post_username")
            upload_post_platforms = text_setting("Plataformas Upload-Post", "upload_post_platforms")
            upload_post_auto_upload = st.checkbox("Publicar automaticamente após gerar", bool(settings.get("upload_post_auto_upload", False)))

        if st.form_submit_button("Guardar configurações do MoneyPrinterTurbo", type="primary"):
            settings.update({
                "port": port, "moneyprinter_path": moneyprinter_path, "youtube_api_key": youtube_api_key,
                "log_level": log_level, "listen_host": listen_host, "listen_port": listen_port, "video_source": video_source,
                "endpoint": endpoint, "proxy_http": proxy_http, "proxy_https": proxy_https, "match_materials_to_script": match_materials_to_script,
                "llm_provider": llm_provider, "azure_speech_key": azure_speech_key, "azure_speech_region": azure_speech_region,
                "siliconflow_tts_api_key": siliconflow_tts_api_key, "minimax_tts_api_key": minimax_tts_api_key,
                "minimax_tts_base_url": minimax_tts_base_url, "minimax_tts_model_id": minimax_tts_model_id, "minimax_tts_voice_id": minimax_tts_voice_id,
                "elevenlabs_api_key": elevenlabs_api_key, "elevenlabs_model_id": elevenlabs_model_id,
                "pexels_api_keys": pexels_api_keys, "pixabay_api_keys": pixabay_api_keys, "coverr_api_keys": coverr_api_keys, "twelvelabs_api_keys": twelvelabs_api_keys,
                "chatterbox_base_url": chatterbox_base_url, "chatterbox_api_key": chatterbox_api_key, "chatterbox_model_id": chatterbox_model_id,
                "sonilo_api_key": sonilo_api_key, "sonilo_base_url": sonilo_base_url, "subtitle_provider": subtitle_provider,
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
                    st.success("Configurações guardadas localmente. Indique uma pasta válida do MoneyPrinterTurbo para sincronizar config.toml.")
            except Exception as exc:
                st.warning(f"Configurações locais guardadas, mas não foi possível sincronizar config.toml: {exc}")


def render_metadata_cleaner():
    st.title("Limpador de metadado")
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
    cols = st.columns(len(STAGES))
    for col, stage in zip(cols, STAGES):
        with col:
            card(stage.title(), len(queues.get(stage, [])), "fila")


def main():
    pages = [
        ("Dashboard", ":material/home:", "Início"),
        ("Pipeline", ":material/account_tree:", "Pipeline"),
        ("Blueprints", ":material/library_books:", "Blueprints"),
        ("Canais", ":material/ondemand_video:", "Canais"),
        ("Novo vídeo", ":material/add_circle:", "Novo vídeo"),
        ("Vídeos", ":material/video_library:", "Vídeos"),
        ("Upload", ":material/cloud_upload:", "Upload"),
        ("Limpador de metadado", ":material/edit_note:", "Limpador de metadado"),
        ("Configurações", ":material/settings:", "Configurações"),
    ]
    current_page = st.session_state.get("page", "Dashboard")
    with st.sidebar:
        st.title("MoneyPrinterTurbo")
        st.caption("Navegação")
        for target, icon, label in pages:
            if st.button(label, key=f"nav_{target}", icon=icon, use_container_width=True, type="primary" if current_page == target else "secondary"):
                st.session_state["page"] = target
                st.rerun()
    renderers = {
        "Dashboard": render_dashboard,
        "Pipeline": render_pipeline,
        "Blueprints": render_blueprints,
        "Canais": render_channels,
        "Novo vídeo": render_new_video,
        "Vídeos": render_videos,
        "Upload": render_upload,
        "Limpador de metadado": render_metadata_cleaner,
        "Configurações": render_settings,
    }
    renderers.get(current_page, render_dashboard)()


if __name__ == "__main__":
    main()
