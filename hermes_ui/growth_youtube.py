from __future__ import annotations

import base64
import json
import re
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Mapping

import requests

from .llm_providers import ensure_llm_provider_cards
from .provider_routing import ProviderRoutingError, route_llm_json
from .storage import STORAGE, read_json, write_json

ANALYSES_FILENAME = "youtube_growth_analyses.json"
ANALYSES_DIR = STORAGE / "growth" / "youtube"
AGENT_METRICS = (
    "Demanda validada", "Qualidade da thumbnail", "Qualidade do título",
    "Hook — retenção inicial", "Ritmo e edição", "Origem do tráfego",
    "Conversão em inscritos", "Cadência de publicação",
)


def analysis_code(now: datetime | None = None) -> str:
    moment = now or datetime.now(timezone.utc)
    return f"GYA-{moment.strftime('%Y%m%d-%H%M%S')}-{uuid.uuid4().hex[:6].upper()}"


def _score_color(score: int | float) -> str:
    return "red" if score <= 30 else "yellow" if score < 70 else "green"


def _safe_int(value: Any, default: int = 0) -> int:
    try:
        return int(value or default)
    except (TypeError, ValueError):
        return default


def _public_videos(channel_url: str, limit: int = 3) -> list[dict[str, Any]]:
    try:
        import yt_dlp
    except ImportError as exc:
        raise RuntimeError("yt-dlp não está instalado. Instale as dependências do Thunderbolt.") from exc
    options = {"quiet": True, "skip_download": True, "extract_flat": True, "playlistend": limit, "noplaylist": False}
    with yt_dlp.YoutubeDL(options) as downloader:
        info = downloader.extract_info(channel_url, download=False)
    entries = info.get("entries") if isinstance(info, Mapping) else []
    videos: list[dict[str, Any]] = []
    for item in entries or []:
        if not isinstance(item, Mapping):
            continue
        video_id = str(item.get("id") or "").strip()
        if not video_id:
            continue
        videos.append({
            "id": video_id,
            "title": str(item.get("title") or "Sem título").strip(),
            "url": str(item.get("webpage_url") or f"https://www.youtube.com/watch?v={video_id}"),
            "thumbnail_url": str(item.get("thumbnail") or f"https://i.ytimg.com/vi/{video_id}/maxresdefault.jpg"),
            "upload_date": str(item.get("upload_date") or ""),
            "duration": _safe_int(item.get("duration")),
            "view_count": _safe_int(item.get("view_count")),
        })
    return videos[:limit]


def _download_thumbnail(video: Mapping[str, Any], directory: Path) -> str:
    directory.mkdir(parents=True, exist_ok=True)
    destination = directory / f"{video['id']}.jpg"
    if not destination.exists():
        try:
            import yt_dlp
            options = {
                "quiet": True,
                "skip_download": True,
                "writethumbnail": True,
                "outtmpl": str(directory / f"{video['id']}.%(ext)s"),
                "noplaylist": True,
            }
            with yt_dlp.YoutubeDL(options) as downloader:
                downloader.download([str(video.get("url") or f"https://www.youtube.com/watch?v={video['id']}")])
            generated = next(directory.glob(f"{video['id']}.*"), None)
            if generated and generated != destination:
                generated.replace(destination)
        except Exception as exc:
            raise RuntimeError(f"Não foi possível baixar a thumbnail {video['id']} com yt-dlp: {exc}") from exc
    if not destination.exists():
        raise RuntimeError(f"yt-dlp não gerou a thumbnail do vídeo {video['id']}.")
    return str(destination)


def _transcript(video_id: str) -> tuple[str, str]:
    try:
        from youtube_transcript_api import YouTubeTranscriptApi
    except ImportError:
        return "", "ferramenta youtube-transcript-api não instalada"
    try:
        api = YouTubeTranscriptApi()
        fetched = api.fetch(video_id)
        text = " ".join(str(item.text if hasattr(item, "text") else item.get("text", "")) for item in fetched)
        return text.strip(), "disponível" if text.strip() else "vazia"
    except Exception as exc:
        return "", str(exc)[:180]


def _title_score(title: str) -> tuple[int, str]:
    words = re.findall(r"[\wÀ-ÿ'-]+", title, flags=re.UNICODE)
    lower = title.lower()
    points = 20
    if 3 <= len(words) <= 12: points += 20
    if any(token in lower for token in ("como", "por que", "why", "how", "what", "segredo", "mistério", "mistério")): points += 20
    if re.search(r"\d", title): points += 15
    if any(token in lower for token in ("novo", "incrível", "proven", "explosive", "urgente", "fatal")): points += 10
    if len(title) <= 70: points += 15
    return min(100, points), "Curiosidade, clareza, keyword inicial e uso de números avaliados heurísticamente."


def _transcript_score(text: str) -> tuple[int, str]:
    if not text:
        return 50, "Sem transcrição pública disponível; não foi inferida retenção."
    lower = text.lower()
    score = 45
    if len(text) >= 400: score += 15
    if any(token in lower[:1800] for token in ("hoje", "neste vídeo", "today", "in this video")): score += 15
    if any(token in lower for token in ("inscreva", "subscribe", "comente", "comment")): score += 15
    if text.count(".") >= 20: score += 10
    return min(100, score), "Hook, clareza de abertura, CTA e cadência textual avaliados; retenção real requer YouTube Studio."


def _analyse_transcript_with_llm(text: str, settings: Mapping[str, Any]) -> tuple[int, str]:
    if not text:
        return _transcript_score(text)
    try:
        result = route_llm_json(
            settings,
            "You are a YouTube Growth Auditor. Return JSON only with score (0-100), diagnosis, hook, pacing, cta. Do not invent retention percentages.",
            "Analyse this transcript against the Growth Auditor criteria. Focus on the first 30 seconds, pattern interrupts, clarity and CTA.\n\n" + text[:14000],
        )
        payload = result.payload
        choices = payload.get("choices") if isinstance(payload, Mapping) else []
        content = choices[0].get("message", {}).get("content", "") if choices and isinstance(choices[0], Mapping) else ""
        match = re.search(r"\{.*\}", str(content), flags=re.S)
        parsed = json.loads(match.group(0)) if match else {}
        score = max(0, min(100, _safe_int(parsed.get("score"), _transcript_score(text)[0])))
        diagnosis = str(parsed.get("diagnosis") or _transcript_score(text)[1])[:500]
        return score, diagnosis
    except (ProviderRoutingError, ValueError, TypeError, KeyError):
        return _transcript_score(text)


def _vision_prompt(video: Mapping[str, Any]) -> str:
    return ("Analyse this YouTube thumbnail for a Growth audit. Return concise JSON with score (0-100), "
            "contrast, mobile_readability, text_words, hierarchy, emotion, overlap_risk, diagnosis. "
            "Use the agent criteria: high contrast, max three words, clear subject, readable at 5-inch size. "
            f"Video title: {video.get('title', '')}")


def analyse_thumbnail_with_paligemma(path: str, card: Mapping[str, Any]) -> dict[str, Any]:
    key = str(card.get("api_key") or "").strip()
    base = str(card.get("base_url") or "https://integrate.api.nvidia.com/v1").rstrip("/")
    if "integrate.api.nvidia.com" in base:
        base = base.replace("integrate.api.nvidia.com", "ai.api.nvidia.com")
    endpoint = base if "/vlm/google/paligemma" in base else f"{base}/vlm/google/paligemma"
    model = str(card.get("model") or "google/paligemma").strip()
    if not key:
        return {"score": 50, "diagnosis": "API key NVIDIA NIM Paligemma não configurada.", "status": "sem_dados"}
    data = base64.b64encode(Path(path).read_bytes()).decode("ascii")
    payload = {"model": model, "messages": [{"role": "user", "content": [
        {"type": "text", "text": "Evaluate this thumbnail for YouTube Growth. Return JSON with score, diagnosis, contrast, mobile_readability, text_words, hierarchy, emotion, overlap_risk."},
        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{data}"}},
    ]}], "max_tokens": 500, "temperature": 0.1}
    response = requests.post(endpoint, headers={"Authorization": f"Bearer {key}", "Accept": "application/json", "Content-Type": "application/json"}, json=payload, timeout=120)
    response.raise_for_status()
    content = response.json().get("choices", [{}])[0].get("message", {}).get("content", "")
    match = re.search(r"\{.*\}", str(content), flags=re.S)
    parsed = json.loads(match.group(0)) if match else {"diagnosis": str(content)[:1000]}
    parsed["score"] = max(0, min(100, _safe_int(parsed.get("score"), 50)))
    parsed["status"] = "analisado"
    return parsed


def _report_markdown(record: Mapping[str, Any]) -> str:
    analytics = record.get("analytics") or {}
    lines = [f"# CHANNEL AUDIT REPORT: {record.get('channel_name', 'Canal')}", "", f"- Código: `{record.get('code')}`", "- Plataforma: YouTube", f"- Data: {record.get('created_at')}", f"- Nota geral: **{record.get('overall_score', 0)}/100**", "", "## 1. Projecção financeira e contexto", "", "A análise pública não expõe RPM, país da audiência nem horas de visualização. O relatório não inventa estes valores. Para referência do agente, o YPP usa 1.000 inscritos e 4.000 horas de vídeos longos em 12 meses ou 10 milhões de visualizações de Shorts em 90 dias até 31/01/2027; a partir de 01/02/2027 a meta de Shorts indicada pelo agente é 20 milhões.", "", "## 2. Resumo do diagnóstico", "", "| Pilar | Nota | Métrica observada | Origem | Diagnóstico |", "|---|---:|---|---|---|"]
    pillar_names = {"Demanda validada": "Demanda", "Qualidade da thumbnail": "Thumbnail", "Qualidade do título": "Título", "Hook — retenção inicial": "Hook", "Ritmo e edição": "Pacing", "Origem do tráfego": "Tráfego", "Conversão em inscritos": "CTA", "Cadência de publicação": "Cadência"}
    for metric in record.get("metrics", []):
        lines.append(f"| **{pillar_names.get(metric['label'], metric['label'])}** | {metric['score']}/100 | {metric['value']} | {metric.get('source', 'unknown')} | {metric['diagnosis']} |")
    lines += ["", "## 3. Últimos 3 vídeos", "", "| Título | Visualizações | Thumbnail | Transcrição | Nota do título |", "|---|---:|---|---|---:|"]
    for video in record.get("videos", []):
        lines.append(f"| {video.get('title', '').replace('|', '/')} | {video.get('view_count', 0):,} | {video.get('thumbnail_status', '')} | {video.get('transcript_status', '')} | {video.get('title_score', 0)}/100 |")
    lines += ["", "## 4. Dados internos do YouTube Studio", "", f"Estado Analytics: **{analytics.get('status', 'not_connected')}**. {analytics.get('message', 'Sem OAuth Analytics autorizado; os valores privados permanecem indisponíveis ou estimados.')}", "", "## 5. Actionable Roadmap — Top 3 prioridades", "", "1. **REMAKE THUMBNAILS** dos vídeos abaixo de 70: aumentar contraste, sujeito claro, emoção forte e máximo de três palavras legíveis no telemóvel.", "2. **REWRITE TITLES** com Curiosity, Clarity e Urgency; colocar a keyword principal no início e usar números/adjectivos de poder quando forem verdadeiros.", "3. **EDIT HOOK**: começar pelo resultado, promessa ou estatística forte e introduzir pattern interrupts a cada 5–8 segundos.", "", "## 6. Estratégia de longo prazo", "", "Construir uma biblioteca de pelo menos 50 vídeos evergreen, publicar com cadência semanal fixa e procurar que Browse Features se torne a principal origem de tráfego. Para um criador solo, consistência supera frequência; melhorar Thumbnail + Título antes de alterar a produção.", "", "## Limitações", "", "CTR, retenção real, origem de tráfego, RPM e horas de visualização exigem dados autorizados do YouTube Studio e não são inventados a partir da página pública."]
    return "\n".join(lines) + "\n"


def run_audit(channel: Mapping[str, Any], settings: Mapping[str, Any], *, vision_card: Mapping[str, Any] | None = None, progress: Callable[[str], None] | None = None) -> dict[str, Any]:
    code = analysis_code()
    root = ANALYSES_DIR / code
    root.mkdir(parents=True, exist_ok=True)
    notify = progress or (lambda _message: None)
    channel_url = str(channel.get("url") or channel.get("handle") or "").strip()
    if not channel_url:
        raise RuntimeError("O canal seleccionado não tem URL pública ou handle YouTube.")
    notify("A buscar o canal e os 3 vídeos mais recentes…")
    try:
        videos = _public_videos(channel_url, 3)
    except Exception as exc:
        failed = {"code": code, "channel_id": str(channel.get("id") or ""), "channel_name": str(channel.get("name") or "Canal"), "platform": "YouTube", "created_at": datetime.now(timezone.utc).isoformat(), "status": "failed", "error": str(exc)[:500]}
        analyses = read_json(ANALYSES_FILENAME, [])
        if not isinstance(analyses, list): analyses = []
        analyses.append(failed)
        write_json(ANALYSES_FILENAME, analyses[-100:])
        raise
    if not videos:
        failed = {"code": code, "channel_id": str(channel.get("id") or ""), "channel_name": str(channel.get("name") or "Canal"), "platform": "YouTube", "created_at": datetime.now(timezone.utc).isoformat(), "status": "failed", "error": "Não foram encontrados vídeos públicos no canal seleccionado."}
        analyses = read_json(ANALYSES_FILENAME, [])
        if not isinstance(analyses, list): analyses = []
        analyses.append(failed)
        write_json(ANALYSES_FILENAME, analyses[-100:])
        raise RuntimeError(failed["error"])
    title_scores: list[int] = []
    transcript_scores: list[int] = []
    for index, video in enumerate(videos, 1):
        notify(f"A analisar vídeo {index}/{len(videos)}…")
        try:
            video["thumbnail_path"] = _download_thumbnail(video, root / "thumbnails")
            video["thumbnail_status"] = "baixada"
        except Exception as exc:
            video["thumbnail_path"] = ""
            video["thumbnail_status"] = f"erro: {str(exc)[:120]}"
        text, status = _transcript(str(video["id"]))
        video["transcript_status"] = status
        video["transcript_path"] = str(root / "transcripts" / f"{video['id']}.txt")
        Path(video["transcript_path"]).parent.mkdir(parents=True, exist_ok=True)
        Path(video["transcript_path"]).write_text(text, encoding="utf-8")
        video["title_score"], video["title_diagnosis"] = _title_score(video["title"])
        video["transcript_score"], video["transcript_diagnosis"] = _analyse_transcript_with_llm(text, settings)
        title_scores.append(video["title_score"])
        transcript_scores.append(video["transcript_score"])
        if vision_card and video.get("thumbnail_path"):
            try: video["vision"] = analyse_thumbnail_with_paligemma(video["thumbnail_path"], vision_card)
            except Exception as exc: video["vision"] = {"score": 50, "status": "erro", "diagnosis": str(exc)[:220]}
        else: video["vision"] = {"score": 50, "status": "sem_dados", "diagnosis": "Provider Paligemma não configurado."}
    analytics: dict[str, Any]
    try:
        from integrations.youtube_growth_api import query_channel_analytics
        analytics = query_channel_analytics(channel, settings, STORAGE)
    except Exception as exc:
        analytics = {"status": "query_failed", "message": str(exc)[:300]}
    analytics_values = analytics.get("values", {}) if analytics.get("status") == "ready" else {}
    analytics_source = "youtube_analytics_oauth" if analytics_values else "estimated_proxy"
    analytics_note = "YouTube Analytics OAuth" if analytics_values else str(analytics.get("message") or "Sem dados internos; proxy estimado")
    thumb_scores = [int((video.get("vision") or {}).get("score", 50)) for video in videos]
    metrics = [
        {"label": "Demanda validada", "score": 50, "value": f"{len(videos)} vídeos públicos", "source": "public", "diagnosis": "Amostra pública recolhida; volume de pesquisa/concorrência não disponível."},
        {"label": "Qualidade da thumbnail", "score": round(sum(thumb_scores) / len(thumb_scores)), "value": f"{len(videos)} thumbnails analisadas", "source": "paligemma" if any((video.get("vision") or {}).get("status") == "analisado" for video in videos) else "estimated", "diagnosis": "Avaliação Paligemma/NIM ou sem dados quando não configurado."},
        {"label": "Qualidade do título", "score": round(sum(title_scores) / len(title_scores)), "value": f"{len(videos)} títulos analisados", "source": "public", "diagnosis": "Curiosidade, clareza, urgência, palavras-chave e números."},
        {"label": "Hook — retenção inicial", "score": round(sum(transcript_scores) / len(transcript_scores)), "value": "Análise textual das aberturas", "source": "estimated", "diagnosis": "Inferência textual; retenção percentual real não está disponível."},
        {"label": "Ritmo e edição", "score": _safe_int(analytics_values.get("averageViewPercentage"), 50) if analytics_values else 50, "value": "Percentagem média assistida (OAuth)" if analytics_values else "Proxy: sem curva de retenção", "source": analytics_source, "diagnosis": analytics_note},
        {"label": "Origem do tráfego", "score": 50, "value": "Dados de tráfego (OAuth)" if analytics_values else "Indisponível sem OAuth", "source": analytics_source if analytics_values else "unavailable", "diagnosis": analytics_note},
        {"label": "Conversão em inscritos", "score": 50, "value": f"{analytics_values.get('subscribersGained', '—')} ganhos / {analytics_values.get('subscribersLost', '—')} perdidos" if analytics_values else "Indisponível sem Analytics", "source": analytics_source if analytics_values else "unavailable", "diagnosis": analytics_note},
        {"label": "Cadência de publicação", "score": 50, "value": "Datas públicas recolhidas", "source": "public", "diagnosis": "Cadência detalhada será calculada quando datas válidas forem fornecidas."},
    ]
    weights = {"Qualidade da thumbnail": 0.30, "Qualidade do título": 0.25, "Hook — retenção inicial": 0.25, "Conversão em inscritos": 0.20}
    overall = round(sum(metric["score"] * weights.get(metric["label"], 0) for metric in metrics) / sum(weights.values()))
    record = {"code": code, "channel_id": str(channel.get("youtube_channel_id") or channel.get("id") or ""), "channel_name": str(channel.get("name") or "Canal"), "platform": "YouTube", "created_at": datetime.now(timezone.utc).isoformat(), "overall_score": overall, "score_color": _score_color(overall), "score_weights": weights, "analytics": analytics, "metrics": metrics, "videos": videos, "status": "completed"}
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


__all__ = ["AGENT_METRICS", "ANALYSES_DIR", "analysis_code", "analyse_thumbnail_with_paligemma", "list_analyses", "run_audit"]
