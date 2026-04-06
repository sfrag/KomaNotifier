from __future__ import annotations

import hashlib
import logging
import re
import unicodedata


def setup_logging(verbose: bool = False) -> None:
    """Configura logging en consola."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
    )


def normalize_text(text: str) -> str:
    """Normaliza texto para mejorar coincidencias de términos."""
    normalized = unicodedata.normalize("NFKC", text or "")
    normalized = re.sub(r"\s+", " ", normalized)
    return normalized.strip()


def stable_id_from_url(url: str) -> str:
    """Genera un ID estable cuando la fuente no provee listing_id."""
    digest = hashlib.sha256(url.encode("utf-8")).hexdigest()
    return digest[:20]
