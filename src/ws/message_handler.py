import orjson
import logging

from src.schemas.ws import WSConnection

from src.ws.events import MessageEvent
from src.ws.events import WebRTCEvent
from src.ws.connection_manager import WSConnectionManager


class WSMessageHandler:
    """Class for processing websocket message"""

    def __init__(self, connection: WSConnection, manager: WSConnectionManager):
        self.connection = connection
        self.manager = manager

        self.message_handlers = {
            "message": MessageEvent(self.connection, self.manager),
            "webrtc:offer": WebRTCEvent(self.connection, self.manager),
            "webrtc:answer": WebRTCEvent(self.connection, self.manager),
            "webrtc:ice": WebRTCEvent(self.connection, self.manager),
        }

        self.__logger = logging.getLogger(__name__)

    async def process_message(self, message: str) -> None:
        """Process message"""
        content = orjson.loads(message)
        message_type = content.get("event")

        message_handler = self.message_handlers.get(message_type)

        if not message_handler:
            self.__logger.info(f"Получен неизвестный тип сообщения: {message_type}")
            return

        await message_handler.handle(content)
