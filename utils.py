from __future__ import annotations

import json
import logging
from hashlib import sha256
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Any

from config import LOG_DIR


def setup_logging(log_file: Path) -> logging.Logger:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    logger = logging.getLogger("tech_radar")
    logger.setLevel(logging.INFO)

    if logger.handlers:
        return logger

    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    file_handler = RotatingFileHandler(log_file, maxBytes=1_000_000, backupCount=3, encoding="utf-8")
    file_handler.setFormatter(formatter)

    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.addHandler(stream_handler)
    return logger


def normalize_text(value: str) -> str:
    return " ".join((value or "").split()).strip()


def safe_trim(text: str, limit: int) -> str:
    cleaned = normalize_text(text)
    if len(cleaned) <= limit:
        return cleaned
    return cleaned[: limit - 3].rstrip() + "..."


def make_content_hash(*parts: str) -> str:
    normalized = "||".join(normalize_text(part) for part in parts if part)
    return sha256(normalized.encode("utf-8")).hexdigest()


def save_json(path: Path, data: list[dict[str, Any]], logger) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
        logger.info("JSON salvo em %s", path)
    except Exception as exc:
        logger.exception("Falha ao salvar JSON em %s: %s", path, exc)
