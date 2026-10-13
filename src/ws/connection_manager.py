import logging
import traceback

from src.schemas.ws import WSConnection

from src.database.crud import users as users_crud

from src.utils.time_formatter import TimeFormatter


class WSConnectionManager:
    """WS Connection manager"""
    def __init__(self):
        self.active_connections: dict[str, WSConnection] = {}

        self.__logger = logging.getLogger(__name__)

    async def connect(self, connection: WSConnection) -> bool:
        """Установка соединения с пользователем"""
        await connection.websocket.accept()

        self.active_connections[connection.user.id] = connection

        return True

    async def disconnect(self, connection: WSConnection) -> None:
        """Отключение соединения с пользователем"""
        # Отключаем комнату, если есть
        if self.active_connections.get(connection.user.id):
            self.active_connections.pop(connection.user.id)

        await users_crud.update_last_seen(
            connection.session,
            connection.user,
            TimeFormatter.get_current_unix()
        )

    async def broadcast(self, content: dict) -> None:
        """Метод оповещения сообщения всем пользователям"""
        for connection in list(self.active_connections.values()):
            try:
                await connection.websocket.send_json(content)
            except Exception:
                self.__logger.warning(
                    f"Произошла ошибка при отправке JSON клиенту {traceback.format_exc()}"
                )
                continue
