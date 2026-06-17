from __future__ import annotations

import os
import sys
from pathlib import Path


if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
    PROJECT_ROOT = Path(sys._MEIPASS)  # type: ignore[attr-defined]
else:
    PROJECT_ROOT = Path(__file__).resolve().parents[2]
ANALYSIS_DIR = PROJECT_ROOT / "analysis"
DOCS_DIR = PROJECT_ROOT / "docs"
REVIEW_SHAPE_DIR = ANALYSIS_DIR / "review_shape_20260527"
INTEGRATED_MAP_DIR = ANALYSIS_DIR / "integrated_evidence_map_20260527"
DETACHED_CORPUS_DIR = PROJECT_ROOT / "DevelopmentalCorpusArchive_20260526_122541"


def local_data_dir() -> Path:
    base = os.environ.get("SELENE_DATA_DIR")
    if base:
        return Path(base).expanduser().resolve()
    local = os.environ.get("LOCALAPPDATA")
    if local:
        return Path(local) / "Selene" / "data"
    return PROJECT_ROOT / ".selene_data"


def local_log_dir() -> Path:
    local = os.environ.get("LOCALAPPDATA")
    if local:
        return Path(local) / "Selene" / "logs"
    return PROJECT_ROOT / ".selene_logs"


def export_dir() -> Path:
    return local_data_dir() / "exports"


def default_db_path() -> Path:
    return local_data_dir() / "selene.sqlite3"
