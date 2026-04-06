from __future__ import annotations

import json
import logging
import smtplib
from email.message import EmailMessage

import requests

from saturn_koma_watcher.config import WatcherConfig
from saturn_koma_watcher.models import Listing

LOGGER = logging.getLogger(__name__)


class Notifier:
    def __init__(self, config: WatcherConfig) -> None:
        self.config = config

    def notify(self, listing: Listing, dry_run: bool = False) -> None:
        if dry_run:
            LOGGER.info("[dry-run] Notificación omitida para: %s", listing.title)
            return

        self._notify_discord(listing)
        self._notify_email(listing)

    def _build_message_text(self, listing: Listing) -> str:
        terms = ", ".join(listing.matched_terms) if listing.matched_terms else "(sin términos)"
        lines = [
            f"Fuente: {listing.source}",
            f"Título: {listing.title}",
            f"Score: {listing.score}",
            f"Términos: {terms}",
            f"URL: {listing.url}",
        ]
        if listing.price:
            lines.insert(2, f"Precio: {listing.price}")
        return "\n".join(lines)

    def _notify_discord(self, listing: Listing) -> None:
        webhook = self.config.discord_webhook_url.strip()
        if not webhook:
            LOGGER.info("Discord no configurado; se omite notificación")
            return

        content = self._build_message_text(listing)
        payload = {
            "content": (
                "[ALERTA] Posible coincidencia de Saturn Koma\n"
                f"Fuente: {listing.source}\n"
                f"Titulo: {listing.title}\n"
                f"Score: {listing.score}\n"
                f"Terminos: {', '.join(listing.matched_terms) if listing.matched_terms else '-'}\n"
                f"Enlace: {listing.url}\n\n"
                f"```\n{content}\n```"
            ),
        }

        try:
            response = requests.post(
                webhook,
                data=json.dumps(payload),
                headers={"Content-Type": "application/json"},
                timeout=self.config.request_timeout,
            )
            response.raise_for_status()
            LOGGER.info("Notificación enviada a Discord para '%s'", listing.title)
        except requests.RequestException as exc:
            LOGGER.exception("Error enviando a Discord: %s", exc)

    def _notify_email(self, listing: Listing) -> None:
        cfg = self.config
        if not (cfg.smtp_host and cfg.smtp_from and cfg.smtp_to):
            LOGGER.debug("SMTP incompleto; email opcional omitido")
            return

        msg = EmailMessage()
        msg["Subject"] = f"[saturn-koma-watcher] Posible match ({listing.score})"
        msg["From"] = cfg.smtp_from
        msg["To"] = cfg.smtp_to
        msg.set_content(self._build_message_text(listing))

        try:
            with smtplib.SMTP(cfg.smtp_host, cfg.smtp_port, timeout=cfg.request_timeout) as server:
                server.starttls()
                if cfg.smtp_username and cfg.smtp_password:
                    server.login(cfg.smtp_username, cfg.smtp_password)
                server.send_message(msg)
            LOGGER.info("Email enviado para '%s'", listing.title)
        except Exception as exc:  # pragma: no cover
            LOGGER.exception("Error enviando email SMTP: %s", exc)
