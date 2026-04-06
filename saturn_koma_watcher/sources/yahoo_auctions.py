from __future__ import annotations

import logging

from saturn_koma_watcher.config import WatcherConfig
from saturn_koma_watcher.models import Listing
from saturn_koma_watcher.sources.base import SourcePlugin

LOGGER = logging.getLogger(__name__)


class YahooAuctionsSource(SourcePlugin):
    name = "yahoo_auctions"

    def search(self, query: str, config: WatcherConfig) -> list[Listing]:
        LOGGER.warning(
            "[yahoo_auctions] parser desactivado para '%s': Yahoo Auctions JP cambia estructura y anti-bot frecuentemente; "
            "se devuelve [] de forma segura.",
            query,
        )
        return []
