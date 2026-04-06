from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from pathlib import Path
import logging

DEFAULT_QUERIES = [
    "広井政昭 土星こま",
    "土星こま",
    "The Saturn 広井政昭",
    "Hiroi Masaaki Saturn koma",
    "mh044 土星こま",
    "広井政昭 独楽",
    "江戸独楽 広井政昭",
]

DEFAULT_ENABLED_SOURCES = ["buyee", "yahoo_auctions", "mercari", "rakuma", "mandarake"]
LOGGER = logging.getLogger(__name__)


@dataclass
class WatcherConfig:
    queries: list[str] = field(default_factory=lambda: list(DEFAULT_QUERIES))
    enabled_sources: list[str] = field(default_factory=lambda: list(DEFAULT_ENABLED_SOURCES))
    min_score: int = 60
    discord_webhook_url: str = ""
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_username: str = ""
    smtp_password: str = ""
    smtp_from: str = ""
    smtp_to: str = ""
    request_timeout: int = 15
    user_agent: str = (
        "Mozilla/5.0 (X11; Linux x86_64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    )


def _parse_json_list(value: str) -> list[str]:
    value = value.strip()
    if not value:
        return []
    if value.startswith("["):
        raw = json.loads(value)
        if isinstance(raw, list):
            return [str(x) for x in raw]
        return []
    return [item.strip() for item in value.split(",") if item.strip()]


def _env_str(name: str) -> str | None:
    value = os.getenv(name)
    return value if value is not None else None


def _env_int(name: str) -> int | None:
    value = os.getenv(name)
    if value is None:
        return None
    try:
        return int(value)
    except ValueError:
        return None


def load_config(config_path: str | None = None) -> WatcherConfig:
    """Carga configuración desde defaults, archivo JSON y variables de entorno."""
    cfg = WatcherConfig()

    if config_path:
        path = Path(config_path)
        if path.exists():
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                LOGGER.warning("Archivo de configuración inválido: %s. Se usan defaults/env.", path)
                data = {}
            if isinstance(data, dict):
                cfg.queries = [str(x) for x in data.get("queries", cfg.queries)]
                cfg.enabled_sources = [
                    str(x) for x in data.get("enabled_sources", cfg.enabled_sources)
                ]
                cfg.min_score = int(data.get("min_score", cfg.min_score))
                cfg.discord_webhook_url = str(
                    data.get("discord_webhook_url", cfg.discord_webhook_url)
                )
                cfg.smtp_host = str(data.get("smtp_host", cfg.smtp_host))
                cfg.smtp_port = int(data.get("smtp_port", cfg.smtp_port))
                cfg.smtp_username = str(data.get("smtp_username", cfg.smtp_username))
                cfg.smtp_password = str(data.get("smtp_password", cfg.smtp_password))
                cfg.smtp_from = str(data.get("smtp_from", cfg.smtp_from))
                cfg.smtp_to = str(data.get("smtp_to", cfg.smtp_to))
                cfg.request_timeout = int(data.get("request_timeout", cfg.request_timeout))
                cfg.user_agent = str(data.get("user_agent", cfg.user_agent))

    env_queries = _env_str("WATCHER_QUERIES")
    if env_queries:
        parsed = _parse_json_list(env_queries)
        if parsed:
            cfg.queries = parsed

    env_sources = _env_str("WATCHER_ENABLED_SOURCES")
    if env_sources:
        parsed = _parse_json_list(env_sources)
        if parsed:
            cfg.enabled_sources = parsed

    for attr, env_name in [
        ("discord_webhook_url", "DISCORD_WEBHOOK_URL"),
        ("smtp_host", "SMTP_HOST"),
        ("smtp_username", "SMTP_USERNAME"),
        ("smtp_password", "SMTP_PASSWORD"),
        ("smtp_from", "SMTP_FROM"),
        ("smtp_to", "SMTP_TO"),
        ("user_agent", "WATCHER_USER_AGENT"),
    ]:
        value = _env_str(env_name)
        if value is not None and value != "":
            setattr(cfg, attr, value)

    for attr, env_name in [
        ("min_score", "WATCHER_MIN_SCORE"),
        ("smtp_port", "SMTP_PORT"),
        ("request_timeout", "WATCHER_REQUEST_TIMEOUT"),
    ]:
        value = _env_int(env_name)
        if value is not None:
            setattr(cfg, attr, value)

    cfg.queries = [q for q in cfg.queries if q.strip()]
    cfg.enabled_sources = [s.strip().lower() for s in cfg.enabled_sources if s.strip()]
    return cfg
