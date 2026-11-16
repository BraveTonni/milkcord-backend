# API Reference

Base URL: `/api/v1`. Responses are JSON: success objects carry
`{"success": true, ...}`, errors carry `{"success": false, "error": "..."}`.

## Authentication

Sessions are token-based: every private endpoint expects the user's
`access_token` (returned by `/users/signup` and `/users/login`).

> Legacy shape: the token is passed as a query parameter on GET endpoints and
> as a form/body field on POST endpoints. Moving it to an
> `Authorization: Bearer` header is the planned next step; the client layer
> would need the matching change.

## Endpoints

### Health

| Method | Path | Description |
|---|---|---|
| GET | `/health` | `200` app+db OK, `503` database unavailable |

### Users

| Method | Path | Description |
|---|---|---|
| GET | `/users/me` | current user by token |
| GET | `/users/avatar?filename=` | avatar image (falls back to default) |
| GET | `/users/cover?filename=` | cover image (falls back to default) |
| GET | `/users/profile/{id\|username}` | public profile |
| POST | `/users/login` | sign in |
| POST | `/users/signup` | register |
| PATCH | `/users/me/bio` | update bio |
| POST | `/users/avatar` | upload avatar (image only, size-capped) |
| POST | `/users/cover` | upload cover (image only, size-capped) |
| POST | `/users/settings/update` | change username/email/password |

### Friends

`POST /friends/request/{username}`, `POST /friends/accept/{username}`,
`DELETE /friends/remove/{username}`, `GET /friends/list`,
`GET /friends/incoming`, `GET /friends/outgoing`,
`GET /friends/status/{username}`.

### Chats & messages

| Method | Path | Description |
|---|---|---|
| GET | `/chats/all` | list chats of the current user |
| GET | `/chats/chat/{user_id}` | get or create a direct chat |
| POST | `/messages/send` | text message |
| POST | `/messages/send/sticker` | sticker message |
| POST | `/messages/send/file` | file attachments (size-capped) |
| GET | `/messages/{chat_id}/messages` | chat history |
| GET | `/messages/get/{file_name}` | download attachment |
| POST | `/messages/edit` | edit own text message |
| POST | `/messages/delete` | soft-delete own message |

### Posts

`POST /posts/create`, `GET /posts/all?username=`, `GET /posts/{id}`,
`POST /posts/{id}/like`, `POST /posts/{id}/comment`,
`GET /posts/{id}/comments`, `DELETE /posts/delete/{id}`, `POST /posts/pin`,
`GET /posts/get/{file_name}`.

### Stickers, music, calls

- `GET /stickers/list`, `GET /stickers/{pack}/{sticker}`
- `GET /music/list`
- `POST /calls/start`, `/calls/accept`, `/calls/reject`, `/calls/end`

### WebSocket

`WS /api/v1/ws?access_token=...`

Client → server:

```json
{"event": "webrtc:offer", "payload": {"call_id": 1, "sdp": "..."}}
{"event": "webrtc:answer", "payload": {"call_id": 1, "sdp": "..."}}
{"event": "webrtc:ice",    "payload": {"call_id": 1, "candidate": "..."}}
```

Server → client events: `message`, `message:sticker`, `message:file`,
`message:edit`, `message:delete`, `friend:*`, plus relayed `webrtc:*`.
Payloads always include `self` (`true` for the sender's own socket) so the
client can tell echo from partner events.
