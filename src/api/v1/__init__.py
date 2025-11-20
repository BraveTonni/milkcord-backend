from fastapi.routing import APIRouter

from .users import router as users_router
from .friends import router as friends_router
from .posts import router as posts_router
from .ws import router as ws_router
from .chats import router as chats_router
from .messages import router as messages_router
from .stickers import router as stickers_router
from .music import router as music_router
from .calls import router as calls_router


def register_v1_routers(router: APIRouter) -> None:
    """Register all routers"""
    api_router = APIRouter(
        prefix="/v1"
    )

    api_router.include_router(users_router)
    api_router.include_router(friends_router)
    api_router.include_router(posts_router)
    api_router.include_router(ws_router)
    api_router.include_router(chats_router)
    api_router.include_router(messages_router)
    api_router.include_router(stickers_router)
    api_router.include_router(music_router)
    api_router.include_router(calls_router)

    router.include_router(api_router)
