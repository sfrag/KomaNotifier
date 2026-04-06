from __future__ import annotations

import logging

from saturn_koma_watcher.config import WatcherConfig
from saturn_koma_watcher.models import Listing
from saturn_koma_watcher.sources.base import SourcePlugin

LOGGER = logging.getLogger(__name__)


class MandarakeSource(SourcePlugin):
    name = "mandarake"

    def search(self, query: str, config: WatcherConfig) -> list[Listing]:
        LOGGER.warning(
            "[mandarake] parser desactivado para '%s': el HTML y filtros cambian con frecuencia y no hay contrato estable; "
            "se devuelve [] para priorizar robustez.",
            query,
        )
        return []
