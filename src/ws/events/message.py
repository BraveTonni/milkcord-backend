from .base import EventHandler

from src.schemas.ws import WSConnection
from src.schemas.users import UserPublic
from src.ws.connection_manager import WSConnectionManager

from src.core.ws_manager import ws_manager


class MessageEvent(EventHandler):
    def __init__(self, connection: WSConnection, manager: WSConnectionManager):
        super().__init__(connection, manager)

    async def handle(self, content: dict) -> None:
        message = content.get("payload", {}).get("content").strip()

        if not message:
            return

        # Длина ограничена до 1024 символов
        if len(message) > 1024:
            message = message[:1024]

        # Получаем собеседника, и если в сети отправляем сообщение
        partner = await ws_manager[self.connection.user.id]

        if not partner:
            return

        await partner.websocket.send_json(
            {
                "event": "message",
                "payload": {
                    "content": message,
                    "from": UserPublic(user=self.connection.user),
                    "self": False
                }
            }
        )
