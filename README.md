# saturn-koma-watcher

Monitor de anuncios para detectar posibles publicaciones de la peonza rara de Masaaki Hiroi conocida como `The Saturn` / `土星こま`.

El proyecto consulta varias fuentes japonesas, puntúa coincidencias con un sistema explícito de términos y avisa por Discord (y opcionalmente por email SMTP).

## Objetivo

Detectar automáticamente anuncios potencialmente relevantes aunque estén descritos con nombres inconsistentes.

Palabras clave principales:

- `土星こま`
- `The Saturn`
- `広井政昭`
- `Hiroi Masaaki`
- `mh044`

Buyee es la fuente prioritaria en la implementación.

## Características

- Arquitectura modular por plugins de fuentes.
- Scoring con pesos explícitos y bonus por múltiples coincidencias.
- Más peso para términos encontrados en el título que en la descripción.
- Estado persistente en `state.json` para evitar avisos duplicados.
- Notificación por Discord webhook.
- Notificación SMTP opcional sin bloquear ejecución si falta configuración.
- Ejecución local por CLI y automática en GitHub Actions.
- Logging y manejo de errores por fuente.

## Estructura

```text
saturn-koma-watcher/
  README.md
  requirements.txt
  .gitignore
  config.example.json
  watcher.py
  state.json (runtime, no versionado)
  saturn_koma_watcher/
    __init__.py
    config.py
    models.py
    notifier.py
    scoring.py
    storage.py
    utils.py
    sources/
      __init__.py
      base.py
      buyee.py
      yahoo_auctions.py
      mercari.py
      rakuma.py
      mandarake.py
  .github/
    workflows/
      watch.yml
  tests/
    test_scoring.py
    test_storage.py
```

## Instalación local

1. Crear entorno virtual:

```bash
.venv/bin/python --version  # (opcional, para comprobar si ya existe)
/opt/homebrew/bin/python3.11 -m venv .venv
source .venv/bin/activate
```

2. Instalar dependencias:

```bash
python3 -m pip install -r requirements.txt
```

Recomendación: usar Python 3.11 dentro de `.venv`.

3. Crear configuración local:

```bash
cp config.example.json config.json
```

4. Editar `config.json` con tus valores.

## Uso local

Ejecución normal:

```bash
.venv/bin/python watcher.py --config config.json
```

Modo simulación (no notifica ni guarda estado):

```bash
.venv/bin/python watcher.py --config config.json --dry-run
```

Modo verbose:

```bash
.venv/bin/python watcher.py --config config.json --verbose
```

También funciona con:

```bash
.venv/bin/python watcher.py
```

Si `config.json` no existe, se usan defaults internos y variables de entorno.

## Configuración

Opciones en `config.example.json`:

- `queries`: lista de búsquedas en japonés/inglés.
- `enabled_sources`: fuentes activas (`buyee`, `yahoo_auctions`, `mercari`, `rakuma`, `mandarake`).
- `min_score`: umbral mínimo para notificar.
- `discord_webhook_url`: webhook de Discord.
- `smtp_*`: configuración SMTP opcional.
- `request_timeout`: timeout HTTP en segundos.
- `user_agent`: User-Agent para requests.

Variables de entorno soportadas (sobrescriben archivo):

- `WATCHER_QUERIES` (JSON array o CSV)
- `WATCHER_ENABLED_SOURCES` (JSON array o CSV)
- `WATCHER_MIN_SCORE`
- `DISCORD_WEBHOOK_URL`
- `SMTP_HOST`, `SMTP_PORT`, `SMTP_USERNAME`, `SMTP_PASSWORD`, `SMTP_FROM`, `SMTP_TO`
- `WATCHER_REQUEST_TIMEOUT`
- `WATCHER_USER_AGENT`

## Sistema de scoring

Pesos base (título > descripción):

- `+50` `土星こま`
- `+45` `The Saturn`
- `+40` `mh044`
- `+25` `広井政昭`
- `+20` `Hiroi`
- `+15` `Masaaki`
- `+10` `球` / `球体` / `内球`
- `+10` `二重構造`
- `+8` `回転`
- `+8` `江戸独楽`

La descripción aplica peso reducido (`60%` del peso base). Además hay bonus por múltiples coincidencias entre términos fuertes, autor y estructura.

## Fuentes soportadas

Orden de prioridad:

1. Buyee
2. Yahoo! Auctions Japan
3. Mercari Japan
4. Rakuten Rakuma
5. Mandarake

Estado actual de robustez:

- `buyee`: implementación activa con parser defensivo (JSON-LD + fallback HTML).
- `yahoo_auctions`, `mercari`, `rakuma`, `mandarake`: plugin implementado pero devuelve `[]` con warning explícito por baja fiabilidad sin API estable.

Esto es intencional para evitar parsers frágiles que aparenten funcionar.

## Notificaciones

### Discord webhook

1. Crea un webhook en tu servidor de Discord.
2. Configura `DISCORD_WEBHOOK_URL` o `discord_webhook_url`.
3. Cada alerta incluye:
   - fuente
   - título
   - score
   - términos detectados
   - URL

### Email SMTP (opcional)

Configura al menos:

- `smtp_host`
- `smtp_from`
- `smtp_to`

Opcionalmente autenticación:

- `smtp_username`
- `smtp_password`

Si SMTP no está configurado, el watcher no falla; solo omite email.

## Estado y deduplicación

`state.json` almacena `seen_ids` para no repetir avisos.

Reglas:

- Si un anuncio ya existe en `state.json`, se omite notificación.
- Si hay cambios, se actualiza `state.json`.
- En `--dry-run`, nunca se persiste estado.

## GitHub Actions

Workflow: `.github/workflows/watch.yml`

Incluye:

- ejecución manual (`workflow_dispatch`)
- ejecución cada 30 minutos (`cron: */30 * * * *`)
- instalación de dependencias
- ejecución del watcher
- commit de `state.json` solo si cambió

Configura secretos en GitHub (Settings > Secrets and variables > Actions):

- `DISCORD_WEBHOOK_URL`
- `SMTP_HOST`
- `SMTP_PORT`
- `SMTP_USERNAME`
- `SMTP_PASSWORD`
- `SMTP_FROM`
- `SMTP_TO`

Si no hay cambios en `state.json`, no se hace commit.

## Tests

Ejecutar:

```bash
.venv/bin/python -m pytest -q
```

Nota práctica (macOS): en algunos entornos `pip` o `pytest` no están en `PATH`.
Usar `python3 -m pip` y `python3 -m pytest` evita ese problema.

Tests incluidos:

- `test_scoring.py`
- `test_storage.py`

## Limitaciones

- Algunas fuentes japonesas tienen anti-bot fuerte o renderizado dinámico no estable para scraping sin API oficial.
- La calidad del matching depende del texto visible en el anuncio.
- Puede haber falsos positivos si aparecen términos parciales relevantes.

## Ideas de mejora

- Añadir más señales semánticas (tokenización japonés y similitud difusa).
- Guardar histórico con timestamp y score por ejecución.
- Añadir resumen diario por Discord.
- Añadir ranking por confianza y priorización por fuente.
- Integrar APIs oficiales cuando existan.
