from __future__ import annotations

from saturn_koma_watcher.sources.base import SourcePlugin
from saturn_koma_watcher.sources.buyee import BuyeeSource
from saturn_koma_watcher.sources.mandarake import MandarakeSource
from saturn_koma_watcher.sources.mercari import MercariSource
from saturn_koma_watcher.sources.rakuma import RakumaSource
from saturn_koma_watcher.sources.yahoo_auctions import YahooAuctionsSource

SOURCE_REGISTRY: dict[str, type[SourcePlugin]] = {
    "buyee": BuyeeSource,
    "yahoo_auctions": YahooAuctionsSource,
    "mercari": MercariSource,
    "rakuma": RakumaSource,
    "mandarake": MandarakeSource,
}


def build_sources(enabled_sources: list[str]) -> list[SourcePlugin]:
    sources: list[SourcePlugin] = []
    for name in enabled_sources:
        cls = SOURCE_REGISTRY.get(name)
        if cls:
            sources.append(cls())
    return sources
