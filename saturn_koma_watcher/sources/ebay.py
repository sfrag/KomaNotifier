from __future__ import annotations

import logging
import re
from urllib.parse import quote_plus

from bs4 import BeautifulSoup

from saturn_koma_watcher.config import WatcherConfig
from saturn_koma_watcher.models import Listing
from saturn_koma_watcher.sources.base import SourcePlugin
from saturn_koma_watcher.utils import stable_id_from_url

LOGGER = logging.getLogger(__name__)


class EbaySource(SourcePlugin):
    """Plugin de eBay (global). Parser defensivo con filtros anti-ruido."""

    name = "ebay"
    _BASE_URL = "https://www.ebay.com/sch/i.html"

    def search(self, query: str, config: WatcherConfig) -> list[Listing]:
        url = f"{self._BASE_URL}?_nkw={quote_plus(query)}&_sacat=0"

        try:
            response = self._http_get(url, config)
        except Exception as exc:
            LOGGER.warning("[ebay] fallo HTTP para query '%s': %s", query, exc)
            return []

        soup = BeautifulSoup(response.text, "html.parser")
        listings: list[Listing] = []
        seen_urls: set[str] = set()

        for card in soup.select("li.s-item"):
            link_tag = card.select_one("a.s-item__link")
            title_tag = card.select_one("h3.s-item__title")
            if not link_tag or not title_tag:
                continue

            url_candidate = str(link_tag.get("href", "")).strip()
            title = title_tag.get_text(" ", strip=True)
            if not url_candidate or not title:
                continue

            # eBay añade entradas de navegación/promoción sin item real.
            if "shop on ebay" in title.lower():
                continue
            if "/itm/" not in url_candidate:
                continue

            # Limpia tracking params para mejorar deduplicación.
            clean_url = url_candidate.split("?", 1)[0]
            if clean_url in seen_urls:
                continue
            seen_urls.add(clean_url)

            price_tag = card.select_one(".s-item__price")
            subtitle_tag = card.select_one(".s-item__subtitle")
            image_tag = card.select_one("img.s-item__image-img")

            price = price_tag.get_text(" ", strip=True) if price_tag else ""
            description = subtitle_tag.get_text(" ", strip=True) if subtitle_tag else ""
            image_urls = [str(image_tag.get("src", "")).strip()] if image_tag else []
            image_urls = [x for x in image_urls if x and x.startswith("http")]

            listings.append(
                Listing(
                    source=self.name,
                    title=title,
                    url=clean_url,
                    price=price,
                    description=description,
                    image_urls=image_urls,
                    listing_id=self._extract_listing_id(clean_url),
                    raw_metadata={"query": query},
                )
            )

        if not listings:
            LOGGER.info("[ebay] sin resultados parseables para query '%s'", query)
        return listings

    def _extract_listing_id(self, url: str) -> str:
        match = re.search(r"/itm/(?:[^/]+/)?(\d+)", url)
        if match and match.group(1):
            return match.group(1)
        return stable_id_from_url(url)

