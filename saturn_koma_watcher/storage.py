from __future__ import annotations

import json
import logging
from pathlib import Path

LOGGER = logging.getLogger(__name__)


def load_seen_ids(state_path: Path) -> set[str]:
    """Carga IDs ya vistos desde state.json."""
    if not state_path.exists():
        return set()

    try:
        data = json.loads(state_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        LOGGER.warning("state.json inválido; se reinicia estado vacío")
        return set()

    if isinstance(data, dict):
        seen_ids = data.get("seen_ids", [])
    else:
        LOGGER.warning("Formato de state.json no soportado; se usa estado vacío")
        return set()

    return {str(item) for item in seen_ids}


def save_seen_ids(state_path: Path, seen_ids: set[str]) -> None:
    """Guarda IDs vistos en state.json, ordenados para diffs estables."""
    payload = {
        "seen_ids": sorted(seen_ids),
    }
    state_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def listing_is_seen(listing_id: str, seen_ids: set[str]) -> bool:
    return listing_id in seen_ids
