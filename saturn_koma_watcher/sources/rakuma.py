from __future__ import annotations

import logging

from saturn_koma_watcher.config import WatcherConfig
from saturn_koma_watcher.models import Listing
from saturn_koma_watcher.sources.base import SourcePlugin

LOGGER = logging.getLogger(__name__)


class RakumaSource(SourcePlugin):
    name = "rakuma"

    def search(self, query: str, config: WatcherConfig) -> list[Listing]:
        LOGGER.warning(
            "[rakuma] parser desactivado para '%s': Rakuma renderiza datos de forma poco estable para scraping sin API oficial; "
            "se devuelve [] de forma segura.",
            query,
        )
        return []
