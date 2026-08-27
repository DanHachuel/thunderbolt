"""Domínio, storage e adapters de dados para AI Influencers.

O módulo mantém a UI independente do backend. SQLite é totalmente local; Supabase
usa a Data API/Storage quando configurado. Nenhuma credencial é incluída em
registos, respostas de diagnóstico ou artefactos persistidos.
"""

from __future__ import annotations

import hashlib
import json
import mimetypes
import re
import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Mapping

from .storage import ROOT, STORAGE

BACKEND_OPTIONS = ("Supabase", "SQLite")
STANDALONE_CONTENT_INFLUENCER_ID = "__standalone_ai_content__"
IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".gif"}
DOCUMENT_EXTENSIONS = {".md", ".json"}
ASSET_EXTENSIONS = IMAGE_EXTENSIONS | DOCUMENT_EXTENSIONS
MAX_ASSET_BYTES = 25 * 1024 * 1024

SQLITE_SCHEMA = """
PRAGMA foreign_keys = ON;
CREATE TABLE IF NOT EXISTS influencers (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    bio TEXT NOT NULL DEFAULT '',
    instagram_business_id TEXT NOT NULL DEFAULT '',
    language TEXT NOT NULL DEFAULT '',
    profile_json TEXT NOT NULL DEFAULT '{}',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS influencer_assets (
    id TEXT PRIMARY KEY,
    influencer_id TEXT NOT NULL REFERENCES influencers(id) ON DELETE CASCADE,
    asset_type TEXT NOT NULL CHECK(asset_type IN ('image', 'document')),
    original_name TEXT NOT NULL,
    stored_path TEXT NOT NULL,
    public_url TEXT NOT NULL DEFAULT '',
    mime_type TEXT NOT NULL DEFAULT 'application/octet-stream',
    size_bytes INTEGER NOT NULL DEFAULT 0,
    sha256 TEXT NOT NULL,
    document_json TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL,
    UNIQUE(influencer_id, sha256)
);
CREATE INDEX IF NOT EXISTS idx_influencer_assets_influencer ON influencer_assets(influencer_id, created_at);
CREATE TABLE IF NOT EXISTS influencer_weekly_plans (
    id TEXT PRIMARY KEY,
    influencer_id TEXT NOT NULL REFERENCES influencers(id) ON DELETE CASCADE,
    week TEXT NOT NULL,
    plan TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    UNIQUE(influencer_id, week)
);
CREATE TABLE IF NOT EXISTS influencer_content (
    id TEXT PRIMARY KEY,
    influencer_id TEXT NOT NULL REFERENCES influencers(id) ON DELETE CASCADE,
    content_type TEXT NOT NULL CHECK(content_type IN ('image', 'video')),
    prompt TEXT NOT NULL DEFAULT '',
    caption TEXT NOT NULL DEFAULT '',
    provider TEXT NOT NULL DEFAULT '',
    model TEXT NOT NULL DEFAULT '',
    platform TEXT NOT NULL DEFAULT '',
    state TEXT NOT NULL DEFAULT 'queued',
    artifact_path TEXT NOT NULL DEFAULT '',
    provider_request_id TEXT NOT NULL DEFAULT '',
    error TEXT NOT NULL DEFAULT '',
    metadata_json TEXT NOT NULL DEFAULT '{}',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_influencer_content_influencer ON influencer_content(influencer_id, created_at);
CREATE INDEX IF NOT EXISTS idx_influencer_content_state ON influencer_content(state, updated_at);
"""


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _safe_filename(value: Any, fallback: str = "asset") -> str:
    name = Path(str(value or "")).name.strip()
    name = re.sub(r"[^A-Za-z0-9._-]+", "-", name).strip(".-")
    return name or fallback


def _safe_id(value: Any) -> str:
    clean = re.sub(r"[^A-Za-z0-9_-]+", "-", str(value or "")).strip("-")
    return clean or uuid.uuid4().hex


def _json_text(value: Any, default: str = "{}") -> str:
    if isinstance(value, str):
        return value
    try:
        return json.dumps(value if value is not None else {}, ensure_ascii=False)
    except (TypeError, ValueError):
        return default


def _json_value(value: Any) -> Any:
    if not isinstance(value, str):
        return value if value is not None else {}
    try:
        return json.loads(value) if value.strip() else {}
    except json.JSONDecodeError:
        return {}


def parse_document(name: str, content: bytes) -> dict[str, Any]:
    """Validate and parse a supported Markdown/JSON asset for preview/metadata."""
    suffix = Path(name).suffix.lower()
    if suffix not in DOCUMENT_EXTENSIONS:
        raise ValueError("O documento deve ser Markdown (.md) ou JSON (.json).")
    try:
        text = content.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise ValueError("O documento deve estar codificado em UTF-8.") from exc
    if not text.strip():
        raise ValueError("O documento não pode ficar vazio.")
    if suffix == ".json":
        try:
            parsed = json.loads(text)
        except json.JSONDecodeError as exc:
            raise ValueError(f"JSON inválido: {exc.msg}.") from exc
        return {"format": "json", "value": parsed, "text": text}
    return {"format": "markdown", "value": text, "text": text}


def validate_asset(name: str, content: bytes) -> dict[str, Any]:
    if not content:
        raise ValueError("O ficheiro enviado está vazio.")
    if len(content) > MAX_ASSET_BYTES:
        raise ValueError("Cada asset de personagem pode ter no máximo 25 MB.")
    safe_name = _safe_filename(name)
    suffix = Path(safe_name).suffix.lower()
    if suffix not in ASSET_EXTENSIONS:
        raise ValueError("Formato não suportado. Use imagens ou ficheiros .md/.json.")
    asset_type = "image" if suffix in IMAGE_EXTENSIONS else "document"
    document = parse_document(safe_name, content) if asset_type == "document" else None
    mime = mimetypes.guess_type(safe_name)[0] or ("image/jpeg" if asset_type == "image" else "text/plain")
    return {
        "original_name": safe_name,
        "asset_type": asset_type,
        "mime_type": mime,
        "size_bytes": len(content),
        "sha256": hashlib.sha256(content).hexdigest(),
        "document": document,
    }


def _row_to_dict(row: Any) -> dict[str, Any]:
    if isinstance(row, sqlite3.Row):
        return dict(row)
    if isinstance(row, Mapping):
        return dict(row)
    return {}


def _normalise_influencer(record: Mapping[str, Any]) -> dict[str, Any]:
    now = _now()
    return {
        "id": str(record.get("id") or f"influencer_{uuid.uuid4().hex[:12]}"),
        "name": str(record.get("name") or "").strip(),
        "bio": str(record.get("bio") or "").strip(),
        "instagram_business_id": str(record.get("instagram_business_id") or "").strip(),
        "language": str(record.get("language") or "").strip(),
        "profile_json": _json_text(record.get("profile_json") or record.get("profile") or {}),
        "created_at": str(record.get("created_at") or now),
        "updated_at": str(record.get("updated_at") or now),
    }


def _normalise_content(record: Mapping[str, Any]) -> dict[str, Any]:
    now = _now()
    content_type = str(record.get("content_type") or "image").strip().lower()
    if content_type not in {"image", "video"}:
        raise ValueError("Tipo de conteúdo inválido.")
    state = str(record.get("state") or "queued").strip().lower()
    if state not in {"queued", "running", "completed", "failed", "cancelled", "blocked"}:
        raise ValueError("Estado de conteúdo inválido.")
    return {
        "id": str(record.get("id") or f"content_{uuid.uuid4().hex[:12]}"),
        "influencer_id": str(record.get("influencer_id") or "").strip(),
        "content_type": content_type,
        "prompt": str(record.get("prompt") or "").strip(),
        "caption": str(record.get("caption") or "").strip(),
        "provider": str(record.get("provider") or "").strip(),
        "model": str(record.get("model") or "").strip(),
        "platform": str(record.get("platform") or "").strip(),
        "state": state,
        "artifact_path": str(record.get("artifact_path") or "").strip(),
        "provider_request_id": str(record.get("provider_request_id") or "").strip(),
        "error": str(record.get("error") or "").strip(),
        "metadata_json": _json_text(record.get("metadata_json") or record.get("metadata") or {}),
        "created_at": str(record.get("created_at") or now),
        "updated_at": str(record.get("updated_at") or now),
    }


class InfluencerBackendError(RuntimeError):
    """Raised when the selected database backend is unavailable or misconfigured."""


def _resolve_sqlite_path(path: str | Path | None = None) -> Path:
    raw_path = Path(path or (STORAGE / "state" / "ai_influencers.db")).expanduser()
    if raw_path.is_absolute():
        return raw_path.resolve()
    parts = raw_path.parts
    if parts and parts[0].casefold() == "storage":
        raw_path = Path(*parts[1:]) if len(parts) > 1 else Path("state") / "ai_influencers.db"
    return (STORAGE / raw_path).resolve()


class SQLiteInfluencerRepository:
    backend = "SQLite"

    def __init__(self, path: str | Path | None = None):
        self.path = _resolve_sqlite_path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def ensure_schema(self) -> None:
        with sqlite3.connect(self.path) as connection:
            connection.executescript(SQLITE_SCHEMA)
            connection.commit()

    def test_connection(self) -> dict[str, Any]:
        try:
            self.ensure_schema()
            with sqlite3.connect(self.path) as connection:
                connection.execute("SELECT 1").fetchone()
            return {"ok": True, "status": "success", "message": "SQLite disponível e schema verificado."}
        except sqlite3.Error:
            return {"ok": False, "status": "error", "message": "Não foi possível abrir o ficheiro SQLite."}

    def _connect(self) -> sqlite3.Connection:
        self.ensure_schema()
        connection = sqlite3.connect(self.path)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        return connection

    def list_influencers(self) -> list[dict[str, Any]]:
        with self._connect() as connection:
            rows = connection.execute("SELECT * FROM influencers ORDER BY updated_at DESC, name ASC").fetchall()
        return [_row_to_dict(row) for row in rows]

    def get_influencer(self, influencer_id: str) -> dict[str, Any] | None:
        with self._connect() as connection:
            row = connection.execute("SELECT * FROM influencers WHERE id = ?", (str(influencer_id),)).fetchone()
        return _row_to_dict(row) if row else None

    def create_influencer(self, record: Mapping[str, Any]) -> dict[str, Any]:
        item = _normalise_influencer(record)
        if not item["name"]:
            raise ValueError("Informe o nome do personagem.")
        with self._connect() as connection:
            connection.execute(
                "INSERT INTO influencers (id, name, bio, instagram_business_id, language, profile_json, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                tuple(item[key] for key in ("id", "name", "bio", "instagram_business_id", "language", "profile_json", "created_at", "updated_at")),
            )
            connection.commit()
        return item

    def update_influencer(self, influencer_id: str, updates: Mapping[str, Any]) -> dict[str, Any] | None:
        existing = self.get_influencer(influencer_id)
        if not existing:
            return None
        item = _normalise_influencer({**existing, **dict(updates), "id": influencer_id, "created_at": existing.get("created_at")})
        if not item["name"]:
            raise ValueError("Informe o nome do personagem.")
        with self._connect() as connection:
            connection.execute(
                "UPDATE influencers SET name=?, bio=?, instagram_business_id=?, language=?, profile_json=?, updated_at=? WHERE id=?",
                (item["name"], item["bio"], item["instagram_business_id"], item["language"], item["profile_json"], item["updated_at"], str(influencer_id)),
            )
            connection.commit()
        return item

    def delete_influencer(self, influencer_id: str) -> bool:
        with self._connect() as connection:
            cursor = connection.execute("DELETE FROM influencers WHERE id = ?", (str(influencer_id),))
            connection.commit()
        return cursor.rowcount > 0

    def list_assets(self, influencer_id: str) -> list[dict[str, Any]]:
        with self._connect() as connection:
            rows = connection.execute("SELECT * FROM influencer_assets WHERE influencer_id = ? ORDER BY created_at ASC", (str(influencer_id),)).fetchall()
        return [_row_to_dict(row) for row in rows]

    def save_asset(self, influencer_id: str, name: str, content: bytes) -> dict[str, Any]:
        if not self.get_influencer(influencer_id):
            raise ValueError("Personagem não encontrado.")
        info = validate_asset(name, content)
        directory = STORAGE / "influencers" / _safe_id(influencer_id)
        directory.mkdir(parents=True, exist_ok=True)
        target = directory / f"{info['sha256'][:16]}-{info['original_name']}"
        if not target.exists():
            target.write_bytes(content)
        record = {
            "id": f"asset_{uuid.uuid4().hex[:12]}",
            "influencer_id": str(influencer_id),
            "asset_type": info["asset_type"],
            "original_name": info["original_name"],
            "stored_path": str(target),
            "public_url": "",
            "mime_type": info["mime_type"],
            "size_bytes": info["size_bytes"],
            "sha256": info["sha256"],
            "document_json": _json_text(info["document"]) if info["document"] else "",
            "created_at": _now(),
        }
        with self._connect() as connection:
            existing = connection.execute("SELECT * FROM influencer_assets WHERE influencer_id=? AND sha256=?", (record["influencer_id"], record["sha256"])).fetchone()
            if existing:
                return _row_to_dict(existing)
            connection.execute(
                "INSERT INTO influencer_assets (id, influencer_id, asset_type, original_name, stored_path, public_url, mime_type, size_bytes, sha256, document_json, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                tuple(record[key] for key in ("id", "influencer_id", "asset_type", "original_name", "stored_path", "public_url", "mime_type", "size_bytes", "sha256", "document_json", "created_at")),
            )
            connection.commit()
        return record

    def create_content(self, record: Mapping[str, Any]) -> dict[str, Any]:
        item = _normalise_content(record)
        if not item["influencer_id"]:
            raise ValueError("Seleccione um personagem.")
        if not self.get_influencer(item["influencer_id"]):
            raise ValueError("Personagem não encontrado.")
        with self._connect() as connection:
            connection.execute(
                "INSERT INTO influencer_content (id, influencer_id, content_type, prompt, caption, provider, model, platform, state, artifact_path, provider_request_id, error, metadata_json, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                tuple(item[key] for key in ("id", "influencer_id", "content_type", "prompt", "caption", "provider", "model", "platform", "state", "artifact_path", "provider_request_id", "error", "metadata_json", "created_at", "updated_at")),
            )
            connection.commit()
        return item

    def update_content(self, content_id: str, updates: Mapping[str, Any]) -> dict[str, Any] | None:
        with self._connect() as connection:
            row = connection.execute("SELECT * FROM influencer_content WHERE id = ?", (str(content_id),)).fetchone()
        if not row:
            return None
        item = _normalise_content({**_row_to_dict(row), **dict(updates), "id": content_id, "created_at": row["created_at"]})
        with self._connect() as connection:
            connection.execute(
                "UPDATE influencer_content SET state=?, artifact_path=?, provider_request_id=?, error=?, caption=?, metadata_json=?, updated_at=? WHERE id=?",
                (item["state"], item["artifact_path"], item["provider_request_id"], item["error"], item["caption"], item["metadata_json"], item["updated_at"], str(content_id)),
            )
            connection.commit()
        return item

    def list_content(self, influencer_id: str = "", *, limit: int = 100) -> list[dict[str, Any]]:
        limit = max(1, min(int(limit), 500))
        with self._connect() as connection:
            if influencer_id:
                rows = connection.execute("SELECT * FROM influencer_content WHERE influencer_id=? ORDER BY updated_at DESC LIMIT ?", (str(influencer_id), limit)).fetchall()
            else:
                rows = connection.execute("SELECT * FROM influencer_content ORDER BY updated_at DESC LIMIT ?", (limit,)).fetchall()
        return [_row_to_dict(row) for row in rows]


class SupabaseInfluencerRepository:
    backend = "Supabase"

    def __init__(self, url: str, key: str, bucket: str = "ai-influencers", client: Any | None = None):
        self.url = str(url or "").strip().rstrip("/")
        self.key = str(key or "").strip()
        self.bucket = str(bucket or "ai-influencers").strip() or "ai-influencers"
        if not self.url or not self.key:
            raise InfluencerBackendError("Supabase seleccionado sem credenciais completas; seleccione SQLite ou preencha as credenciais do Supabase.")
        if client is not None:
            self.client = client
            return
        try:
            from supabase import create_client
        except ImportError as exc:
            raise InfluencerBackendError("O pacote Python supabase não está instalado.") from exc
        self.client = create_client(self.url, self.key)

    @staticmethod
    def _data(response: Any) -> list[dict[str, Any]]:
        data = getattr(response, "data", None)
        if isinstance(data, list):
            return [dict(item) for item in data if isinstance(item, Mapping)]
        if isinstance(data, Mapping):
            return [dict(data)]
        return []

    def test_connection(self) -> dict[str, Any]:
        try:
            response = self.client.table("influencers").select("id").limit(1).execute()
            if getattr(response, "data", None) is None:
                return {"ok": False, "status": "error", "message": "Supabase respondeu sem dados; confirme o schema e as permissões."}
            return {"ok": True, "status": "success", "message": "Supabase disponível e tabela influencers acessível."}
        except Exception as exc:
            text = str(exc).lower()
            if "relation" in text or "does not exist" in text or "404" in text:
                message = "Supabase acessível, mas o schema AI Influencers ainda não foi aplicado."
            elif "401" in text or "403" in text or "permission" in text:
                message = "Supabase rejeitou a chave ou as permissões/RLS da tabela."
            else:
                message = "Não foi possível verificar o Supabase; confirme URL, chave, schema e rede."
            return {"ok": False, "status": "error", "message": message}

    def list_influencers(self) -> list[dict[str, Any]]:
        response = self.client.table("influencers").select("*").order("updated_at", desc=True).limit(500).execute()
        return self._data(response)

    def get_influencer(self, influencer_id: str) -> dict[str, Any] | None:
        response = self.client.table("influencers").select("*").eq("id", str(influencer_id)).limit(1).execute()
        rows = self._data(response)
        return rows[0] if rows else None

    def create_influencer(self, record: Mapping[str, Any]) -> dict[str, Any]:
        item = _normalise_influencer(record)
        if not item["name"]:
            raise ValueError("Informe o nome do personagem.")
        payload = {**item, "profile_json": _json_value(item["profile_json"])}
        rows = self._data(self.client.table("influencers").insert(payload).execute())
        return rows[0] if rows else item

    def update_influencer(self, influencer_id: str, updates: Mapping[str, Any]) -> dict[str, Any] | None:
        existing = self.get_influencer(influencer_id)
        if not existing:
            return None
        item = _normalise_influencer({**existing, **dict(updates), "id": influencer_id, "created_at": existing.get("created_at")})
        payload = {**item, "profile_json": _json_value(item["profile_json"])}
        rows = self._data(self.client.table("influencers").update(payload).eq("id", str(influencer_id)).execute())
        return rows[0] if rows else item

    def delete_influencer(self, influencer_id: str) -> bool:
        response = self.client.table("influencers").delete().eq("id", str(influencer_id)).execute()
        return bool(self._data(response)) or getattr(response, "data", None) == []

    def list_assets(self, influencer_id: str) -> list[dict[str, Any]]:
        response = self.client.table("influencer_assets").select("*").eq("influencer_id", str(influencer_id)).order("created_at").limit(500).execute()
        return self._data(response)

    def save_asset(self, influencer_id: str, name: str, content: bytes) -> dict[str, Any]:
        if not self.get_influencer(influencer_id):
            raise ValueError("Personagem não encontrado.")
        info = validate_asset(name, content)
        existing_response = self.client.table("influencer_assets").select("*").eq("influencer_id", str(influencer_id)).eq("sha256", info["sha256"]).limit(1).execute()
        existing_rows = self._data(existing_response)
        if existing_rows:
            return existing_rows[0]
        object_path = f"influencers/{_safe_id(influencer_id)}/{info['sha256'][:16]}-{info['original_name']}"
        public_url = ""
        try:
            bucket = self.client.storage.from_(self.bucket)
            try:
                bucket.upload(object_path, content, {"content-type": info["mime_type"], "upsert": "false"})
            except TypeError:
                bucket.upload(object_path, content)
            try:
                candidate_url = bucket.get_public_url(object_path)
                if isinstance(candidate_url, Mapping):
                    candidate_url = candidate_url.get("publicUrl") or candidate_url.get("public_url") or candidate_url.get("url")
                public_url = str(candidate_url or "").strip()
            except Exception:
                try:
                    signed = bucket.create_signed_url(object_path, 3600)
                    if isinstance(signed, Mapping):
                        public_url = str(signed.get("signedURL") or signed.get("signedUrl") or signed.get("signed_url") or "").strip()
                except Exception:
                    public_url = ""
        except Exception as exc:
            raise InfluencerBackendError("Não foi possível enviar o asset para o bucket Supabase configurado.") from exc
        record = {
            "id": f"asset_{uuid.uuid4().hex[:12]}",
            "influencer_id": str(influencer_id),
            "asset_type": info["asset_type"],
            "original_name": info["original_name"],
            "stored_path": object_path,
            "public_url": public_url,
            "mime_type": info["mime_type"],
            "size_bytes": info["size_bytes"],
            "sha256": info["sha256"],
            "document_json": _json_value(_json_text(info["document"])) if info["document"] else None,
            "created_at": _now(),
        }
        try:
            rows = self._data(self.client.table("influencer_assets").insert(record).execute())
        except Exception as exc:
            raise InfluencerBackendError("O asset foi enviado mas não pôde ser registado na tabela Supabase.") from exc
        return rows[0] if rows else record

    def create_content(self, record: Mapping[str, Any]) -> dict[str, Any]:
        item = _normalise_content(record)
        payload = {**item, "metadata_json": _json_value(item["metadata_json"])}
        rows = self._data(self.client.table("influencer_content").insert(payload).execute())
        return rows[0] if rows else item

    def update_content(self, content_id: str, updates: Mapping[str, Any]) -> dict[str, Any] | None:
        fields = dict(updates)
        if "metadata_json" in fields:
            fields["metadata_json"] = _json_value(fields["metadata_json"])
        fields["updated_at"] = _now()
        rows = self._data(self.client.table("influencer_content").update(fields).eq("id", str(content_id)).execute())
        return rows[0] if rows else None

    def list_content(self, influencer_id: str = "", *, limit: int = 100) -> list[dict[str, Any]]:
        query = self.client.table("influencer_content").select("*")
        if influencer_id:
            query = query.eq("influencer_id", str(influencer_id))
        response = query.order("updated_at", desc=True).limit(max(1, min(int(limit), 500))).execute()
        return self._data(response)


def ensure_standalone_content_owner(repository: Any) -> str:
    """Return a hidden owner row for AI content that has no character dependency."""
    existing = repository.get_influencer(STANDALONE_CONTENT_INFLUENCER_ID)
    if existing:
        return STANDALONE_CONTENT_INFLUENCER_ID
    repository.create_influencer(
        {
            "id": STANDALONE_CONTENT_INFLUENCER_ID,
            "name": "__Thunderbolt AI content__",
            "bio": "Internal owner for standalone Motion Control and UGC Products content.",
            "language": "",
        }
    )
    return STANDALONE_CONTENT_INFLUENCER_ID


def sqlite_path_from_settings(settings: Mapping[str, Any]) -> Path:
    raw = str(settings.get("influencer_sqlite_path") or "storage/state/ai_influencers.db").strip()
    return _resolve_sqlite_path(raw)


def backend_name(settings: Mapping[str, Any]) -> str:
    """Return the usable backend; an empty Supabase configuration never blocks local use."""
    value = str(settings.get("influencer_db_backend") or "").strip().casefold()
    if value == "sqlite":
        return "SQLite"
    if value == "supabase" and str(settings.get("influencer_supabase_url") or "").strip() and str(settings.get("influencer_supabase_key") or "").strip():
        return "Supabase"
    return "SQLite"


def get_repository(settings: Mapping[str, Any], *, client: Any | None = None) -> SQLiteInfluencerRepository | SupabaseInfluencerRepository:
    if backend_name(settings) == "SQLite":
        return SQLiteInfluencerRepository(sqlite_path_from_settings(settings))
    return SupabaseInfluencerRepository(settings.get("influencer_supabase_url", ""), settings.get("influencer_supabase_key", ""), settings.get("influencer_supabase_bucket", "ai-influencers"), client=client)


def test_backend(settings: Mapping[str, Any], *, client: Any | None = None) -> dict[str, Any]:
    try:
        return get_repository(settings, client=client).test_connection()
    except InfluencerBackendError as exc:
        return {"ok": False, "status": "missing", "message": str(exc)}
    except Exception:
        return {"ok": False, "status": "error", "message": "Não foi possível inicializar o backend AI Influencers."}


def backend_status(settings: Mapping[str, Any]) -> dict[str, Any]:
    backend = backend_name(settings)
    if backend == "SQLite":
        path = sqlite_path_from_settings(settings)
        return {"backend": backend, "configured": True, "target": str(path), "message": "SQLite local pronto para inicialização automática."}
    url = str(settings.get("influencer_supabase_url") or "").strip()
    key = str(settings.get("influencer_supabase_key") or "").strip()
    return {
        "backend": backend,
        "configured": bool(url and key),
        "target": url or "Project URL não configurado",
        "message": "Supabase configurado; confirme schema/RLS/bucket.",
    }


__all__ = [
    "ASSET_EXTENSIONS",
    "BACKEND_OPTIONS",
    "DOCUMENT_EXTENSIONS",
    "IMAGE_EXTENSIONS",
    "InfluencerBackendError",
    "STANDALONE_CONTENT_INFLUENCER_ID",
    "SQLiteInfluencerRepository",
    "SupabaseInfluencerRepository",
    "SQLITE_SCHEMA",
    "backend_name",
    "backend_status",
    "get_repository",
    "ensure_standalone_content_owner",
    "parse_document",
    "sqlite_path_from_settings",
    "test_backend",
    "validate_asset",
]
