from fastapi import WebSocket, WebSocketDisconnect, Depends

from fastapi.routing import APIRouter

from src.ws.message_handler import WSMessageHandler
from src.schemas.ws import WSConnection
from src.core.ws_manager import ws_manager

from src.database.crud import users as users_crud

from src.database.session import get_session

from sqlalchemy.ext.asyncio import AsyncSession


router = APIRouter()


@router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    access_token: str,
    session: AsyncSession = Depends(get_session)
) -> None:
    """Websocket connect endpoint"""
    user = await users_crud.get_user_by_access_token(session, access_token)

    if not user:
        return

    connection = WSConnection(
        websocket=websocket,
        user=user,
        session=session
    )

    await ws_manager.connect(connection)

    handler = WSMessageHandler(connection, ws_manager)

    try:
        while True:
            message = await websocket.receive_text()

            await handler.process_message(
                message=message
            )
    except WebSocketDisconnect:
        await ws_manager.disconnect(connection)
