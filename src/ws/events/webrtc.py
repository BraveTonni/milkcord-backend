# В файле WebRTCEvent
from .base import EventHandler
from src.core.ws_manager import ws_manager
import logging

logger = logging.getLogger(__name__)


class WebRTCEvent(EventHandler):
    """
    Handles WebRTC signalling between two users:
    - webrtc:offer
    - webrtc:answer
    - webrtc:ice
    """

    def __init__(self, connection, manager):
        super().__init__(connection, manager)

    async def handle(self, content: dict) -> None:
        event = content.get("event")
        payload = content.get("payload", {})

        # Получаем call_id из payload
        call_id = payload.get("call_id")
        if not call_id:
            logger.warning("webrtc event without 'call_id' field: %s", content)
            return

        # Получаем информацию о звонке
        from sqlalchemy.ext.asyncio import AsyncSession
        from src.database.session import get_session
        from src.database.crud import calls as calls_crud
        
        session_gen = get_session()
        session = await session_gen.__anext__()
        
        try:
            call_obj = await calls_crud.get_call(session, call_id)
            if not call_obj:
                logger.warning(f"Call {call_id} not found")
                return

            # Определяем ID собеседника
            if self.connection.user.id == call_obj.caller_id:
                target_id = call_obj.callee_id
            elif self.connection.user.id == call_obj.callee_id:
                target_id = call_obj.caller_id
            else:
                logger.warning(f"User {self.connection.user.id} not part of call {call_id}")
                return

            # Получаем соединение собеседника через метод менеджера
            partner = ws_manager.active_connections.get(target_id)
            if not partner:
                logger.info(f"User {target_id} is offline, cannot forward {event}")
                return

            # добавляем sender
            payload["from"] = self.connection.user.id

            await partner.websocket.send_json({"event": event, "payload": payload})
        finally:
            await session.close()
            try:
                await session_gen.__anext__()
            except StopAsyncIteration:
                pass