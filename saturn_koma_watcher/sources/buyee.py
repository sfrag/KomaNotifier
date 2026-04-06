from __future__ import annotations

import json
import logging
import re
from urllib.parse import quote, urljoin

import requests
from bs4 import BeautifulSoup

from saturn_koma_watcher.config import WatcherConfig
from saturn_koma_watcher.models import Listing
from saturn_koma_watcher.sources.base import SourcePlugin
from saturn_koma_watcher.utils import stable_id_from_url

LOGGER = logging.getLogger(__name__)


class BuyeeSource(SourcePlugin):
    """Plugin Buyee (prioritario). Intenta JSON-LD y fallback HTML."""

    name = "buyee"
    _BASE_URL = "https://buyee.jp"
    _MARKET_URL_TOKENS = (
        "/item/yahoo/",
        "/item/mercari/",
        "/item/rakuma/",
        "/item/jdirectitems/",
    )
    _NOISE_URL_TOKENS = (
        "/item/search/",
        "/item/category/",
        "/help/",
        "/guide/",
    )

    def search(self, query: str, config: WatcherConfig) -> list[Listing]:
        encoded = quote(query)
        url = f"{self._BASE_URL}/item/search/query/{encoded}"

        try:
            response = self._http_get(url, config)
        except requests.HTTPError as exc:
            status_code = exc.response.status_code if exc.response is not None else None
            if status_code == 404:
                LOGGER.info("[buyee] sin resultados (404) para query '%s'", query)
                return []
            LOGGER.warning("[buyee] fallo HTTP para query '%s': %s", query, exc)
            return []
        except Exception as exc:
            LOGGER.warning("[buyee] fallo HTTP para query '%s': %s", query, exc)
            return []

        soup = BeautifulSoup(response.text, "html.parser")
        listings = self._parse_json_ld(soup)
        if listings:
            return listings

        # Fallback defensivo para HTML cuando JSON-LD no viene disponible.
        fallback = self._parse_html_fallback(soup)
        if not fallback:
            LOGGER.warning(
                "[buyee] no se pudieron extraer resultados para '%s' (estructura no fiable)",
                query,
            )
        return fallback

    def _parse_json_ld(self, soup: BeautifulSoup) -> list[Listing]:
        listings: list[Listing] = []
        seen_urls: set[str] = set()

        for script in soup.find_all("script", attrs={"type": "application/ld+json"}):
            raw = (script.string or "").strip()
            if not raw:
                continue

            try:
                payload = json.loads(raw)
            except json.JSONDecodeError:
                continue

            for item in self._iter_item_list(payload):
                if not isinstance(item, dict):
                    continue

                data = item.get("item", item)
                if not isinstance(data, dict):
                    continue

                url = str(data.get("url", "")).strip()
                title = str(data.get("name", "")).strip()
                if not url or not title:
                    continue

                absolute_url = url if url.startswith("http") else urljoin(self._BASE_URL, url)
                if not self._is_probable_listing_url(absolute_url):
                    continue
                if absolute_url in seen_urls:
                    continue
                seen_urls.add(absolute_url)

                offers = data.get("offers", {}) if isinstance(data.get("offers"), dict) else {}
                price = str(offers.get("price", "")).strip()
                image = data.get("image", [])
                image_urls = [str(image)] if isinstance(image, str) else [str(x) for x in image if x]

                listing_id = self._extract_listing_id(absolute_url)
                listings.append(
                    Listing(
                        source=self.name,
                        title=title,
                        url=absolute_url,
                        price=price,
                        listing_id=listing_id,
                        image_urls=image_urls,
                        raw_metadata={"offers": offers},
                    )
                )

        return listings

    def _iter_item_list(self, payload: object) -> list[dict]:
        if isinstance(payload, dict):
            if isinstance(payload.get("itemListElement"), list):
                return [x for x in payload["itemListElement"] if isinstance(x, dict)]
            if isinstance(payload.get("@graph"), list):
                out: list[dict] = []
                for node in payload["@graph"]:
                    if isinstance(node, dict) and isinstance(node.get("itemListElement"), list):
                        out.extend([x for x in node["itemListElement"] if isinstance(x, dict)])
                return out
        if isinstance(payload, list):
            out: list[dict] = []
            for node in payload:
                out.extend(self._iter_item_list(node))
            return out
        return []

    def _parse_html_fallback(self, soup: BeautifulSoup) -> list[Listing]:
        listings: list[Listing] = []
        seen_urls: set[str] = set()

        for anchor in soup.select("a[href]"):
            href = str(anchor.get("href", "")).strip()
            if "/item/" not in href:
                continue

            title = anchor.get_text(" ", strip=True)
            if len(title) < 6:
                continue

            absolute_url = href if href.startswith("http") else urljoin(self._BASE_URL, href)
            if not self._is_probable_listing_url(absolute_url):
                continue
            if absolute_url in seen_urls:
                continue
            seen_urls.add(absolute_url)

            context_text = anchor.parent.get_text(" ", strip=True) if anchor.parent else ""
            price_match = re.search(r"([¥￥]\s?[\d,]+)", context_text)
            price = price_match.group(1) if price_match else ""

            image_urls: list[str] = []
            if anchor.find("img") and anchor.find("img").get("src"):
                src = str(anchor.find("img").get("src"))
                image_urls.append(src if src.startswith("http") else urljoin(self._BASE_URL, src))

            listings.append(
                Listing(
                    source=self.name,
                    title=title,
                    url=absolute_url,
                    price=price,
                    listing_id=self._extract_listing_id(absolute_url),
                    image_urls=image_urls,
                    raw_metadata={"fallback": True},
                )
            )

        return listings

    def _extract_listing_id(self, url: str) -> str:
        match = re.search(r"/item/[^/]+/(?:auction|item)?/?([^/?#]+)", url)
        if match and match.group(1):
            return match.group(1)
        return stable_id_from_url(url)

    def _is_probable_listing_url(self, url: str) -> bool:
        lower = url.lower()
        if any(token in lower for token in self._NOISE_URL_TOKENS):
            return False
        return any(token in lower for token in self._MARKET_URL_TOKENS)
