from __future__ import annotations

import logging
from abc import ABC, abstractmethod

import requests

from saturn_koma_watcher.config import WatcherConfig
from saturn_koma_watcher.models import Listing

LOGGER = logging.getLogger(__name__)


class SourcePlugin(ABC):
    """Contrato base para plugins de fuentes."""

    name: str

    @abstractmethod
    def search(self, query: str, config: WatcherConfig) -> list[Listing]:
        """Busca anuncios para una query y devuelve resultados normalizados."""

    def _http_get(self, url: str, config: WatcherConfig, params: dict[str, str] | None = None) -> requests.Response:
        headers = {
            "User-Agent": config.user_agent,
            "Accept-Language": "ja,en-US;q=0.9,en;q=0.8",
        }
        response = requests.get(
            url,
            headers=headers,
            params=params,
            timeout=config.request_timeout,
        )
        response.raise_for_status()
        return response
