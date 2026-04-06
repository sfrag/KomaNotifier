from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class Listing:
    """Representa un anuncio detectado en una fuente."""

    source: str
    title: str
    url: str
    price: str = ""
    description: str = ""
    image_urls: list[str] = field(default_factory=list)
    listing_id: str = ""
    score: int = 0
    matched_terms: list[str] = field(default_factory=list)
    raw_metadata: dict[str, Any] = field(default_factory=dict)
