from fastapi import Depends, Form, File, UploadFile
from fastapi.routing import APIRouter
from fastapi.responses import FileResponse

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload


from src.database.session import get_session
from src.database.crud import posts as posts_crud

from src.schemas.posts import (
    PostResponse,
    PostPins,
    PostPinResponse,
    PostsResponse,
    LikeResponse,
    CommentCreate,
    CommentResponse,
    CommentsResponse,
    SuccessResponse,
)
from src.schemas.response import ErrorResponse
from src.database.crud import users as users_crud
from src.database.crud import items as items_crud

from src.database.models.posts import PostFile, Post

from src.utils.helpers.files import FilesHelper
from src.utils.helpers.paths import PathHelper
from src.core.config import settings

router = APIRouter(prefix="/posts", tags=["Posts"])


@router.post("/create")
async def create_post(
    access_token: str,
    text: str = Form(...),
    files: list[UploadFile] = File(default=[]),
    session: AsyncSession = Depends(get_session),
) -> PostResponse | ErrorResponse:
    user = await users_crud.get_user_by_access_token(session, access_token)
    if not user:
        return ErrorResponse(error="Неверный токен")

    if not text.strip() and not files:
        return ErrorResponse(error="Пост не может быть пустым")

    post = await posts_crud.create_post(session, user.id, text.strip())

    for upload_file in files:
        if not upload_file.filename:
            continue
        if upload_file.size and upload_file.size > settings.MAX_UPLOAD_SIZE:
            await session.rollback()
            return ErrorResponse(error="Файл слишком большой")

        file_name = await FilesHelper.save_upload_file(upload_file, "posts")
        session.add(
            PostFile(
                post_id=post.id, file_name=file_name, file_size=upload_file.size or 0,
                orig_name=upload_file.filename
            )
        )

    await session.commit()

    # Перезагружаем пост с нужными данными
    stmt = (
        select(Post)
        .options(joinedload(Post.files))
        .options(joinedload(Post.user))
        .where(Post.id == post.id)
    )
    result = await session.execute(stmt)
    post_obj = result.unique().scalar_one()

    # Вручную заполняем виртуальные поля (как в get_all_posts)
    post_obj.likes_count = 0
    post_obj.comments_count = 0
    post_obj.liked = False
    post_obj.is_pin = False

    return PostResponse(post=post_obj)


@router.get("/get/{file_name}", response_model=None)
async def get_file_post(
    file_name: str,
    session: AsyncSession = Depends(get_session),
) -> FileResponse | ErrorResponse:
    result = await session.execute(
        select(PostFile).where(PostFile.file_name == file_name)
    )
    post_file: PostFile | None = result.scalar_one_or_none()

    if not post_file:
        return ErrorResponse(error="Файл не найден")

    file_path = PathHelper.get_root() / "static" / "files" / "posts" / file_name

    try:
        resolved_path = file_path.resolve()
        allowed_root = (PathHelper.get_root() / "static" / "files").resolve()

        if not resolved_path.is_relative_to(allowed_root):
            return ErrorResponse(error="Недопустимый путь")

        if not resolved_path.exists():
            return ErrorResponse(error="Файл не найден на диске")
    except Exception:
        return ErrorResponse(error="Ошибка проверки пути")

    mime_type = FilesHelper.media_type_for(resolved_path)

    original_filename = post_file.orig_name

    return FileResponse(
        path=str(resolved_path),
        media_type=mime_type,
        filename=original_filename,
        headers={
            "Cache-Control": "public, max-age=31536000, immutable",
        },
    )


@router.get("/all")
async def get_all_posts(
    username: str, session: AsyncSession = Depends(get_session)
) -> PostsResponse:
    user = await users_crud.get_user_by_username(session, username)
    if not user:
        return ErrorResponse(error="Пользователь не найден")

    posts = await posts_crud.get_all_posts(session, user.id)

    return PostsResponse(posts=posts)


@router.post("/{post_id}/like")
async def toggle_like(
    access_token: str, post_id: int, session: AsyncSession = Depends(get_session)
) -> LikeResponse | ErrorResponse:
    user = await users_crud.get_user_by_access_token(session, access_token)
    if not user:
        return ErrorResponse(error="Пользователь не найден")

    result = await posts_crud.toggle_like(session, user.id, post_id)

    return LikeResponse(
        message="Лайк обновлён",
        liked=result["liked"],
        likes_count=result["likes_count"],
    )


@router.post("/{post_id}/comment")
async def add_comment(
    access_token: str,
    post_id: int,
    data: CommentCreate,
    session: AsyncSession = Depends(get_session),
) -> CommentResponse | ErrorResponse:
    user = await users_crud.get_user_by_access_token(session, access_token)
    if not user:
        return ErrorResponse(error="Пользователь не найден")

    comment = await posts_crud.create_comment(session, user.id, post_id, data.text)
    await items_crud.update_item(session, comment)

    comment.username = user.username

    return CommentResponse(comment=comment)


@router.get("/{post_id}/comments")
async def get_comments(
    post_id: int, session: AsyncSession = Depends(get_session)
) -> CommentsResponse:
    comments = await posts_crud.get_comments_for_post(session, post_id)
    return CommentsResponse(comments=comments)


# === Получить один пост по ID ===
@router.get("/{post_id}")
async def get_post_by_id(
    post_id: int, session: AsyncSession = Depends(get_session)
) -> PostResponse | ErrorResponse:
    post = await posts_crud.get_post_by_id(session, post_id)
    if not post:
        return ErrorResponse(error="Пост не найден")

    return PostResponse(post=post)


# === Удаление поста по ID ===
@router.delete("/delete/{post_id}")
async def delete_post(
    access_token: str, post_id: int, session: AsyncSession = Depends(get_session)
) -> SuccessResponse | ErrorResponse:
    user = await users_crud.get_user_by_access_token(session, access_token)
    if not user:
        return ErrorResponse(error="Пользователь не найден")

    await posts_crud.delete_post(session, post_id, user.id)

    return SuccessResponse()


# === Закрепление поста по ID ===
@router.post("/pin")
async def pin_post(
    access_token: str, post: PostPins, session: AsyncSession = Depends(get_session)
) -> PostPinResponse | ErrorResponse:
    user = await users_crud.get_user_by_access_token(session, access_token)
    if not user:
        return ErrorResponse(error="Пользователь не найден")

    try:
        post_pin = await posts_crud.pin_post(session, post.post_id, user.id)
    except ValueError:
        return ErrorResponse(error="Пост не найден")

    return PostPinResponse(is_new=post_pin is not None)
