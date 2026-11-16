# Architecture

## Layers

Requests flow strictly top-down; each layer only imports the layers below it:

```
main.py                    app factory, lifespan (db init), static mount
    │
src/api/v1                 routers: http contract, validation, auth by access_token
    │
src/ws                     websocket runtime: connection manager + event handlers
    │
src/database/crud          data access: queries and commits
    ├── src/database/models    sqlalchemy orm models
    ├── src/schemas            pydantic dto (request/response)
    └── src/utils/helpers      file/music/sticker helpers
    │
src/core                   settings (env), logging, enums, ws_manager singleton
src/database/base          async engine + init_db (metadata.create_all)
```

Import rules that keep the graph acyclic:

- `src/schemas` knows nothing about the database;
- `src/database/models` never imports routers or ws;
- `src/core/ws_manager` is the only place where the `core` and `ws` layers meet,
  they are committed together by design.

## Request lifecycle (REST)

1. Router receives the request and resolves `access_token` against
   `crud.users.get_user_by_access_token`.
2. CRUD layer queries/mutates rows inside the session from
   `get_session` (one session per request).
3. Response is a `SuccessResponse`-derived schema (`{"success": true, ...}`)
   or an `ErrorResponse` (`{"success": false, "error": "..."}`).

## WebSocket lifecycle

1. `GET /api/v1/ws?access_token=...` — invalid tokens are closed with code
   `1008` instead of a silent drop.
2. `WSConnectionManager.connect` registers the socket in
   `active_connections` keyed by user id.
3. Incoming frames are parsed by `WSMessageHandler`; malformed JSON and
   unknown events are logged and ignored, WebRTC signalling
   (`webrtc:offer|answer|ice`) is relayed to the call partner.
4. Message/post/friend notifications are pushed from the REST layer
   (`active_connections.get(user_id)`), not from incoming ws frames.
5. `finally:` disconnects on any error, so no dead sockets stay registered.

## Database

- Engine: async SQLAlchemy with a small pool; SQL echo is opt-in
  (`SQL_ECHO=true`, keep it off in production).
- Tables are created on startup via `Base.metadata.create_all`.
  Alembic exists for incremental schema changes — its baseline migration was
  written against an already-created database, treat `create_all` as the
  source of truth for fresh installs.
- Timestamps are stored as unix seconds (`BigInteger`), except `calls`,
  which use naive UTC `DateTime` columns.

## Concurrency model

The app runs a **single uvicorn process**: `active_connections` lives in
process memory, so multiple workers would silently lose websocket
notifications. Scale-out would require an external pub/sub bridge
(REDIS + fan-out) — out of scope for now.

## Security notes

- Passwords: PBKDF2-HMAC-SHA256, per-user salt, constant-time comparison;
  legacy unsalted SHA-256 hashes still verify so old accounts keep working.
- Uploads: extension + content-type allowlists, `MAX_UPLOAD_SIZE` cap,
  generated file names (client filenames never touch the path).
- Static file serving: all dynamic paths are `resolve()`d and checked against
  their allowed root; anything not on the media allowlist is served as
  `application/octet-stream` (downloads instead of executing HTML/JS).
- CORS origins, host/port and log level come from the environment.
