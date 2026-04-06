from __future__ import annotations

import argparse
import logging
from pathlib import Path

from saturn_koma_watcher.config import load_config
from saturn_koma_watcher.notifier import Notifier
from saturn_koma_watcher.scoring import score_texts
from saturn_koma_watcher.sources import SOURCE_REGISTRY, build_sources
from saturn_koma_watcher.storage import listing_is_seen, load_seen_ids, save_seen_ids
from saturn_koma_watcher.utils import setup_logging, stable_id_from_url

LOGGER = logging.getLogger("watcher")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Monitoriza anuncios para Saturn Koma")
    parser.add_argument("--config", default="config.json", help="Ruta al archivo de configuración JSON")
    parser.add_argument("--dry-run", action="store_true", help="No envía notificaciones ni guarda estado")
    parser.add_argument("--verbose", action="store_true", help="Activa logs en nivel DEBUG")
    return parser.parse_args()


def run() -> int:
    args = parse_args()
    setup_logging(verbose=args.verbose)

    config_path = args.config if Path(args.config).exists() else None
    config = load_config(config_path)

    if not config.queries:
        LOGGER.error("No hay queries configuradas")
        return 2

    enabled_names = [name for name in config.enabled_sources if name in SOURCE_REGISTRY]
    unknown_sources = [name for name in config.enabled_sources if name not in SOURCE_REGISTRY]
    for unknown in unknown_sources:
        LOGGER.warning("Fuente desconocida en configuración: %s", unknown)

    sources = build_sources(enabled_names)
    if not sources:
        LOGGER.error("No hay fuentes activas válidas")
        return 2

    state_path = Path("state.json")
    seen_ids = load_seen_ids(state_path)
    seen_before = set(seen_ids)

    notifier = Notifier(config)

    LOGGER.info("Inicio de ejecución. Fuentes activas: %s", ", ".join([s.name for s in sources]))
    LOGGER.info("Queries activas: %d | min_score=%d", len(config.queries), config.min_score)

    found_total = 0
    notified_total = 0
    processed_ids: set[str] = set()

    for source in sources:
        for query in config.queries:
            LOGGER.debug("Buscando en %s -> %s", source.name, query)
            try:
                listings = source.search(query, config)
            except Exception as exc:
                LOGGER.exception("Error inesperado en fuente %s para query '%s': %s", source.name, query, exc)
                continue

            for listing in listings:
                identifier = listing.listing_id.strip() or stable_id_from_url(listing.url)
                listing.listing_id = identifier
                if identifier in processed_ids:
                    LOGGER.debug("Duplicado entre queries omitido: %s", listing.url)
                    continue
                processed_ids.add(identifier)

                listing.score, listing.matched_terms = score_texts(listing.title, listing.description)
                found_total += 1

                if listing.score > 0:
                    LOGGER.info(
                        "Resultado [%s] score=%d terms=%s title=%s",
                        listing.source,
                        listing.score,
                        ",".join(listing.matched_terms) if listing.matched_terms else "-",
                        listing.title,
                    )
                elif args.verbose:
                    LOGGER.debug("Resultado descartado score=0 [%s] %s", listing.source, listing.title)

                if listing.score < config.min_score:
                    continue

                if listing_is_seen(identifier, seen_ids):
                    LOGGER.debug("Duplicado omitido: %s", listing.url)
                    continue

                notifier.notify(listing, dry_run=args.dry_run)
                notified_total += 1

                if not args.dry_run:
                    seen_ids.add(identifier)

    if not args.dry_run and seen_ids != seen_before:
        save_seen_ids(state_path, seen_ids)
        LOGGER.info("state.json actualizado con %d IDs", len(seen_ids))
    elif args.dry_run:
        LOGGER.info("Modo dry-run: estado no persistido")
    else:
        LOGGER.info("Sin cambios en state.json")

    LOGGER.info("Fin. encontrados=%d notificados=%d", found_total, notified_total)
    return 0


if __name__ == "__main__":
    raise SystemExit(run())
