from __future__ import annotations

import json
import re
import uuid
from datetime import datetime, timezone
from html import escape
from pathlib import Path
from typing import Any, Callable, Mapping

import streamlit as st

from integrations.instagram_public import fetch_public_instagram_profile
from .storage import STORAGE, read_json, write_json

ANALYSES_FILENAME = "instagram_growth_analyses.json"
ANALYSES_DIR = STORAGE / "growth" / "instagram"
AGENT_METRICS = (
    "Demanda e potencial de viralização", "Qualidade visual — stop the scroll", "Hook e storytelling",
    "Ritmo e edição", "Tráfego Explore/Reels", "Engajamento e saves", "Conversão em seguidores", "Mix de formatos", "Cadência",
)


def analysis_code(now: datetime | None = None) -> str:
    moment = now or datetime.now(timezone.utc)
    return f"GIA-{moment.strftime('%Y%m%d-%H%M%S')}-{uuid.uuid4().hex[:6].upper()}"


def _score_color(score: int | float) -> str:
    return "red" if score <= 30 else "yellow" if score < 70 else "green"


def _safe_int(value: Any, default: int = 0) -> int:
    try:
        return int(value or default)
    except (TypeError, ValueError):
        return default


def _number(value: Any) -> float | None:
    try:
        return float(value) if value not in (None, "", "—") else None
    except (TypeError, ValueError):
        return None


def _public_videos(source: str, limit: int = 5) -> list[dict[str, Any]]:
    try:
        import yt_dlp
    except ImportError as exc:
        raise RuntimeError("yt-dlp não está instalado. Instale as dependências do Thunderbolt.") from exc
    options = {"quiet": True, "skip_download": True, "extract_flat": True, "playlistend": limit, "noplaylist": False}
    with yt_dlp.YoutubeDL(options) as downloader:
        info = downloader.extract_info(source, download=False)
    entries = info.get("entries") if isinstance(info, Mapping) else []
    videos: list[dict[str, Any]] = []
    for item in entries or []:
        if not isinstance(item, Mapping):
            continue
        video_id = str(item.get("id") or item.get("webpage_url") or "").strip()
        if not video_id:
            continue
        videos.append({
            "id": video_id,
            "title": str(item.get("title") or "Sem título").strip(),
            "url": str(item.get("webpage_url") or f"https://www.instagram.com/@{source.lstrip('@').split('/')[-1]}/video/{video_id}"),
            "view_count": _safe_int(item.get("view_count")),
            "like_count": _safe_int(item.get("like_count")),
            "comment_count": _safe_int(item.get("comment_count")),
            "repost_count": _safe_int(item.get("repost_count") or item.get("share_count")),
            "save_count": _safe_int(item.get("save_count")),
            "duration": _safe_int(item.get("duration")),
            "upload_date": str(item.get("upload_date") or ""),
        })
    return videos[:limit]


def _score_from_rate(rate: float | None, thresholds: tuple[float, float]) -> int:
    if rate is None:
        return 50
    low, high = thresholds
    if rate < low:
        return 30
    if rate < high:
        return 60
    return 85


def _report_markdown(record: Mapping[str, Any]) -> str:
    profile = record.get("profile") or {}
    lines = [
        f"# INSTAGRAM CHANNEL AUDIT REPORT: {record.get('channel_name', 'Canal')}", "",
        f"- Código: `{record.get('code')}`", "- Plataforma: Instagram",
        f"- Data: {record.get('created_at')}", f"- Nota geral: **{record.get('overall_score', 0)}/100**", "",
        "## Resumo executivo", "",
        f"- Elegível para ferramentas de monetização: **{record.get('monetization_status', 'A verificar')}**",
        f"- Seguidores públicos: **{profile.get('subscriber_count', '—')}**",
        f"- Visualizações públicas na amostra: **{record.get('sample_views', '—')}**", "",
        "## Diagnóstico", "", "| Pilar | Nota | Métrica observada | Origem | Diagnóstico |", "|---|---:|---|---|---|",
    ]
    for metric in record.get("metrics", []):
        lines.append(f"| **{metric['label']}** | {metric['score']}/100 | {metric['value']} | {metric.get('source', 'unknown')} | {metric['diagnosis']} |")
    lines += ["", "## Últimos vídeos públicos", "", "| Título | Visualizações | Gostos | Comentários | Duração |", "|---|---:|---:|---:|---:|"]
    for video in record.get("videos", []):
        lines.append(f"| {str(video.get('title', '')).replace('|', '/')} | {video.get('view_count', 0):,} | {video.get('like_count', 0):,} | {video.get('comment_count', 0):,} | {video.get('duration', 0)}s |")
    lines += ["", "## Roadmap accionável", "", "1. **REBUILD THE HOOK**: nos primeiros 3 segundos, começar com resultado, estatística, pergunta directa ou pattern interrupt; sem logo ou introdução lenta.", "2. **OPTIMIZE RETENTION**: renovar visual/texto a cada 3–5 segundos, inserir pattern interrupt a cada 5–8 segundos e evitar frames estáticos por mais de 3 segundos.", "3. **PUBLISH CONSISTENTLY**: manter 3–5 Reels por semana, combinando Reels para alcance, Carrosséis para saves e Stories para relacionamento.", "", "## Limitações", "", "Retenção de 3 segundos, skip rate, conclusão, alcance, impressões, fontes Explore/Reels, saves, RPM e seguidores ganhos exigem dados autorizados do Instagram Insights. Estes valores não são inventados a partir de uma página pública."]
    return "\n".join(lines) + "\n"


def run_audit(channel: Mapping[str, Any], settings: Mapping[str, Any] | None = None, *, progress: Callable[[str], None] | None = None) -> dict[str, Any]:
    del settings
    code = analysis_code()
    root = ANALYSES_DIR / code
    root.mkdir(parents=True, exist_ok=True)
    notify = progress or (lambda _message: None)
    source = str(channel.get("url") or channel.get("handle") or "").strip()
    if not source:
        raise RuntimeError("A conta seleccionada não tem URL pública ou handle Instagram.")
    notify("A consultar o perfil público Instagram…")
    profile_result = fetch_public_instagram_profile(source)
    profile = dict(profile_result.data or {})
    if not profile_result.ok and not profile:
        raise RuntimeError(profile_result.message)
    notify("A recolher as últimas 5 publicações públicas…")
    try:
        videos = _public_videos(source, 5)
    except Exception as exc:
        videos = []
        profile["video_lookup_error"] = str(exc)[:240]
    views = sum(_safe_int(item.get("view_count")) for item in videos)
    likes = sum(_safe_int(item.get("like_count")) for item in videos)
    comments = sum(_safe_int(item.get("comment_count")) for item in videos)
    shares = sum(_safe_int(item.get("repost_count")) for item in videos)
    saves = sum(_safe_int(item.get("save_count")) for item in videos)
    engagement = ((likes + comments + shares + saves) / views * 100) if views else None
    save_rate = (saves / views * 100) if views else None
    share_rate = (shares / views * 100) if views else None
    avg_views = views / len(videos) if videos else None
    durations = [_safe_int(item.get("duration")) for item in videos if _safe_int(item.get("duration")) > 0]
    avg_duration = sum(durations) / len(durations) if durations else None
    followers = _number(profile.get("subscriber_count"))
    conversion = (followers / views * 100) if followers is not None and views else None
    cadence_score = 70 if len(videos) >= 3 else 40 if videos else 0
    metrics = [
        {"label": "Demanda e potencial de viralização", "score": 50 if videos else 0, "value": f"{len(videos)} publicações públicas", "source": "public", "diagnosis": "Alcance, impressões e pesquisa exigem Instagram Insights."},
        {"label": "Qualidade visual — stop the scroll", "score": 50, "value": "Retenção inicial indisponível", "source": "unavailable", "diagnosis": "Skip rate e retenção de 3 segundos exigem Instagram Insights."},
        {"label": "Hook e storytelling", "score": 50, "value": f"Duração média {avg_duration:.0f}s" if avg_duration else "Curva de retenção indisponível", "source": "public" if avg_duration else "unavailable", "diagnosis": "A duração pública não substitui watch time ou conclusão."},
        {"label": "Ritmo e edição", "score": 50, "value": "Quedas de retenção indisponíveis", "source": "unavailable", "diagnosis": "Pacing depende da curva de retenção."},
        {"label": "Tráfego Explore/Reels", "score": 50, "value": "Origem Explore/Reels indisponível", "source": "unavailable", "diagnosis": "Fontes Explore, Reels, Search, Profile e External exigem Insights."},
        {"label": "Engajamento e saves", "score": _score_from_rate(engagement, (2, 3)), "value": f"{engagement:.2f}% na amostra" if engagement is not None else "Sem interacções públicas", "source": "public", "diagnosis": f"Saves: {save_rate:.2f}% · Shares: {share_rate:.2f}%" if save_rate is not None and share_rate is not None else "Interacções públicas indisponíveis."},
        {"label": "Conversão em seguidores", "score": _score_from_rate(conversion, (0.5, 1.0)), "value": f"{conversion:.2f}% proxy" if conversion is not None else "Seguidores ganhos indisponíveis", "source": "estimated" if conversion is not None else "unavailable", "diagnosis": "Proxy não equivale a seguidores ganhos por publicação."},
        {"label": "Mix de formatos", "score": 50, "value": "Reels/Carrosséis indisponíveis", "source": "unavailable", "diagnosis": "A distribuição de formatos requer o catálogo autorizado da conta."},
        {"label": "Cadência", "score": cadence_score, "value": f"{len(videos)} publicações na amostra", "source": "public", "diagnosis": "Meta do agente: 3–5 Reels por semana, com consistência."},
    ]
    overall = round(sum(item["score"] for item in metrics) / len(metrics)) if metrics else 0
    monetization = "A verificar — faltam dados privados" if followers is None or followers < 10000 else "Possível — confirmar conta profissional, pública e estado elegível"
    record = {"code": code, "channel_id": str(channel.get("id") or ""), "channel_name": str(channel.get("name") or profile.get("name") or "Conta Instagram"), "platform": "Instagram", "created_at": datetime.now(timezone.utc).isoformat(), "overall_score": overall, "score_color": _score_color(overall), "metrics": metrics, "videos": videos, "profile": profile, "sample_views": views, "engagement_rate": engagement, "save_rate": save_rate, "share_rate": share_rate, "monetization_status": monetization, "status": "completed"}
    report_path = root / f"{code}.md"
    report_path.write_text(_report_markdown(record), encoding="utf-8")
    record["report_path"] = str(report_path)
    analyses = read_json(ANALYSES_FILENAME, [])
    if not isinstance(analyses, list): analyses = []
    analyses.append(record)
    write_json(ANALYSES_FILENAME, analyses[-100:])
    return record


def list_analyses() -> list[dict[str, Any]]:
    value = read_json(ANALYSES_FILENAME, [])
    return [dict(item) for item in value if isinstance(item, Mapping)] if isinstance(value, list) else []


def _card(title: str, score: Any, featured: bool, rows: list[tuple[str, str, str, str]]) -> str:
    score_int = _safe_int(score)
    row_html = "".join(f'<tr><td>{escape(label)}</td><td><b>{escape(value)}</b></td><td>{escape(target)}</td><td style="color:{colour};font-weight:700;">● {escape(status)}</td></tr>' for label, value, target, status, colour in rows)
    return f'<div style="min-height:{"350px" if featured else "280px"};border:1px solid #2b3b52;border-radius:14px;padding:16px;background:linear-gradient(145deg,#111c2b,#0b121c);box-shadow:0 8px 22px rgba(0,0,0,.16);"><div style="font-size:{"19px" if featured else "16px"};font-weight:750;color:#f8fafc;margin-top:8px;">{escape(title)}</div><div style="display:flex;align-items:baseline;gap:5px;margin:8px 0 10px;"><span style="font-size:{"38px" if featured else "30px"};font-weight:850;color:{"#ef4444" if score_int <= 30 else "#f59e0b" if score_int < 70 else "#22c55e"};">{score_int}</span><span style="font-size:13px;color:#94a3b8;">/100</span></div><div style="overflow-x:auto;"><table style="width:100%;border-collapse:collapse;font-size:11px;color:#cbd5e1;"><thead><tr><th style="text-align:left;padding:5px 3px;border-bottom:1px solid #334155;">KPI</th><th style="text-align:left;padding:5px 3px;border-bottom:1px solid #334155;">Valor</th><th style="text-align:left;padding:5px 3px;border-bottom:1px solid #334155;">Meta</th><th style="text-align:left;padding:5px 3px;border-bottom:1px solid #334155;">Status</th></tr></thead><tbody>{row_html}</tbody></table></div></div>'


def render_growth_instagram() -> None:
    st.title("Analista Growth Instagram")
    st.caption("Auditoria pública baseada nos 3 pilares críticos e nas métricas secundárias do agente Growth Instagram.")
    channels = [item for item in read_json("channels.json", []) if isinstance(item, dict) and item.get("active", True) and str(item.get("platform") or "").casefold() == "instagram"]
    if not channels:
        st.info("Cadastre pelo menos uma conta Instagram em Canais Instagram para iniciar a análise.")
        return
    selector_col, action_col = st.columns([1.05, 1.15], gap="small")
    with selector_col:
        selected = st.selectbox("Conta a analisar", channels, format_func=lambda item: str(item.get("name") or item.get("handle") or "Conta sem nome"), key="growth_instagram_channel")
    with action_col:
        st.write("")
        analyse_clicked = st.button("ANALISAR CONTA", type="primary", width="stretch", key="growth_instagram_analyse")
    st.markdown("**Estado das APIs de Growth**")
    api_cols = st.columns(2, gap="small")
    with api_cols[0]:
        st.caption("Instagram página pública: perfil e amostra de vídeos")
        st.markdown('<span style="color:#22c55e;font-weight:700;">● Disponível quando a página pública responder</span>', unsafe_allow_html=True)
    with api_cols[1]:
        st.caption("Instagram Studio: retenção, FYP, CTR e conversão")
        st.markdown('<span style="color:#94a3b8;font-weight:700;">● Requer dados privados autorizados</span>', unsafe_allow_html=True)
    if analyse_clicked:
        with st.status("A preparar a análise pública…", expanded=True) as status:
            try:
                record = run_audit(selected, read_json("settings.json", {}), progress=st.write)
                st.session_state["growth_instagram_last_code"] = record["code"]
                status.update(label="Análise concluída", state="complete")
            except Exception as exc:
                status.update(label="Análise falhou", state="error")
                st.error(str(exc)[:500])
    records = list_analyses()
    selected_record = next((item for item in reversed(records) if str(item.get("channel_id")) == str(selected.get("id"))), None)
    metric_by_label = {str(item.get("label")): item for item in (selected_record.get("metrics", []) if selected_record else [])}
    metrics = selected_record.get("metrics", []) if selected_record else [{"label": label, "score": 0, "value": "Aguardando análise", "source": "unknown"} for label in AGENT_METRICS]
    score = selected_record.get("overall_score") if selected_record else None
    score_color = "#64748b" if score is None else ("#ef4444" if score <= 30 else "#f59e0b" if score < 70 else "#22c55e")
    summary_col, download_col = st.columns([3.25, 1], gap="large")
    with summary_col:
        st.markdown(f'<div style="border:1px solid #263447;border-radius:12px;padding:18px;margin:12px 0 20px;background:#101722;display:flex;align-items:center;justify-content:space-between;min-height:76px;"><div><div style="font-size:13px;color:#94a3b8;text-transform:uppercase;letter-spacing:.08em;">Nota geral da conta</div><div style="font-size:18px;font-weight:700;margin-top:5px;">{escape(str(selected.get("name") or selected.get("handle") or "Conta Instagram"))}</div></div><div style="font-size:42px;font-weight:800;color:{score_color};line-height:1;">{score if score is not None else "—"}<span style="font-size:16px;color:#94a3b8;">{("/100" if score is not None else "")}</span></div></div>', unsafe_allow_html=True)
    with download_col:
        st.write("")
        report_path = Path(str(selected_record.get("report_path") or "")) if selected_record else Path()
        if report_path.is_file():
            st.download_button("BAIXAR ANALISE COMPLETA", report_path.read_bytes(), file_name=report_path.name, mime="text/markdown", width="stretch", key=f"instagram_download_{selected_record['code']}")
        else:
            st.button("BAIXAR ANALISE COMPLETA", disabled=True, width="stretch", key="instagram_download_disabled")
    st.subheader("Dashboard de Growth")
    st.caption("3 pilares críticos em destaque e camadas operacionais abaixo. Vermelho: 0–30 · Amarelo: 31–69 · Verde: 70–100.")
    def item(label: str, target: str, available: bool = False) -> tuple[str, str, str, str, str]:
        metric = metric_by_label.get(label, {})
        value = str(metric.get("value", "Aguardando análise"))
        return (label, value, target, "A verificar" if not available else "Meta atingida", "#94a3b8" if not available else "#22c55e")
    cards = [
        ("Demanda e potencial de viralização", True, [item("Demanda e potencial de viralização", "> 60% Explore/Reels", True), ("Alcance", "Dados privados", "Crescente", "A verificar", "#94a3b8")]),
        ("Qualidade visual — stop the scroll", True, [item("Qualidade visual — stop the scroll", "> 70% retenção 3s"), ("Skip rate", "Dados privados", "< 60%", "A verificar", "#94a3b8")]),
        ("Hook e storytelling", True, [item("Hook e storytelling", "> 30% conclusão"), ("Watch time", "Dados privados", "próximo da duração", "A verificar", "#94a3b8")]),
        ("Ritmo e edição", False, [item("Ritmo e edição", "Pattern interrupt 5–8s")]),
        ("Tráfego Explore/Reels", False, [item("Tráfego Explore/Reels", "> 60%")]),
        ("Engajamento e saves", False, [item("Engajamento e saves", "> 3% engagement"), ("Save rate", "Dados privados", "> 2%", "A verificar", "#94a3b8")]),
        ("Conversão em seguidores", False, [item("Conversão em seguidores", "> 1%")]),
        ("Mix de formatos", False, [item("Mix de formatos", "80% Reels")]),
        ("Cadência", False, [item("Cadência", "3–5 Reels/semana")]),
    ]
    st.markdown('<div style="display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:14px;margin:14px 0 18px;">' + "".join(_card(title, metric_by_label.get(title, {}).get("score", 0), featured, rows) for title, featured, rows in cards[:3]) + '</div>', unsafe_allow_html=True)
    st.markdown('<div style="display:grid;grid-template-columns:repeat(5,minmax(0,1fr));gap:12px;margin:0 0 18px;">' + "".join(_card(title, metric_by_label.get(title, {}).get("score", 0), featured, rows) for title, featured, rows in cards[3:]) + '</div>', unsafe_allow_html=True)
    st.caption("Legenda: ● Verde = meta atingida · ● Amarelo = atenção · ● Vermelho = crítico · Cinzento = dado não disponível na fonte autorizada.")
    st.divider()
    history_tab, dashboard_tab = st.tabs(["Últimas análises", "Leitura estratégica"])
    with dashboard_tab:
        st.write("Priorize Hook, retenção e cadência. CTR, FYP, retenção real e seguidores ganhos ficam pendentes de dados autorizados do Instagram Studio.")
    with history_tab:
        if not records:
            st.info("Ainda não existem análises guardadas.")
        for record in reversed(records[-20:]):
            row = st.columns([2, 1, 2.2, 1.2, 1, 1.4])
            row[0].write(f"**{record.get('channel_name', 'Conta Instagram')}**")
            row[1].write("Instagram")
            row[2].caption(str(record.get("code", "")))
            row[3].caption(str(record.get("created_at", "")).replace("T", " ")[:19])
            row[4].write(f"{record.get('overall_score', '—')}/100")
            path = Path(str(record.get("report_path") or ""))
            if path.is_file():
                row[5].download_button("Análise", path.read_bytes(), file_name=path.name, mime="text/markdown", key=f"instagram_history_{record.get('code')}")


__all__ = ["AGENT_METRICS", "ANALYSES_DIR", "analysis_code", "list_analyses", "run_audit", "render_growth_instagram"]
