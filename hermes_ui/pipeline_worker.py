from __future__ import annotations

import json
import os
import queue
import re
import subprocess
import threading
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from integrations.upload_routing import upload_with_default_route
from hermes_ui.creative_generation import CreativeGenerationError, generate_creative_package, generate_title_and_keywords, generate_thumbnail_prompt, generate_topic_for_channel
from hermes_ui.script_documents import save_script_document
from hermes_ui.script_generation import generate_script_document
from hermes_ui.storage import STORAGE, ensure_storage, read_json, write_json
from hermes_ui.llm_providers import active_llm_card, provider_definition
from hermes_ui.media_generation import MediaGenerationError, _append_generation_constraints, generate_image_from_pool, generate_video_from_pool
from hermes_ui.media_providers import media_cards_for_pool
from hermes_ui.thumbnail_generation import ThumbnailGenerationError, generate_thumbnail_image

PIPELINE_LOCK_FILENAME = "pipeline_worker.lock"
PIPELINE_LOG_FILENAME = "pipeline_worker.json"
VIDEO_TIMEOUT_SECONDS = 20 * 60
STALE_TASK_SECONDS = VIDEO_TIMEOUT_SECONDS + 5 * 60
WORKER_HEARTBEAT_TIMEOUT_SECONDS = 15


class PipelineError(RuntimeError):
    """Raised when a pipeline stage cannot complete with an actionable error."""


class PipelineStopped(PipelineError):
    """Raised when the user stops a task while the worker is processing it."""


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _settings() -> dict[str, Any]:
    value = read_json("settings.json", {})
    return value if isinstance(value, dict) else {}


def _generate_pipeline_thumbnail(
    settings: dict[str, Any],
    prompt: str,
    *,
    topic: str,
    variant_index: int = 0,
    lettering_text: str = "",
    lettering_prompt: str = "",
) -> Path:
    """Use the image pool while keeping the legacy single-Nano call seam."""
    cards = media_cards_for_pool(settings, "image")
    if len(cards) == 1 and str(cards[0].get("provider") or "") == "nano_banana":
        return generate_thumbnail_image(
            settings,
            prompt,
            topic=topic,
            variant_index=variant_index,
            lettering_text=lettering_text,
            lettering_prompt=lettering_prompt,
        )
    return generate_image_from_pool(
        settings,
        prompt,
        topic=topic,
        variant_index=variant_index,
        lettering_text=lettering_text,
        lettering_prompt=lettering_prompt,
    )


def _lock_path() -> Path:
    ensure_storage()
    return STORAGE / "state" / PIPELINE_LOCK_FILENAME


def _pid_alive(pid: int) -> bool:
    if pid <= 0:
        return False
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    except OSError:
        return False
    return True


def _acquire_lock() -> Path | None:
    path = _lock_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        descriptor = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    except FileExistsError:
        try:
            old_pid = int(path.read_text(encoding="utf-8").strip())
        except (OSError, ValueError):
            old_pid = 0
        if _pid_alive(old_pid):
            return None
        try:
            path.unlink()
        except OSError:
            return None
        try:
            descriptor = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        except FileExistsError:
            return None
    try:
        os.write(descriptor, str(os.getpid()).encode("ascii"))
    finally:
        os.close(descriptor)
    return path


def _write_worker_state(**updates: Any) -> None:
    state = read_json(PIPELINE_LOG_FILENAME, {})
    if not isinstance(state, dict):
        state = {}
    state.update(updates)
    state["updated_at"] = _now()
    write_json(PIPELINE_LOG_FILENAME, state)


def _worker_heartbeat(**updates: Any) -> None:
    _write_worker_state(
        worker_pid=os.getpid(),
        last_heartbeat_at=_now(),
        **updates,
    )


def _parse_timestamp(value: Any) -> datetime | None:
    text = str(value or "").strip()
    if not text:
        return None
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        return None
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)


def load_pipeline_worker_status() -> dict[str, Any]:
    """Return the persisted worker heartbeat for the Backlog UI."""
    status = read_json(PIPELINE_LOG_FILENAME, {})
    if not isinstance(status, dict):
        status = {}
    heartbeat_at = _parse_timestamp(status.get("last_heartbeat_at"))
    status["alive"] = bool(
        heartbeat_at
        and (datetime.now(timezone.utc) - heartbeat_at.astimezone(timezone.utc)).total_seconds()
        <= WORKER_HEARTBEAT_TIMEOUT_SECONDS
    )
    return status


def _recover_stale_tasks() -> list[str]:
    """Convert abandoned doing tasks to failed after the worker timeout window."""
    from hermes_ui.domain import update_task

    recovered: list[str] = []
    current_time = datetime.now(timezone.utc)
    for task in read_json("tasks.json", []):
        if not isinstance(task, dict) or str(task.get("state") or "") != "doing":
            continue
        updated_at = _parse_timestamp(task.get("updated_at"))
        if not updated_at:
            continue
        age_seconds = (current_time - updated_at.astimezone(timezone.utc)).total_seconds()
        if age_seconds <= STALE_TASK_SECONDS:
            continue
        task_id = str(task.get("id") or "")
        if not task_id:
            continue
        message = (
            f"A tarefa ficou sem heartbeat durante mais de {STALE_TASK_SECONDS // 60} minutos. "
            "Foi marcada como falhada para evitar execução eterna; reveja o log do worker."
        )
        update_task(task_id, {"state": "failed", "error": message, "failed_stage": task.get("stage") or "pipeline"})
        recovered.append(task_id)
    return recovered


def recover_stale_tasks() -> list[str]:
    """Public wrapper used by the UI to recover tasks after an abrupt worker exit."""
    return _recover_stale_tasks()


def _task_by_id(task_id: str) -> dict[str, Any] | None:
    return next((task for task in read_json("tasks.json", []) if isinstance(task, dict) and task.get("id") == task_id), None)


def _update(task_id: str, **updates: Any) -> dict[str, Any]:
    from hermes_ui.domain import update_task

    current = _task_by_id(task_id)
    if not current:
        raise PipelineError(f"Tarefa {task_id} deixou de existir durante a execução.")
    if str(current.get("state") or "") in {"blocked", "cancelled"}:
        raise PipelineStopped("A tarefa foi parada pelo utilizador.")
    updated = update_task(task_id, updates)
    if not updated:
        raise PipelineError(f"Tarefa {task_id} deixou de existir durante a execução.")
    _worker_heartbeat(
        task_id=task_id,
        status="running",
        stage=str(updated.get("stage") or "pipeline"),
        progress=int(updated.get("progress") or 0),
    )
    return updated


def _channel_for_task(task: dict[str, Any]) -> dict[str, Any]:
    channel_id = str(task.get("channel_id") or "")
    return next((channel for channel in read_json("channels.json", []) if str(channel.get("id")) == channel_id), {})


def _blueprint_for_channel(channel: dict[str, Any]) -> dict[str, Any]:
    blueprint_id = str(channel.get("default_blueprint_id") or channel.get("blueprint_id") or "")
    blueprints = read_json("blueprints.json", [])
    if not isinstance(blueprints, list):
        return {}
    return next((item for item in blueprints if isinstance(item, dict) and str(item.get("id")) == blueprint_id), {})


def _keywords(topic: str, title: str, niche: str = "") -> list[str]:
    """Derive deterministic SEO keywords when the LLM does not return a keyword list."""
    source = f"{title} {topic} {niche}".casefold()
    words = re.findall(r"[\wÀ-ÿ]{4,}", source, flags=re.UNICODE)
    blocked = {"para", "como", "sobre", "mais", "esse", "esta", "that", "this", "with", "from", "video"}
    result: list[str] = []
    for word in words:
        if word in blocked or word in result:
            continue
        result.append(word)
    return result[:15]


def _save_json_artifact(task_id: str, name: str, payload: dict[str, Any]) -> str:
    directory = STORAGE / "artifacts"
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / f"{task_id}-{name}.json"
    temporary = path.with_suffix(".tmp")
    temporary.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    temporary.replace(path)
    return str(path)


def _configured_moneyprinter_root(settings: dict[str, Any]) -> Path | None:
    """Resolve the installed MoneyPrinterTurbo project selected by the user."""
    configured = str(settings.get("moneyprinter_path") or os.environ.get("MONEYPRINTER_PATH") or "").strip()
    if not configured:
        return None
    root = Path(configured).expanduser().resolve()
    if not (root / "cli.py").is_file():
        raise PipelineError(f"A pasta configurada do MoneyPrinterTurbo não contém cli.py: {root}")
    if not ((root / "config.toml").is_file() or (root / "config.example.toml").is_file()):
        raise PipelineError(f"A pasta configurada do MoneyPrinterTurbo não contém config.toml: {root}")
    return root


def _helper_output_value(output: str, key: str) -> str:
    match = re.search(rf"(?m)^{re.escape(key)}=(.+)$", output)
    return match.group(1).strip() if match else ""


def _redact_helper_output(text: str) -> str:
    for key in ("MPT_LLM_API_KEY", "MPT_PEXELS_API_KEY"):
        secret = os.environ.get(key, "").strip()
        if secret:
            text = text.replace(secret, "[redacted]")
    return text


def _persist_video_diagnostics(task: dict[str, Any], output: str) -> dict[str, str]:
    """Persist only bounded helper diagnostics and return its declared file paths."""
    task_id = str(task.get("id") or "").strip()
    if not task_id:
        return {}
    log_file = _helper_output_value(output, "LOG_FILE")
    result_file = _helper_output_value(output, "RESULT_FILE")
    try:
        payload: dict[str, Any] = {
            "captured_at": _now(),
            "log_file": log_file,
            "result_file": result_file,
            "output_tail": _redact_helper_output(output[-6000:]),
        }
        artifact_path = _save_json_artifact(task_id, "video-diagnostics", payload)
        current = _task_by_id(task_id) or task
        artifacts = dict(current.get("artifacts") or {})
        artifacts["video_diagnostics"] = artifact_path
        updates: dict[str, Any] = {"artifacts": artifacts}
        if log_file:
            updates["video_log"] = log_file
            artifacts["video_log"] = log_file
        if result_file:
            updates["video_result"] = result_file
            artifacts["video_result"] = result_file
        from hermes_ui.domain import update_task
        update_task(task_id, updates)
        return {"log_file": log_file, "result_file": result_file, "artifact": artifact_path}
    except Exception:
        # Diagnostics must never hide the actual generation error.
        return {"log_file": log_file, "result_file": result_file}


def _stop_process(process: subprocess.Popen[str]) -> None:
    if process.poll() is None:
        process.kill()
    try:
        process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait()


def _run_video_helper(task: dict[str, Any]) -> Path:
    helper_dir = Path(__file__).resolve().parents[1] / "seed" / "skills"
    helper = helper_dir / "mpt_agent.py"
    if not helper.is_file():
        raise PipelineError("O helper de vídeo MoneyPrinterTurbo não está instalado no pacote.")
    subject = str(task.get("topic") or "").strip()
    if not subject:
        raise PipelineError("A etapa Vídeo não recebeu um tema válido.")
    settings = _settings()
    configured_root = _configured_moneyprinter_root(settings)
    task_id = str(task.get("id") or "").strip()
    if not task_id:
        raise PipelineError("A tarefa de vídeo não tem um identificador válido.")
    env = os.environ.copy()
    card = active_llm_card(settings)
    provider = str(card.get("provider") or "openai").strip()
    definition = provider_definition(provider)
    env_values = {
        "MPT_LLM_PROVIDER": provider,
        "MPT_LLM_API_KEY": str(card.get("api_key") or "").strip(),
        "MPT_LLM_BASE_URL": str(card.get("base_url") or definition.default_base_url or "").strip(),
        "MPT_LLM_MODEL_NAME": str(card.get("model") or "").strip(),
        "MPT_PEXELS_API_KEY": str(settings.get("pexels_api_key") or "").strip(),
    }
    for key, value in env_values.items():
        if value:
            env[key] = value
    command = ["uv", "run", "--no-project", "--python", "3.11", "python", "mpt_agent.py"]
    if configured_root:
        command.extend(["--root", str(configured_root)])
    command.extend(["--subject", subject])
    output_lines: list[str] = []
    line_queue: queue.Queue[str | None] = queue.Queue()
    started_at = time.monotonic()
    process: subprocess.Popen[str] | None = None

    def _read_output() -> None:
        if process is None or process.stdout is None:
            line_queue.put(None)
            return
        for line in iter(process.stdout.readline, ""):
            line_queue.put(line.rstrip())
        process.stdout.close()
        line_queue.put(None)

    try:
        process = subprocess.Popen(
            command,
            cwd=helper_dir,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        )
    except FileNotFoundError as exc:
        raise PipelineError("O comando uv não está instalado; não foi possível iniciar a geração de vídeo.") from exc

    reader = threading.Thread(target=_read_output, name=f"mpt-output-{task.get('id', 'video')}", daemon=True)
    reader.start()
    output_finished = False
    last_heartbeat = 0.0
    try:
        while True:
            try:
                line = line_queue.get(timeout=0.5)
                if line is None:
                    output_finished = True
                elif line:
                    output_lines.append(line)
            except queue.Empty:
                pass
            elapsed = time.monotonic() - started_at
            if elapsed - last_heartbeat >= 5:
                # O helper expõe o resultado final, mas não uma percentagem estável.
                # Mantemos uma faixa reservada para a etapa de vídeo e avançamos-a
                # lentamente enquanto o processo responde, sem fingir conclusão.
                video_progress = min(79, 52 + int(elapsed // 15))
                current_task = _task_by_id(task_id)
                if current_task and str(current_task.get("state") or "") in {"blocked", "cancelled"}:
                    _stop_process(process)
                    raise PipelineStopped("A tarefa foi parada pelo utilizador.")
                _update(
                    task_id,
                    progress=video_progress,
                    video_elapsed_seconds=int(elapsed),
                )
                _worker_heartbeat(
                    task_id=str(task.get("id") or ""),
                    status="running",
                    stage="video",
                    progress=video_progress,
                    video_elapsed_seconds=int(elapsed),
                )
                last_heartbeat = elapsed
            if process.poll() is not None and output_finished:
                break
            if elapsed >= VIDEO_TIMEOUT_SECONDS:
                _stop_process(process)
                raise PipelineError(f"A etapa Vídeo excedeu o limite de {VIDEO_TIMEOUT_SECONDS // 60} minutos e foi encerrada.")
    finally:
        reader.join(timeout=2)
        _persist_video_diagnostics(task, "\n".join(output_lines))
    if process.returncode is None:
        process.wait(timeout=5)
    result_code = process.returncode
    output = "\n".join(output_lines)
    _persist_video_diagnostics(task, output)
    if result_code == 10:
        raise PipelineError("A geração de vídeo precisa de credenciais adicionais do MoneyPrinterTurbo.")
    if result_code != 0:
        detail = _redact_helper_output(output[-1200:]).strip() or "erro sem detalhes devolvidos pelo helper"
        raise PipelineError(f"MoneyPrinterTurbo falhou na etapa Vídeo: {detail}")
    match = re.search(r"(?m)^VIDEO_FILE=(.+)$", output)
    video_path = Path(match.group(1).strip()).expanduser() if match else None
    if not video_path or not video_path.is_file() or video_path.stat().st_size <= 0:
        result_root = configured_root or (Path.home() / "MoneyPrinterTurbo")
        result_file = result_root / ".agent-logs" / "moneyprinterturbo-video" / "latest-result.json"
        if result_file.is_file():
            try:
                payload = json.loads(result_file.read_text(encoding="utf-8"))
                video_path = Path(str(payload.get("video_file") or payload.get("VIDEO_FILE") or "")).expanduser()
            except (OSError, json.JSONDecodeError):
                video_path = None
    if not video_path or not video_path.is_file() or video_path.stat().st_size <= 0:
        raise PipelineError("MoneyPrinterTurbo terminou sem devolver um MP4 válido.")
    return video_path


def _run_task(task: dict[str, Any]) -> dict[str, Any]:
    task_id = str(task.get("id") or "")
    channel = _channel_for_task(task)
    settings = _settings()
    blueprint = _blueprint_for_channel(channel)
    topic = str(task.get("topic") or "").strip()
    if not topic or str(task.get("topic_source") or "") in {"auto", "llm_pending"}:
        _update(task_id, stage="topic", state="doing", progress=5, error=None)
        topic_result = generate_topic_for_channel(settings, channel, blueprint, user_context=str(task.get("topic_context") or ""))
        topic = str(topic_result.get("topic") or "").strip()
        if not topic:
            raise PipelineError("A IA não devolveu um tema válido.")
        _update(task_id, topic=topic, topic_source="llm", ai_generation={"topic": topic_result}, progress=12)

    _update(task_id, stage="script", state="doing", progress=18, error=None)
    generation_settings = task.get("generation_settings") if isinstance(task.get("generation_settings"), dict) else {}
    provided_script = str(generation_settings.get("video_script") or "").strip()
    if provided_script:
        script = {
            "document_type": "video_script",
            "title": str(task.get("title") or topic),
            "summary": topic,
            "content": provided_script,
            "language": str(task.get("language") or channel.get("language") or "Português"),
            "blueprint_id": str(blueprint.get("id") or ""),
            "blueprint_name": str(blueprint.get("name") or "SEM BLUEPRINT CONFIGURADO"),
            "channel_id": str(channel.get("id") or ""),
            "channel_name": str(channel.get("name") or "Canal sem nome"),
            "generation_settings": generation_settings,
            "generated_by": "video_creation_form",
        }
    else:
        script = generate_script_document(
            settings,
            document_type="Roteiro de vídeo",
            title=str(task.get("title") or topic),
            brief=topic,
            language=str(task.get("language") or channel.get("language") or "Português"),
            channel=channel,
            blueprint=blueprint,
            structure_notes=str(generation_settings.get("script_structure_notes") or ""),
            generation_settings=generation_settings,
        )
    script_record = save_script_document(script)
    artifacts = dict(task.get("artifacts") or {})
    artifacts["script"] = script_record.get("path", "")
    _update(task_id, artifacts=artifacts, progress=30)

    _update(task_id, stage="title", state="doing", progress=35)
    provided_title = str(task.get("title") or "").strip()
    provided_keywords = generation_settings.get("video_keywords") or task.get("keywords")
    if isinstance(provided_keywords, str):
        provided_keywords = re.split(r"[,\n;|]+", provided_keywords)
    provided_keywords = [str(item).strip() for item in provided_keywords or [] if str(item).strip()]
    title_candidates = task.get("title_candidates") if isinstance(task.get("title_candidates"), list) else []
    editorial: dict[str, Any] = {
        "title": provided_title or topic,
        "title_candidates": title_candidates,
        "keywords": provided_keywords,
    }
    if not provided_title:
        try:
            editorial = generate_title_and_keywords(
                settings,
                channel,
                topic,
                blueprint,
                language=str(task.get("language") or channel.get("language") or "Português"),
            )
        except CreativeGenerationError:
            # A falha editorial não deve impedir a geração do vídeo: usa o tema
            # como título e keywords determinísticas, deixando o erro de imagem
            # para a etapa posterior e independente da criação do MP4.
            editorial = {"title": topic, "title_candidates": [], "keywords": []}
    title = str(editorial.get("title") or provided_title or topic).strip()
    keywords = provided_keywords[:15] or (
        editorial.get("keywords") if isinstance(editorial.get("keywords"), list) else []
    )
    keywords = [str(item).strip() for item in keywords if str(item).strip()][:15] or _keywords(
        topic,
        title,
        str(channel.get("niche") or ""),
    )
    title_candidates = editorial.get("title_candidates") if isinstance(editorial.get("title_candidates"), list) else title_candidates
    title_artifact = _save_json_artifact(
        task_id,
        "title-keywords",
        {"topic": topic, "title": title, "keywords": keywords, "title_candidates": title_candidates},
    )
    artifacts = {**artifacts, "title_keywords": title_artifact}
    _update(task_id, title=title, tags=keywords, artifacts=artifacts, title_candidates=title_candidates, progress=45)

    _update(task_id, stage="keywords", state="doing", progress=48)
    _update(task_id, tags=keywords, progress=50)

    # O vídeo é deliberadamente concluído antes de qualquer chamada ao provider
    # de imagem. O artefacto fica persistido mesmo que a quota da thumbnail falhe.
    _update(task_id, stage="video", state="doing", progress=52, error=None)
    video_cards = media_cards_for_pool(settings, "video")
    if bool(settings.get("media_video_pool_enabled")) and video_cards:
        try:
            video_prompt = _append_generation_constraints(
                f"Título: {title}\n\nRoteiro:\n{str(script.get('content') or '')[:12000]}",
                kind="video",
            )
            video_path = generate_video_from_pool(settings, video_prompt)
        except MediaGenerationError as exc:
            raise PipelineError(f"Pool de vídeo externo: {exc}") from exc
    else:
        video_path = _run_video_helper({**task, "topic": topic, "title": title})
    current_after_video = _task_by_id(task_id) or {}
    artifacts = dict(current_after_video.get("artifacts") or artifacts)
    artifacts["video"] = str(video_path)
    _update(task_id, artifacts=artifacts, video_ready=True, progress=80)

    _update(task_id, stage="thumbnail_prompt", state="doing", progress=82, error=None)
    existing_variant = task.get("thumbnail_variant") if isinstance(task.get("thumbnail_variant"), dict) else {}
    existing_variant = dict(existing_variant)
    if not str(existing_variant.get("image_prompt") or "").strip() and str(task.get("thumbnail_prompt") or "").strip():
        existing_variant["image_prompt"] = str(task.get("thumbnail_prompt") or "").strip()
    if not str(existing_variant.get("overlay_text") or "").strip() and str(task.get("thumbnail_text") or "").strip():
        existing_variant["overlay_text"] = str(task.get("thumbnail_text") or "").strip()
    variant = existing_variant
    if not str(variant.get("image_prompt") or "").strip():
        try:
            variant = generate_thumbnail_prompt(
                settings,
                channel,
                topic,
                blueprint=blueprint,
                language=str(task.get("language") or channel.get("language") or "Português"),
            )
        except CreativeGenerationError as exc:
            raise PipelineError(f"Não foi possível gerar o prompt da thumbnail: {exc}") from exc
    prompt_payload = {
        "topic": topic,
        "title": title,
        "keywords": keywords,
        "thumbnail": variant,
        "requirements": {
            "aspect_ratio": "16:9",
            "resolution": "1920x1080",
            "max_elements": 3,
            "max_overlay_words": 4,
            "lettering_required": True,
            "lettering_text": str(variant.get("overlay_text") or ""),
            "lettering_prompt": str(variant.get("lettering_prompt") or ""),
        },
    }
    prompt_artifact = _save_json_artifact(task_id, "thumbnail-prompt", prompt_payload)
    artifacts["thumbnail_prompt_json"] = prompt_artifact
    _update(
        task_id,
        stage="thumbnail_prompt",
        state="doing",
        progress=84,
        thumbnail_variant=variant,
        thumbnail_prompt=str(variant.get("image_prompt") or ""),
        thumbnail_text=str(variant.get("overlay_text") or ""),
        thumbnail_status="prompt_ready",
        artifacts=artifacts,
    )

    _update(task_id, stage="thumbnail", state="doing", progress=86, error=None)
    current_artifacts = dict((_task_by_id(task_id) or {}).get("artifacts") or artifacts)
    existing_thumbnail = Path(str(current_artifacts.get("thumbnail") or variant.get("image_path") or "")).expanduser()
    if existing_thumbnail.is_file() and existing_thumbnail.stat().st_size > 0:
        thumbnail_path = existing_thumbnail
    else:
        try:
            thumbnail_path = _generate_pipeline_thumbnail(
                settings,
                str(variant.get("image_prompt") or ""),
                topic=topic,
                variant_index=0,
                lettering_text=str(variant.get("overlay_text") or ""),
                lettering_prompt=str(variant.get("lettering_prompt") or ""),
            )
        except (MediaGenerationError, ThumbnailGenerationError) as exc:
            raise PipelineError(f"A thumbnail não foi gerada; o vídeo já está disponível em {video_path}: {exc}") from exc
    artifacts = dict((_task_by_id(task_id) or {}).get("artifacts") or current_artifacts)
    artifacts["thumbnail"] = str(thumbnail_path)
    _update(task_id, artifacts=artifacts, thumbnail_status="generated", progress=90)

    _update(task_id, stage="upload", state="doing", progress=94, error=None)
    result = upload_with_default_route(
        settings,
        storage_root=STORAGE,
        channel=channel,
        account=next((item for item in settings.get("youtube_batch_accounts", []) if isinstance(item, dict) and str(item.get("id")) == str(channel.get("google_account_id"))), None),
        video_path=str(video_path),
        title=title,
        description=str(script.get("summary") or "") + "\n\n" + str(script.get("content") or "")[:5000],
        tags=keywords,
        language=str(task.get("language") or channel.get("language") or "pt-BR"),
        privacy_status="unlisted",
        thumbnail_path=str(thumbnail_path),
        captions_path=str(artifacts.get("captions") or ""),
    )
    if not result.ok:
        raise PipelineError(result.message)
    artifacts["upload"] = result.data
    return _update(task_id, stage="upload", state="done", progress=100, artifacts=artifacts, error=None)


def run_once() -> dict[str, Any]:
    ensure_storage()
    lock = _acquire_lock()
    if lock is None:
        return {"ok": True, "busy": True}
    try:
        recovered = _recover_stale_tasks()
        tasks = read_json("tasks.json", [])
        candidate = next((task for task in tasks if isinstance(task, dict) and task.get("state") in {"to_do", "doing"}), None)
        if not candidate:
            _worker_heartbeat(last_task_id=None, last_error="", status="idle", stage="idle", progress=0, recovered_task_ids=recovered)
            return {"ok": True, "status": "idle", "recovered_task_ids": recovered}
        task_id = str(candidate.get("id") or "")
        _worker_heartbeat(last_task_id=task_id, status="running", stage=str(candidate.get("stage") or "pipeline"), progress=int(candidate.get("progress") or 0), last_error="", recovered_task_ids=recovered)
        try:
            result = _run_task(candidate)
            _worker_heartbeat(status="completed", last_error="", stage=str(result.get("stage") or "upload"), progress=100, task_id=task_id)
            return {"ok": True, "task_id": task_id, "task": result, "recovered_task_ids": recovered}
        except PipelineStopped as exc:
            current_task = _task_by_id(task_id) or candidate
            current_state = str(current_task.get("state") or "")
            if current_state not in {"blocked", "cancelled"}:
                from hermes_ui.domain import update_task
                update_task(task_id, {"state": "blocked", "error": str(exc), "failed_stage": current_task.get("stage") or "pipeline"})
            _worker_heartbeat(status="stopped", last_error=str(exc), stage=str(current_task.get("stage") or "pipeline"), progress=int(current_task.get("progress") or 0), task_id=task_id)
            return {"ok": True, "task_id": task_id, "status": "stopped", "recovered_task_ids": recovered}
        except Exception as exc:
            message = str(exc)[:2000]
            from hermes_ui.domain import update_task
            current_task = _task_by_id(task_id) or candidate
            update_task(task_id, {"state": "failed", "error": message, "failed_stage": current_task.get("stage") or "pipeline"})
            _worker_heartbeat(status="failed", last_error=message, stage=str(current_task.get("stage") or "pipeline"), progress=int(current_task.get("progress") or 0), task_id=task_id)
            return {"ok": False, "task_id": task_id, "error": message, "recovered_task_ids": recovered}
    finally:
        try:
            lock.unlink()
        except FileNotFoundError:
            pass


def run_worker(interval_seconds: int = 5) -> None:
    ensure_storage()
    _worker_heartbeat(status="starting", stage="idle", progress=0, last_error="")
    while True:
        run_once()
        time.sleep(max(2, int(interval_seconds)))


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="Executor do pipeline de criação de vídeos Thunderbolt")
    parser.add_argument("--once", action="store_true")
    parser.add_argument("--interval", type=int, default=5)
    args = parser.parse_args()
    if args.once:
        print(json.dumps(run_once(), ensure_ascii=False), flush=True)
    else:
        run_worker(args.interval)


if __name__ == "__main__":
    main()
