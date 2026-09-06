from __future__ import annotations

import re
import uuid
from datetime import datetime, timezone
from html import escape
from pathlib import Path
from typing import Any, Callable, Mapping

import streamlit as st

from .storage import STORAGE, read_json, write_json

ANALYSES_FILENAME = "facebook_pages_growth_analyses.json"
ANALYSES_DIR = STORAGE / "growth" / "facebook_pages"
AGENT_METRICS = (
    "Demanda validada", "Qualidade da thumbnail", "Qualidade do título",
    "Hook — retenção inicial", "Ritmo e edição", "Origem Recommended", "Conversão em seguidores", "Cadência",
)


def analysis_code(now: datetime | None = None) -> str:
    moment = now or datetime.now(timezone.utc)
    return f"GFA-{moment.strftime('%Y%m%d-%H%M%S')}-{uuid.uuid4().hex[:6].upper()}"


def _score_color(score: int | float) -> str:
    return "red" if score <= 30 else "yellow" if score < 70 else "green"


def _safe_int(value: Any, default: int = 0) -> int:
    try:
        return int(value or default)
    except (TypeError, ValueError):
        return default


def _public_posts(page: Mapping[str, Any], limit: int = 5) -> list[dict[str, Any]]:
    posts = page.get("posts") or page.get("recent_posts") or page.get("public_posts") or []
    if isinstance(posts, list):
        return [dict(item) for item in posts[:limit] if isinstance(item, Mapping)]
    return []


def _pages() -> list[dict[str, Any]]:
    settings = read_json("settings.json", {})
    candidates: list[Any] = []
    for key in ("facebook_pages", "facebook_page_accounts", "meta_pages"):
        value = settings.get(key, []) if isinstance(settings, Mapping) else []
        candidates.extend(value if isinstance(value, list) else [value] if isinstance(value, Mapping) else [])
    for channel in read_json("channels.json", []):
        if isinstance(channel, dict) and str(channel.get("platform") or "").casefold() in {"facebook", "facebook_pages", "facebook page"}:
            candidates.append(channel)
    unique: dict[str, dict[str, Any]] = {}
    for item in candidates:
        if not isinstance(item, Mapping):
            continue
        page = dict(item)
        key = str(page.get("id") or page.get("page_id") or page.get("name") or page.get("url") or "").strip()
        if key:
            unique[key] = page
    return [item for item in unique.values() if item.get("active", True)]


def _report_markdown(record: Mapping[str, Any]) -> str:
    lines = [f"# FACEBOOK GROWTH AUDIT REPORT: {record.get('page_name', 'Página')}", "", f"- Código: `{record.get('code')}`", "- Plataforma: Facebook Pages", f"- Data: {record.get('created_at')}", f"- Nota geral: **{record.get('overall_score', 0)}/100**", "", "## Projecção financeira e contexto", "", "A auditoria pública não expõe CPM, minutos de visualização, CTR ou dados de monetização. O relatório não inventa estes valores. A elegibilidade deve confirmar 10.000 seguidores, 600.000 minutos de watch time em 60 dias, conteúdo original e conta em país elegível.", "", "## Diagnóstico", "", "| Pilar | Nota | Métrica observada | Origem | Diagnóstico |", "|---|---:|---|---|---|"]
    for metric in record.get("metrics", []):
        lines.append(f"| **{metric['label']}** | {metric['score']}/100 | {metric['value']} | {metric.get('source', 'unknown')} | {metric['diagnosis']} |")
    lines += ["", "## Últimas publicações públicas", "", "| Título | Visualizações | Reacções | Comentários | Partilhas |", "|---|---:|---:|---:|---:|"]
    for post in record.get("posts", []):
        lines.append(f"| {str(post.get('title') or post.get('message') or 'Sem título').replace('|', '/')} | {_safe_int(post.get('view_count') or post.get('views')):,} | {_safe_int(post.get('like_count') or post.get('reactions')):,} | {_safe_int(post.get('comment_count') or post.get('comments')):,} | {_safe_int(post.get('share_count') or post.get('shares')):,} |")
    lines += ["", "## Roadmap accionável", "", "1. **REMAKE THUMBNAILS**: aumentar contraste, usar sujeito claro, emoção forte e no máximo três palavras legíveis no telemóvel.", "2. **REWRITE TITLES**: começar pela keyword principal e combinar curiosidade, clareza e urgência sem prometer algo que o vídeo não entrega.", "3. **EDIT HOOK**: abrir com o resultado ou estatística forte; adicionar pattern interrupt a cada 3–5 segundos e CTA visual a 40% do vídeo.", "", "## Limitações", "", "CTR, retenção de 3/15 segundos, tráfego Recommended, alcance, minutos de watch time, seguidores ganhos e monetização exigem dados autorizados do Facebook Page Insights/Creator Studio."]
    return "\n".join(lines) + "\n"


def run_audit(page: Mapping[str, Any], settings: Mapping[str, Any] | None = None, *, progress: Callable[[str], None] | None = None) -> dict[str, Any]:
    del settings
    code = analysis_code()
    root = ANALYSES_DIR / code
    root.mkdir(parents=True, exist_ok=True)
    notify = progress or (lambda _message: None)
    notify("A preparar a auditoria pública da Facebook Page…")
    posts = _public_posts(page, 5)
    views = sum(_safe_int(item.get("view_count") or item.get("views")) for item in posts)
    reactions = sum(_safe_int(item.get("like_count") or item.get("reactions")) for item in posts)
    comments = sum(_safe_int(item.get("comment_count") or item.get("comments")) for item in posts)
    shares = sum(_safe_int(item.get("share_count") or item.get("shares")) for item in posts)
    engagement = ((reactions + comments + shares) / views * 100) if views else None
    followers = _safe_int(page.get("followers") or page.get("follower_count") or page.get("fan_count")) or None
    conversion = (followers / views * 100) if followers and views else None
    cadence = 70 if len(posts) >= 3 else 40 if posts else 0
    public_value = f"{len(posts)} publicações públicas" if posts else "Sem publicações públicas estruturadas"
    metrics = [
        {"label": "Demanda validada", "score": 50 if posts else 0, "value": public_value, "source": "public", "diagnosis": "Concorrência, pesquisa e Recommended exigem Page Insights."},
        {"label": "Qualidade da thumbnail", "score": 50, "value": "CTR indisponível", "source": "unavailable", "diagnosis": "CTR privado; meta do agente: acima de 6%."},
        {"label": "Qualidade do título", "score": 50, "value": "Retenção cruzada indisponível", "source": "unavailable", "diagnosis": "Avaliar os 3 C's: Curiosity, Clarity e Urgency."},
        {"label": "Hook — retenção inicial", "score": 50, "value": "Retenção de 3/15s indisponível", "source": "unavailable", "diagnosis": "Creator Studio é necessário para a retenção absoluta."},
        {"label": "Ritmo e edição", "score": 50, "value": "Quedas de retenção indisponíveis", "source": "unavailable", "diagnosis": "Aplicar pattern interrupt a cada 3–5 segundos."},
        {"label": "Origem Recommended", "score": 50, "value": "Fontes de tráfego indisponíveis", "source": "unavailable", "diagnosis": "Meta: 40–70% Recommended/Suggestions."},
        {"label": "Conversão em seguidores", "score": 50 if conversion is None else (85 if conversion > 1.5 else 60 if conversion >= .5 else 30), "value": f"{conversion:.2f}% proxy" if conversion is not None else "Seguidores ganhos por publicação indisponíveis", "source": "estimated" if conversion is not None else "unavailable", "diagnosis": "Meta: acima de 1,5%; proxy não substitui seguidores ganhos."},
        {"label": "Cadência", "score": cadence, "value": f"{len(posts)} publicações na amostra", "source": "public", "diagnosis": "Meta do agente: 3–5 publicações/Reels por semana."},
    ]
    overall = round(sum(item["score"] for item in metrics) / len(metrics))
    record = {"code": code, "page_id": str(page.get("page_id") or page.get("id") or ""), "page_name": str(page.get("name") or page.get("page_name") or "Facebook Page"), "platform": "Facebook Pages", "created_at": datetime.now(timezone.utc).isoformat(), "overall_score": overall, "score_color": _score_color(overall), "metrics": metrics, "posts": posts, "sample_views": views, "engagement_rate": engagement, "monetization_status": "A verificar — confirmar requisitos no Creator Studio", "status": "completed"}
    report_path = root / f"{code}.md"
    report_path.write_text(_report_markdown(record), encoding="utf-8")
    record["report_path"] = str(report_path)
    analyses = read_json(ANALYSES_FILENAME, [])
    if not isinstance(analyses, list): analyses = []
    analyses.append(record)
    write_json(ANALYSES_FILENAME, analyses[-100:])
    return record


def _card(title: str, score: Any, featured: bool, rows: list[tuple[str, str, str, str, str]]) -> str:
    numeric = _safe_int(score)
    colour = "#ef4444" if numeric <= 30 else "#f59e0b" if numeric < 70 else "#22c55e"
    row_html = "".join(f'<tr><td>{escape(label)}</td><td><b>{escape(value)}</b></td><td>{escape(target)}</td><td style="color:{status_colour};font-weight:700;">● {escape(status)}</td></tr>' for label, value, target, status, status_colour in rows)
    return f'<div style="min-height:{"350px" if featured else "280px"};border:1px solid #2b3b52;border-radius:14px;padding:16px;background:linear-gradient(145deg,#111c2b,#0b121c);box-shadow:0 8px 22px rgba(0,0,0,.16);"><div style="font-size:{"19px" if featured else "16px"};font-weight:750;color:#f8fafc;margin-top:8px;">{escape(title)}</div><div style="display:flex;align-items:baseline;gap:5px;margin:8px 0 10px;"><span style="font-size:{"38px" if featured else "30px"};font-weight:850;color:{colour};">{numeric}</span><span style="font-size:13px;color:#94a3b8;">/100</span></div><div style="overflow-x:auto;"><table style="width:100%;border-collapse:collapse;font-size:11px;color:#cbd5e1;"><thead><tr><th style="text-align:left;padding:5px 3px;border-bottom:1px solid #334155;">KPI</th><th style="text-align:left;padding:5px 3px;border-bottom:1px solid #334155;">Valor</th><th style="text-align:left;padding:5px 3px;border-bottom:1px solid #334155;">Meta</th><th style="text-align:left;padding:5px 3px;border-bottom:1px solid #334155;">Status</th></tr></thead><tbody>{row_html}</tbody></table></div></div>'


def render_growth_facebook_pages() -> None:
    st.title("Analista Facebook Pages")
    st.caption("Auditoria de Facebook Pages baseada nos 3 pilares críticos e nas métricas secundárias do agente Growth.")
    pages = _pages()
    if not pages:
        st.info("Configure pelo menos uma Facebook Page em Configuração API ou no registo de páginas para iniciar a análise.")
        return
    selector_col, action_col = st.columns([1.05, 1.15], gap="small")
    with selector_col:
        selected = st.selectbox("Página a analisar", pages, format_func=lambda item: str(item.get("name") or item.get("page_name") or "Página sem nome"), key="growth_facebook_page")
    with action_col:
        st.write("")
        analyse_clicked = st.button("ANALISAR PÁGINA", type="primary", use_container_width=True, key="growth_facebook_analyse")
    st.markdown("**Estado das APIs de Growth**")
    api_cols = st.columns(2, gap="small")
    with api_cols[0]:
        st.caption("Dados públicos e registos locais")
        st.markdown('<span style="color:#22c55e;font-weight:700;">● Disponível quando houver publicações guardadas</span>', unsafe_allow_html=True)
    with api_cols[1]:
        st.caption("Facebook Page Insights / Creator Studio")
        st.markdown('<span style="color:#94a3b8;font-weight:700;">● Requer dados privados autorizados</span>', unsafe_allow_html=True)
    if analyse_clicked:
        with st.status("A preparar a análise…", expanded=True) as status:
            try:
                record = run_audit(selected, read_json("settings.json", {}), progress=st.write)
                status.update(label="Análise concluída", state="complete")
            except Exception as exc:
                status.update(label="Análise falhou", state="error")
                st.error(str(exc)[:500])
    records = list_analyses()
    selected_record = next((item for item in reversed(records) if str(item.get("page_id")) == str(selected.get("page_id") or selected.get("id"))), None)
    metric_by_label = {str(item.get("label")): item for item in (selected_record.get("metrics", []) if selected_record else [])}
    metrics = selected_record.get("metrics", []) if selected_record else [{"label": label, "score": 0, "value": "Aguardando análise", "source": "unknown"} for label in AGENT_METRICS]
    score = selected_record.get("overall_score") if selected_record else None
    colour = "#64748b" if score is None else "#ef4444" if score <= 30 else "#f59e0b" if score < 70 else "#22c55e"
    summary_col, download_col = st.columns([3.25, 1], gap="large")
    with summary_col:
        st.markdown(f'<div style="border:1px solid #263447;border-radius:12px;padding:18px;margin:12px 0 20px;background:#101722;display:flex;align-items:center;justify-content:space-between;min-height:76px;"><div><div style="font-size:13px;color:#94a3b8;text-transform:uppercase;letter-spacing:.08em;">Nota geral da página</div><div style="font-size:18px;font-weight:700;margin-top:5px;">{escape(str(selected.get("name") or selected.get("page_name") or "Facebook Page"))}</div></div><div style="font-size:42px;font-weight:800;color:{colour};line-height:1;">{score if score is not None else "—"}<span style="font-size:16px;color:#94a3b8;">{"/100" if score is not None else ""}</span></div></div>', unsafe_allow_html=True)
    with download_col:
        st.write("")
        path = Path(str(selected_record.get("report_path") or "")) if selected_record else Path()
        if path.is_file():
            st.download_button("BAIXAR ANALISE COMPLETA", path.read_bytes(), file_name=path.name, mime="text/markdown", use_container_width=True, key=f"facebook_download_{selected_record['code']}")
        else:
            st.button("BAIXAR ANALISE COMPLETA", disabled=True, use_container_width=True, key="facebook_download_disabled")
    st.subheader("Dashboard de Growth")
    st.caption("3 pilares críticos em destaque e camadas operacionais abaixo. Vermelho: 0–30 · Amarelo: 31–69 · Verde: 70–100.")
    def item(label: str, target: str, available: bool = False) -> tuple[str, str, str, str, str]:
        metric = metric_by_label.get(label, {})
        return (label, str(metric.get("value", "Aguardando análise")), target, "Meta atingida" if available else "A verificar", "#22c55e" if available else "#94a3b8")
    cards = [("Demanda validada", True, [item("Demanda validada", "> 500k concorrência", True)]), ("Qualidade da thumbnail", True, [item("Qualidade da thumbnail", "> 6% CTR")]), ("Qualidade do título", True, [item("Qualidade do título", "3 C's")]), ("Hook — retenção inicial", False, [item("Hook — retenção inicial", "> 50% aos 3s")]), ("Ritmo e edição", False, [item("Ritmo e edição", "Interrupt 3–5s")]), ("Origem Recommended", False, [item("Origem Recommended", "40–70%")]), ("Conversão em seguidores", False, [item("Conversão em seguidores", "> 1.5%")]), ("Cadência", False, [item("Cadência", "3–5/semana")])]
    st.markdown('<div style="display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:14px;margin:14px 0 18px;">' + "".join(_card(title, metric_by_label.get(title, {}).get("score", 0), featured, rows) for title, featured, rows in cards[:3]) + '</div>', unsafe_allow_html=True)
    st.markdown('<div style="display:grid;grid-template-columns:repeat(5,minmax(0,1fr));gap:12px;margin:0 0 18px;">' + "".join(_card(title, metric_by_label.get(title, {}).get("score", 0), featured, rows) for title, featured, rows in cards[3:]) + '</div>', unsafe_allow_html=True)
    st.caption("Legenda: ● Verde = meta atingida · ● Amarelo = atenção · ● Vermelho = crítico · Cinzento = dado não disponível na fonte autorizada.")
    st.divider()
    history_tab, dashboard_tab = st.tabs(["Últimas análises", "Leitura estratégica"])
    with dashboard_tab:
        st.write("Priorize Thumbnail, Título e Hook. CTR, retenção, tráfego Recommended, minutos de watch time e monetização ficam pendentes do Page Insights/Creator Studio.")
    with history_tab:
        if not records:
            st.info("Ainda não existem análises guardadas.")
        for record in reversed(records[-20:]):
            row = st.columns([2, 1, 2.2, 1.2, 1, 1.4])
            row[0].write(f"**{record.get('page_name', 'Facebook Page')}**")
            row[1].write("Facebook Pages")
            row[2].caption(str(record.get("code", "")))
            row[3].caption(str(record.get("created_at", "")).replace("T", " ")[:19])
            row[4].write(f"{record.get('overall_score', '—')}/100")
            path = Path(str(record.get("report_path") or ""))
            if path.is_file():
                row[5].download_button("Análise", path.read_bytes(), file_name=path.name, mime="text/markdown", key=f"facebook_history_{record.get('code')}")


def list_analyses() -> list[dict[str, Any]]:
    value = read_json(ANALYSES_FILENAME, [])
    return [dict(item) for item in value if isinstance(item, Mapping)] if isinstance(value, list) else []


__all__ = ["AGENT_METRICS", "ANALYSES_DIR", "analysis_code", "list_analyses", "run_audit", "render_growth_facebook_pages"]
