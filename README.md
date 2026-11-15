# MilkCord Backend

REST + WebSocket backend for the MilkCord messenger: chats, posts, friends,
stickers, music, file sharing and WebRTC call signalling.

## Stack

- Python 3.13, FastAPI, uv
- PostgreSQL + SQLAlchemy 2 (async), Alembic for schema migrations
- WebSocket events for live messages and WebRTC signalling
- Docker / Docker Compose, GitHub Actions CI, pytest

## Quick start

```bash
# 1. install dependencies
uv sync

# 2. configure the environment
cp .env.example .env
# edit DB_* values if your postgres is not on localhost

# 3. run (creates tables on startup, serves on http://127.0.0.1:7000)
uv run python main.py
```

Readiness probe: `GET /api/v1/health` → `200` when the app and the database
are reachable, `503` otherwise.

## Docker

```bash
cp .env.example .env
docker compose up --build
```

The compose stack starts postgres (with a healthcheck) and the API; uploaded
files are bind-mounted from `./static` so they survive container restarts.

## Tests

```bash
uv run pytest -q
```

## Configuration

All settings come from the environment (or `.env` in the project root) and
have safe defaults — see `.env.example`. Notable ones:

| Variable | Default | Purpose |
|---|---|---|
| `DB_*` | local postgres | database connection |
| `APP_HOST` / `APP_PORT` | `127.0.0.1:7000` | bind address |
| `RELOAD` | `false` | dev auto-reload |
| `CORS_ORIGINS` | localhost:5173/5174 | comma-separated allowed origins |
| `LOG_LEVEL` | `INFO` | application log level |
| `MAX_UPLOAD_SIZE` | 10 MiB | upload size limit |

## Layout

```
main.py               # app factory, lifespan, static mount
src/api/v1            # routers (users, chats, messages, posts, friends, calls, ws, health)
src/ws                # websocket connection manager and event handlers
src/database          # engine, session, orm models, crud
src/schemas           # pydantic request/response models
src/core              # settings, logging, enums, ws singleton
src/utils             # crypto, tokens, file/music/sticker helpers
alembic               # migrations
docs/                 # architecture, api and deployment notes
tests/                # pytest suite
```

## Related repositories

- [milkcord](https://github.com/BraveTonni/milkcord) — umbrella repo
- [milkcord-frontend](https://github.com/BraveTonni/milkcord-frontend) — React client
