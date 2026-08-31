"""Composio Platform adapter for user-selected video upload tools."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class ComposioUploadError(ValueError):
    """Safe, user-facing validation or integration error."""


def _safe_value(value: Any) -> Any:
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, dict):
        return {str(key): _safe_value(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_safe_value(item) for item in value]
    for method in ("model_dump", "to_dict", "dict"):
        converter = getattr(value, method, None)
        if callable(converter):
            try:
                return _safe_value(converter())
            except Exception:
                pass
    attributes = getattr(value, "__dict__", None)
    if isinstance(attributes, dict):
        return {str(key): _safe_value(item) for key, item in attributes.items()}
    return str(value)


def _tool_item(tool: Any) -> dict[str, Any]:
    raw = _safe_value(tool)
    if isinstance(raw, dict) and isinstance(raw.get("function"), dict):
        function = raw["function"]
        return {
            "slug": str(function.get("name") or raw.get("name") or ""),
            "name": str(function.get("name") or raw.get("name") or ""),
            "description": str(function.get("description") or raw.get("description") or ""),
            "toolkit": str(raw.get("toolkit") or ""),
            "schema": function.get("parameters") or {},
        }
    if isinstance(raw, dict):
        toolkit = raw.get("toolkit")
        if isinstance(toolkit, dict):
            toolkit = toolkit.get("slug") or toolkit.get("name") or ""
        return {
            "slug": str(raw.get("slug") or raw.get("name") or ""),
            "name": str(raw.get("name") or raw.get("slug") or ""),
            "description": str(raw.get("description") or ""),
            "toolkit": str(toolkit or ""),
            "schema": raw.get("input_parameters") or raw.get("parameters") or {},
        }
    return {"slug": "", "name": "", "description": "", "toolkit": "", "schema": {}}


def _response(result: Any) -> dict[str, Any]:
    raw = _safe_value(result)
    if not isinstance(raw, dict):
        raw = {"data": raw}
    error = raw.get("error")
    return {
        "successful": not bool(error),
        "data": raw.get("data") or {},
        "error": str(error) if error else "",
        "log_id": str(raw.get("log_id") or raw.get("request_id") or ""),
    }


def _require_api_key(api_key: str) -> str:
    value = str(api_key or "").strip()
    if len(value) < 10 or value.lower() in {"placeholder", "your_composio_api_key"}:
        raise ComposioUploadError("Configure uma API key válida do Composio em Configuração API > API Keys Upload > Composio.")
    return value


def _require_user_id(user_id: str) -> str:
    value = str(user_id or "").strip()
    if not value:
        raise ComposioUploadError("Indique um Composio user ID estável antes de continuar.")
    return value


def _client(api_key: str, *, upload_dir: Path | None = None):
    try:
        from composio import Composio
    except ImportError as exc:
        raise ComposioUploadError("A SDK Python composio não está instalada. Execute a instalação do Thunderbolt novamente.") from exc
    kwargs: dict[str, Any] = {"api_key": _require_api_key(api_key), "allow_tracking": False}
    if upload_dir is not None:
        kwargs.update({
            "dangerously_allow_auto_upload_download_files": True,
            "file_upload_dirs": [str(upload_dir.resolve())],
        })
    return Composio(**kwargs)


def discover_tools(api_key: str, user_id: str, query: str, toolkit: str = "") -> list[dict[str, Any]]:
    client = _client(api_key)
    try:
        tools = client.tools.get(
            _require_user_id(user_id),
            search=(query or "upload a video file").strip(),
            toolkits=[toolkit.strip()] if toolkit.strip() else None,
            limit=10,
        )
        return [item for item in (_tool_item(tool) for tool in tools) if item.get("slug")]
    except ComposioUploadError:
        raise
    except Exception as exc:
        raise ComposioUploadError(f"Não foi possível descobrir ferramentas Composio: {type(exc).__name__}: {exc}") from exc


def authorize_toolkit(api_key: str, user_id: str, toolkit: str) -> dict[str, Any]:
    toolkit = str(toolkit or "").strip()
    if not toolkit:
        raise ComposioUploadError("Seleccione uma ferramenta descoberta para saber qual toolkit deve ser autorizado.")
    client = _client(api_key)
    try:
        request = client.create(user_id=_require_user_id(user_id)).authorize(toolkit)
        return {"connected_account_id": str(getattr(request, "id", "") or ""), "redirect_url": str(getattr(request, "redirect_url", "") or "")}
    except ComposioUploadError:
        raise
    except Exception as exc:
        raise ComposioUploadError(f"Não foi possível criar o Connect Link do Composio: {type(exc).__name__}: {exc}") from exc


def parse_arguments(arguments_json: str) -> dict[str, Any]:
    try:
        parsed = json.loads(arguments_json or "{}")
    except json.JSONDecodeError as exc:
        raise ComposioUploadError(f"Os argumentos da ferramenta não são JSON válido: {exc.msg}.") from exc
    if not isinstance(parsed, dict):
        raise ComposioUploadError("Os argumentos da ferramenta devem ser um objecto JSON.")
    return parsed


def execute_upload(api_key: str, user_id: str, slug: str, video_path: str, file_field: str, arguments_json: str = "") -> dict[str, Any]:
    path = Path(str(video_path or "").strip()).expanduser()
    slug = str(slug or "").strip()
    file_field = str(file_field or "").strip()
    if not path.is_file():
        raise ComposioUploadError("O ficheiro de vídeo seleccionado não existe ou não é um ficheiro.")
    if path.stat().st_size <= 0:
        raise ComposioUploadError("O ficheiro de vídeo seleccionado está vazio.")
    if not slug:
        raise ComposioUploadError("Seleccione ou indique o slug de uma ferramenta Composio.")
    if not file_field:
        raise ComposioUploadError("Indique o campo de argumentos que recebe o ficheiro.")
    arguments = parse_arguments(arguments_json)
    if file_field in arguments and arguments[file_field] not in (None, "", str(path)):
        raise ComposioUploadError(f"O campo `{file_field}` já contém um valor. Remova-o antes de injectar o vídeo.")
    arguments[file_field] = str(path.resolve())
    client = _client(api_key, upload_dir=path.parent)
    try:
        result = client.tools.execute(
            slug,
            arguments=arguments,
            user_id=_require_user_id(user_id),
            version="latest",
            dangerously_skip_version_check=True,
        )
        return _response(result)
    except ComposioUploadError:
        raise
    except Exception as exc:
        safe_message = str(exc).replace(str(api_key), "[REDACTED]")
        raise ComposioUploadError(f"A ferramenta Composio falhou: {type(exc).__name__}: {safe_message}") from exc


def test_configuration(api_key: str, user_id: str) -> dict[str, Any]:
    tools = discover_tools(api_key, user_id, "upload a video file")
    return {"successful": True, "data": {"tools": tools}, "error": "", "log_id": ""}
