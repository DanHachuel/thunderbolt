from __future__ import annotations

import io
import re
import shutil
from pathlib import Path
from typing import BinaryIO

import pandas as pd

from hermes_ui.storage import STORAGE

try:
    import kagglehub
except ImportError:  # pragma: no cover - exercised in installations before the extra dependency is installed
    kagglehub = None


DATA_DIR = STORAGE / "data" / "niches"
DEFAULT_DATASET_SLUG = "asaniczka/trending-youtube-videos-113-countries"
DEFAULT_DATASET_FILENAME = "trending_yt_videos_113_countries.csv"
DEFAULT_DATASET_PATH = DATA_DIR / DEFAULT_DATASET_FILENAME

REQUIRED_COLUMNS = (
    "title",
    "publish_date",
    "country",
    "view_count",
    "like_count",
    "comment_count",
)
OPTIONAL_COLUMNS = (
    "video_tags",
    "channel_name",
    "thumbnail_url",
    "video_id",
    "channel_id",
)


class DatasetError(RuntimeError):
    """Raised when a Niche Finder dataset cannot be read or validated."""


def ensure_data_dir() -> Path:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    (DATA_DIR / "uploads").mkdir(parents=True, exist_ok=True)
    return DATA_DIR


def _safe_filename(name: str) -> str:
    stem = re.sub(r"[^A-Za-z0-9._-]+", "-", Path(name or "dataset.csv").name).strip(".-")
    if not stem:
        stem = "dataset.csv"
    if not stem.lower().endswith(".csv"):
        stem += ".csv"
    return stem


def _find_csv(root: Path) -> Path | None:
    candidates = sorted(root.rglob("*.csv"))
    if not candidates:
        return None
    for candidate in candidates:
        if candidate.name.lower() == DEFAULT_DATASET_FILENAME.lower():
            return candidate
    return candidates[0]


def _copy_csv(source: Path, destination: Path) -> Path:
    destination.parent.mkdir(parents=True, exist_ok=True)
    if source.resolve() != destination.resolve():
        shutil.copy2(source, destination)
    return destination


def _download_with_kagglehub() -> Path | None:
    if kagglehub is None:
        return None
    data_dir = ensure_data_dir()
    try:
        downloaded = kagglehub.dataset_download(DEFAULT_DATASET_SLUG, output_dir=str(data_dir))
    except TypeError:
        downloaded = kagglehub.dataset_download(DEFAULT_DATASET_SLUG)
    except Exception as exc:  # pragma: no cover - depends on network/provider state
        raise DatasetError(f"O KaggleHub não conseguiu descarregar o dataset: {exc}") from exc
    source = _find_csv(Path(downloaded))
    if source is None:
        raise DatasetError("O download KaggleHub terminou sem encontrar um ficheiro CSV.")
    return _copy_csv(source, DEFAULT_DATASET_PATH)


def download_kaggle_dataset() -> Path:
    """Download and cache the public Niche-Finder dataset in Thunderbolt storage."""
    ensure_data_dir()
    if DEFAULT_DATASET_PATH.exists() and DEFAULT_DATASET_PATH.stat().st_size > 0:
        return DEFAULT_DATASET_PATH
    if kagglehub is None:
        raise DatasetError("A dependência kagglehub não está instalada. Execute novamente a instalação do Thunderbolt.")
    downloaded = _download_with_kagglehub()
    if downloaded is None:
        raise DatasetError("O KaggleHub não devolveu um caminho de dataset válido.")
    return downloaded


def save_uploaded_csv(payload: bytes | BinaryIO, filename: str) -> Path:
    """Validate and persist an uploaded CSV under the user's local data directory."""
    ensure_data_dir()
    raw = payload.read() if hasattr(payload, "read") else payload
    if not isinstance(raw, (bytes, bytearray)) or not raw:
        raise DatasetError("O ficheiro CSV enviado está vazio.")
    try:
        frame = pd.read_csv(io.BytesIO(raw))
        validate_dataset(frame)
    except (OSError, UnicodeDecodeError, pd.errors.ParserError, pd.errors.EmptyDataError) as exc:
        raise DatasetError(f"Não foi possível ler o CSV enviado: {exc}") from exc
    destination = DATA_DIR / "uploads" / _safe_filename(filename)
    destination.write_bytes(raw)
    return destination


def validate_dataset(frame: pd.DataFrame) -> pd.DataFrame:
    """Validate the minimal schema and return a normalised copy."""
    if frame is None or frame.empty:
        raise DatasetError("O dataset não contém linhas.")
    cleaned = frame.copy()
    cleaned.columns = [str(column).strip() for column in cleaned.columns]
    missing = [column for column in REQUIRED_COLUMNS if column not in cleaned.columns]
    if missing:
        raise DatasetError("O CSV precisa das colunas: " + ", ".join(missing) + ".")
    if "video_tags" not in cleaned.columns:
        cleaned["video_tags"] = ""
    for column in ("view_count", "like_count", "comment_count"):
        cleaned[column] = pd.to_numeric(cleaned[column], errors="coerce")
    cleaned["publish_date"] = pd.to_datetime(cleaned["publish_date"], errors="coerce").dt.strftime("%Y-%m-%d")
    cleaned["country"] = cleaned["country"].astype("string").str.strip()
    cleaned["title"] = cleaned["title"].astype("string").fillna("").str.strip()
    cleaned = cleaned.dropna(subset=["publish_date", "view_count", "like_count", "comment_count"])
    cleaned = cleaned[cleaned["title"] != ""].copy()
    if cleaned.empty:
        raise DatasetError("O dataset não contém linhas válidas depois da normalização.")
    return cleaned.reset_index(drop=True)


def load_dataframe(path: str | Path) -> pd.DataFrame:
    try:
        frame = pd.read_csv(path)
    except (OSError, UnicodeDecodeError, pd.errors.ParserError, pd.errors.EmptyDataError) as exc:
        raise DatasetError(f"Não foi possível ler o dataset: {exc}") from exc
    return validate_dataset(frame)


def list_cached_datasets() -> list[Path]:
    ensure_data_dir()
    return sorted(DATA_DIR.glob("**/*.csv"))
