from __future__ import annotations

import logging

from saturn_koma_watcher.config import WatcherConfig
from saturn_koma_watcher.models import Listing
from saturn_koma_watcher.sources.base import SourcePlugin

LOGGER = logging.getLogger(__name__)


class MercariSource(SourcePlugin):
    name = "mercari"

    def search(self, query: str, config: WatcherConfig) -> list[Listing]:
        LOGGER.warning(
            "[mercari] parser desactivado para '%s': Mercari JP depende de APIs y protección anti-scraping; "
            "se devuelve [] para evitar falsos positivos frágiles.",
            query,
        )
        return []
