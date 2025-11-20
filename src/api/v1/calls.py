from fastapi.routing import APIRouter
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.schemas.calls import (
    CallStartRequest,
    CallEndRequest,
    CallAcceptRequest,
    CallRejectRequest
)
from src.schemas.response import ErrorResponse
from src.database.session import get_session
from src.database.crud import calls as calls_crud
from src.database.crud import users as users_crud
from src.core.ws_manager import ws_manager

router = APIRouter(prefix="/calls", tags=["Calls"])


# ----------------------------
# START CALL
# ----------------------------
@router.post("/start")
async def start_call(
    access_token: str,
    payload: CallStartRequest,
    session: AsyncSession = Depends(get_session)
):
    caller = await users_crud.get_user_by_access_token(session, access_token)
    if not caller:
        return ErrorResponse(error="Пользователь не найден")

    callee = await users_crud.get_user_by_id(session, payload.to_user_id)
    if not callee:
        return ErrorResponse(error="Вызываемый пользователь не найден")

    call_obj = await calls_crud.start_call(
        session=session,
        caller_id=caller.id,
        callee_id=callee.id,
        kind=payload.kind,
    )

    # send call:incoming → called user
    callee_ws = ws_manager.active_connections.get(callee.id)
    if callee_ws:
        await callee_ws.websocket.send_json({
            "event": "call:incoming",
            "payload": {
                "call_id": call_obj.id,
                "from_user": {
                    "id": caller.id,
                    "username": caller.username,
                },
                "kind": call_obj.kind
            }
        })

    # send call:start → caller (confirmation)
    caller_ws = ws_manager.active_connections.get(caller.id)
    if caller_ws:
        await caller_ws.websocket.send_json({
            "event": "call:start",
            "payload": {
                "call_id": call_obj.id,
                "to_user": {
                    "id": callee.id,
                    "username": callee.username,
                },
                "kind": call_obj.kind
            }
        })

    return {"call": call_obj}


# ----------------------------
# ACCEPT CALL
# ----------------------------
@router.post("/accept")
async def accept_call(
    access_token: str,
    payload: CallAcceptRequest,
    session: AsyncSession = Depends(get_session)
):
    user = await users_crud.get_user_by_access_token(session, access_token)
    if not user:
        return ErrorResponse(error="Пользователь не найден")

    call_obj = await calls_crud.get_call(session, payload.call_id)
    if not call_obj:
        return ErrorResponse(error="Звонок не найден")

    caller_ws = ws_manager.active_connections.get(call_obj.caller_id)

    # inform caller
    if caller_ws:
        await caller_ws.websocket.send_json({
            "event": "call:accept",
            "payload": {
                "call_id": payload.call_id,
                "from": user.id
            }
        })

    return {"success": True}


# ----------------------------
# REJECT CALL
# ----------------------------
@router.post("/reject")
async def reject_call(
    access_token: str,
    payload: CallRejectRequest,
    session: AsyncSession = Depends(get_session)
):
    user = await users_crud.get_user_by_access_token(session, access_token)
    if not user:
        return ErrorResponse(error="Пользователь не найден")

    call_obj = await calls_crud.get_call(session, payload.call_id)
    if not call_obj:
        return ErrorResponse(error="Звонок не найден")

    caller_ws = ws_manager.active_connections.get(call_obj.caller_id)

    if caller_ws:
        await caller_ws.websocket.send_json({
            "event": "call:reject",
            "payload": {
                "call_id": payload.call_id,
                "from": user.id
            }
        })

    return {"success": True}


# ----------------------------
# END CALL
# ----------------------------
@router.post("/end")
async def end_call(
    access_token: str,
    payload: CallEndRequest,
    session: AsyncSession = Depends(get_session)
):
    user = await users_crud.get_user_by_access_token(session, access_token)
    if not user:
        return ErrorResponse(error="Пользователь не найден")

    call_obj = await calls_crud.end_call(
        session=session,
        call_id=payload.call_id,
        closed_by=user.id,
    )

    if not call_obj:
        return ErrorResponse(error="Звонок не найден")

    caller_ws = ws_manager.active_connections.get(call_obj.caller_id)
    callee_ws = ws_manager.active_connections.get(call_obj.callee_id)

    payload_json = {
        "event": "call:end",
        "payload": {
            "call_id": call_obj.id,
            "closed_by": user.id
        }
    }

    if caller_ws:
        await caller_ws.websocket.send_json(payload_json)

    if callee_ws:
        await callee_ws.websocket.send_json(payload_json)

    return {"call": call_obj}
