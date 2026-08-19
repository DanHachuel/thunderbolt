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
from integrations.platforms import TikTokAdapter, YouTubeAdapter
from integrations.local_runtime import LocalRuntime

ensure_storage()
st.set_page_config(page_title="Content-Hermes", page_icon="H", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
<style>
:root { --accent:#35a7ff; --bg:#0b1118; --card:#121b26; }
[data-testid="stAppViewContainer"] { background: radial-gradient(circle at top right, #13283b 0, #0b1118 42%); }
[data-testid="stSidebar"] { background:#091018; border-right:1px solid #1d3448; }
.hermes-card { padding: 1rem 1.1rem; border:1px solid #20384d; border-radius:14px; background:rgba(18,27,38,.92); min-height:110px; }
.hermes-label { color:#8ba6bb; font-size:.8rem; text-transform:uppercase; letter-spacing:.07em; }
.hermes-value { color:#f4f8fb; font-size:1.8rem; font-weight:700; margin-top:.3rem; }
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
    st.markdown(f'<div class="hermes-card"><div class="hermes-label">{label}</div><div class="hermes-value">{value}</div><div class="small-muted">{note}</div></div>', unsafe_allow_html=True)


def channel_options() -> list[dict]:
    return [c for c in read_json("channels.json", []) if c.get("active", True)]


def render_dashboard():
    st.title("Content-Hermes")
    st.caption("Central de operação local para a pipeline de conteúdo faceless")
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
    st.title("Configurações e chaves API")
    settings = read_json("settings.json", {})
    with st.form("settings_form"):
        st.subheader("Execução local")
        port = st.number_input("Porta Streamlit", 1, 65535, int(settings.get("port", 3030)))
        hermes_url = st.text_input("URL Hermes", settings.get("hermes_url", "http://localhost:8765"))
        moneyprinter_path = st.text_input("Pasta MoneyPrinterTurbo", settings.get("moneyprinter_path", ""))
        st.subheader("YouTube")
        youtube_api_key = st.text_input("YouTube Data API key", settings.get("youtube_api_key", ""), type="password")
        st.subheader("TikTok Content Posting API")
        tiktok_client_key = st.text_input("Client Key", settings.get("tiktok_client_key", ""), type="password")
        tiktok_client_secret = st.text_input("Client Secret", settings.get("tiktok_client_secret", ""), type="password")
        tiktok_redirect_uri = st.text_input("Redirect URI", settings.get("tiktok_redirect_uri", "http://localhost:3030/oauth/tiktok/callback"))
        tiktok_scopes = st.text_input("Scopes", settings.get("tiktok_scopes", "user.info.basic,video.publish,video.upload"))
        tiktok_access_token = st.text_input("Access token TikTok (opcional)", settings.get("tiktok_access_token", ""), type="password", help="Pode ser substituído pela variável TIKTOK_ACCESS_TOKEN.")
        if st.form_submit_button("Guardar configurações", type="primary"):
            settings.update({"port": port, "hermes_url": hermes_url, "moneyprinter_path": moneyprinter_path, "youtube_api_key": youtube_api_key, "tiktok_client_key": tiktok_client_key, "tiktok_client_secret": tiktok_client_secret, "tiktok_redirect_uri": tiktok_redirect_uri, "tiktok_scopes": tiktok_scopes, "tiktok_access_token": tiktok_access_token})
            write_json("settings.json", settings)
            st.success("Configurações guardadas localmente.")


def render_pipeline():
    st.title("Pipeline")
    st.caption("Estado das filas locais e dependências da cascata")
    queues = read_json("queues.json", {})
    cols = st.columns(len(STAGES))
    for col, stage in zip(cols, STAGES):
        with col:
            card(stage.title(), len(queues.get(stage, [])), "fila")


def main():
    pages = ["Dashboard", "Pipeline", "Blueprints", "Canais", "Novo vídeo", "Vídeos", "Upload", "Configurações"]
    with st.sidebar:
        st.title("Content-Hermes")
        page = st.radio("Navegação", pages, index=pages.index(st.session_state.get("page", "Dashboard")))
        st.session_state["page"] = page
        st.caption("Storage JSON local")
        settings = read_json("settings.json", {})
        runtime = LocalRuntime(settings).status()
        st.caption(f"Porta alvo: {settings.get('port', 3030)}")
        st.caption(f"Modo: {runtime['mode']}")
        st.caption(f"Hermes: {'online' if runtime['hermes'] else 'indisponível'}")
        st.caption(f"MoneyPrinterTurbo: {'encontrado' if runtime['moneyprinter'] else 'não configurado'}")
    {"Dashboard": render_dashboard, "Pipeline": render_pipeline, "Blueprints": render_blueprints, "Canais": render_channels, "Novo vídeo": render_new_video, "Vídeos": render_videos, "Upload": render_upload, "Configurações": render_settings}[page]()


if __name__ == "__main__":
    main()
