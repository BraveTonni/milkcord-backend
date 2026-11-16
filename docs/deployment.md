# Deployment

## Docker Compose (recommended)

```bash
cp .env.example .env      # set real DB_PASSWORD at minimum
docker compose up --build -d
docker compose ps         # db: healthy, api: running
curl -fsS http://127.0.0.1:7000/api/v1/health
```

What the stack does:

- `db` — postgres 17-alpine with `pg_isready` healthcheck; the API waits for
  `service_healthy` before starting;
- `api` — multi-stage image (uv builder → slim runtime, non-root user);
  `DB_HOST=db` is injected, everything else comes from `.env`;
- uploaded files are bind-mounted from `./static/{avatars,covers,files}`,
  database lives in the `dbdata` volume — both survive redeploys.

## Environment

Never bake `.env` into the image (it is in `.dockerignore`). All required
variables are listed in `.env.example`; the app starts with safe defaults for
local development but production should at least set:

```
DB_PASSWORD=<strong>
APP_HOST=0.0.0.0          # reachable inside the container
CORS_ORIGINS=https://app.example.com
LOG_LEVEL=INFO
RELOAD=false
```

## Without Docker

```bash
uv sync --locked
uv run python main.py     # requires a reachable postgres from .env
```

## Operational notes

- **Single worker on purpose**: websocket connections are tracked in process
  memory; running `workers > 1` would drop live notifications.
- **Readiness**: use `/api/v1/health` — it returns `503` while postgres is
  down, so the load balancer stops routing to an instance that cannot serve.
- **Logs**: stdout only (12-factor); `LOG_LEVEL=DEBUG` additionally enables
  SQL echo via `SQL_ECHO=true` for local debugging.
- **Migrations**: fresh databases are initialised from `Base.metadata.create_all`
  at startup; Alembic (`uv run alembic upgrade head`) is for evolving an
  existing database.
- **Backups**: the `dbdata` volume plus `./static` are the two stateful paths.
