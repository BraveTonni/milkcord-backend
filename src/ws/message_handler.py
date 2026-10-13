import orjson
import logging

from src.schemas.ws import WSConnection

from src.ws.events import WebRTCEvent
from src.ws.connection_manager import WSConnectionManager


class WSMessageHandler:
    """Class for processing websocket message"""

    def __init__(self, connection: WSConnection, manager: WSConnectionManager):
        self.connection = connection
        self.manager = manager

        # Уведомления о новых сообщениях приходят из REST-слоя,
        # по вебсокету клиенты отправляют только сигналинг звонков
        self.message_handlers = {
            "webrtc:offer": WebRTCEvent(self.connection, self.manager),
            "webrtc:answer": WebRTCEvent(self.connection, self.manager),
            "webrtc:ice": WebRTCEvent(self.connection, self.manager),
        }

        self.__logger = logging.getLogger(__name__)

    async def process_message(self, message: str) -> None:
        """Process message"""
        try:
            content = orjson.loads(message)
        except orjson.JSONDecodeError:
            self.__logger.warning("Получено сообщение с некорректным JSON")
            return

        message_type = content.get("event")

        message_handler = self.message_handlers.get(message_type)

        if not message_handler:
            self.__logger.info(f"Получен неизвестный тип сообщения: {message_type}")
            return

        await message_handler.handle(content)

