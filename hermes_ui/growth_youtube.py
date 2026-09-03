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


def _public_videos(channel_url: str, limit: int = 10) -> list[dict[str, Any]]:
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
        response = requests.get(str(video.get("thumbnail_url") or ""), timeout=30)
        response.raise_for_status()
        destination.write_bytes(response.content)
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
    model = str(card.get("model") or "google/paligemma").strip()
    if not key:
        return {"score": 50, "diagnosis": "API key NVIDIA NIM Paligemma não configurada.", "status": "sem_dados"}
    data = base64.b64encode(Path(path).read_bytes()).decode("ascii")
    payload = {"model": model, "messages": [{"role": "user", "content": [
        {"type": "text", "text": "Evaluate this thumbnail for YouTube Growth. Return JSON with score, diagnosis, contrast, mobile_readability, text_words, hierarchy, emotion, overlap_risk."},
        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{data}"}},
    ]}], "max_tokens": 500, "temperature": 0.1}
    response = requests.post(f"{base}/chat/completions", headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"}, json=payload, timeout=120)
    response.raise_for_status()
    content = response.json().get("choices", [{}])[0].get("message", {}).get("content", "")
    match = re.search(r"\{.*\}", str(content), flags=re.S)
    parsed = json.loads(match.group(0)) if match else {"diagnosis": str(content)[:1000]}
    parsed["score"] = max(0, min(100, _safe_int(parsed.get("score"), 50)))
    parsed["status"] = "analisado"
    return parsed


def _report_markdown(record: Mapping[str, Any]) -> str:
    lines = [f"# CHANNEL AUDIT REPORT: {record.get('channel_name', 'Canal')}", "", f"- Código: `{record.get('code')}`", f"- Plataforma: YouTube", f"- Data: {record.get('created_at')}", f"- Nota geral: **{record.get('overall_score', 0)}/100**", "", "## Diagnóstico por métrica", "", "| Métrica | Nota | Evidência | Diagnóstico |", "|---|---:|---|---|"]
    for metric in record.get("metrics", []):
        lines.append(f"| {metric['label']} | {metric['score']}/100 | {metric['value']} | {metric['diagnosis']} |")
    lines += ["", "## Últimos 10 vídeos", "", "| Título | Visualizações | Thumbnail | Transcrição | Nota do título |", "|---|---:|---|---|---:|"]
    for video in record.get("videos", []):
        lines.append(f"| {video.get('title', '').replace('|', '/')} | {video.get('view_count', 0):,} | {video.get('thumbnail_status', '')} | {video.get('transcript_status', '')} | {video.get('title_score', 0)}/100 |")
    lines += ["", "## Top 3 prioridades", "", "1. Melhorar primeiro thumbnails e títulos abaixo de 70, aumentando contraste e reduzindo texto.", "2. Reforçar o hook inicial com o resultado ou promessa nos primeiros segundos.", "3. Introduzir CTA contextual e pattern interrupts ao longo do vídeo.", "", "## Limitações", "", "CTR, retenção real, origem de tráfego, RPM e horas de visualização exigem dados autorizados do YouTube Studio e não são inventados a partir da página pública."]
    return "\n".join(lines) + "\n"


def run_audit(channel: Mapping[str, Any], settings: Mapping[str, Any], *, vision_card: Mapping[str, Any] | None = None, progress: Callable[[str], None] | None = None) -> dict[str, Any]:
    code = analysis_code()
    root = ANALYSES_DIR / code
    root.mkdir(parents=True, exist_ok=True)
    notify = progress or (lambda _message: None)
    channel_url = str(channel.get("url") or channel.get("handle") or "").strip()
    if not channel_url:
        raise RuntimeError("O canal seleccionado não tem URL pública ou handle YouTube.")
    notify("A buscar o canal e os 10 vídeos mais recentes…")
    videos = _public_videos(channel_url, 10)
    if not videos:
        raise RuntimeError("Não foram encontrados vídeos públicos no canal seleccionado.")
    title_scores: list[int] = []
    transcript_scores: list[int] = []
    for index, video in enumerate(videos, 1):
        notify(f"A analisar vídeo {index}/{len(videos)}…")
        video["thumbnail_path"] = _download_thumbnail(video, root / "thumbnails")
        video["thumbnail_status"] = "baixada"
        text, status = _transcript(str(video["id"]))
        video["transcript_status"] = status
        video["transcript_path"] = str(root / "transcripts" / f"{video['id']}.txt")
        Path(video["transcript_path"]).parent.mkdir(parents=True, exist_ok=True)
        Path(video["transcript_path"]).write_text(text, encoding="utf-8")
        video["title_score"], video["title_diagnosis"] = _title_score(video["title"])
        video["transcript_score"], video["transcript_diagnosis"] = _analyse_transcript_with_llm(text, settings)
        title_scores.append(video["title_score"])
        transcript_scores.append(video["transcript_score"])
        if vision_card:
            try: video["vision"] = analyse_thumbnail_with_paligemma(video["thumbnail_path"], vision_card)
            except Exception as exc: video["vision"] = {"score": 50, "status": "erro", "diagnosis": str(exc)[:220]}
        else: video["vision"] = {"score": 50, "status": "sem_dados", "diagnosis": "Provider Paligemma não configurado."}
    thumb_scores = [int((video.get("vision") or {}).get("score", 50)) for video in videos]
    metrics = [
        {"label": "Demanda validada", "score": 50, "value": f"{len(videos)} vídeos públicos", "diagnosis": "Amostra pública recolhida; volume de pesquisa/concorrência não disponível."},
        {"label": "Qualidade da thumbnail", "score": round(sum(thumb_scores) / len(thumb_scores)), "value": f"{len(videos)} thumbnails analisadas", "diagnosis": "Avaliação Paligemma/NIM ou sem dados quando não configurado."},
        {"label": "Qualidade do título", "score": round(sum(title_scores) / len(title_scores)), "value": f"{len(videos)} títulos analisados", "diagnosis": "Curiosidade, clareza, urgência, palavras-chave e números."},
        {"label": "Hook — retenção inicial", "score": round(sum(transcript_scores) / len(transcript_scores)), "value": "Análise textual das aberturas", "diagnosis": "Inferência textual; retenção percentual real não está disponível."},
        {"label": "Ritmo e edição", "score": 50, "value": "Sem vídeo/curva de retenção", "diagnosis": "Requer gráfico de retenção do YouTube Studio."},
        {"label": "Origem do tráfego", "score": 50, "value": "Sem dados públicos", "diagnosis": "Requer YouTube Studio."},
        {"label": "Conversão em inscritos", "score": 50, "value": "Sem inscritos por vídeo", "diagnosis": "Requer Analytics autorizado."},
        {"label": "Cadência de publicação", "score": 50, "value": "Datas públicas recolhidas", "diagnosis": "Cadência detalhada será calculada quando datas válidas forem fornecidas."},
    ]
    overall = round(sum(metric["score"] for metric in metrics) / len(metrics))
    record = {"code": code, "channel_id": str(channel.get("id") or ""), "channel_name": str(channel.get("name") or "Canal"), "platform": "YouTube", "created_at": datetime.now(timezone.utc).isoformat(), "overall_score": overall, "score_color": _score_color(overall), "metrics": metrics, "videos": videos, "status": "completed"}
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
