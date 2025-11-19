from sqlalchemy import select, delete, func
from sqlalchemy.orm import joinedload
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.models.posts import Post, PostLike, PostComment, PostPins
from src.database.crud import items as items_crud

from src.database.models.users import UserBase


# === СОЗДАНИЕ ПОСТА ===
async def create_post(session: AsyncSession, user_id: int, text: str) -> Post:
    """Создать новый пост"""
    post = Post(user_id=user_id, text=text)
    session.add(post)
    await items_crud.update_item(session, post)

    # Подставляем вычисляемые поля
    post.likes_count = 0
    post.liked = False

    return post


async def get_post(
    session: AsyncSession,
    post_id: int,
) -> Post:
    """Создать новый пост"""
    result = await session.execute(select(Post).where(Post.id == post_id))
    return result.scalar_one_or_none()


# === ЗАКРЕПЛЕНИЕ ПОСТА ===
async def pin_post(
    session: AsyncSession, post_id: int, user_id: int
) -> PostPins | None:
    post = await get_post(session, post_id)

    if not post:
        raise ValueError("Пост не найден")

    current_pin = await session.execute(
        select(PostPins).where(PostPins.user_id == user_id)
    )
    current = current_pin.scalar_one_or_none()

    if current:
        if current.post_id == post_id:
            await session.delete(current)
            await session.commit()
            return None

        await session.delete(current)

    new_pin = PostPins(post_id=post_id, user_id=user_id)
    session.add(new_pin)
    await session.commit()

    return new_pin


# === ПОЛУЧИТЬ ВСЕ ПОСТЫ ===
async def get_all_posts(
    session: AsyncSession, user_id: int | None = None
) -> list[Post]:
    stmt = (
        select(Post)
        .where(Post.user_id == user_id)
        .order_by(Post.created_at.desc())
        .options(joinedload(Post.files))
        .options(joinedload(Post.user))
    )
    result = await session.execute(stmt)
    posts = result.unique().scalars().all()

    if not posts:
        return []

    post_ids = [p.id for p in posts]

    # Лайки
    likes_data = await session.execute(
        select(PostLike.post_id, func.count(PostLike.id))
        .where(PostLike.post_id.in_(post_ids))
        .group_by(PostLike.post_id)
    )
    likes_map = dict(likes_data.all())

    # Комментарии
    comments_data = await session.execute(
        select(PostComment.post_id, func.count(PostComment.id))
        .where(PostComment.post_id.in_(post_ids))
        .group_by(PostComment.post_id)
    )
    comments_map = dict(comments_data.all())

    # Кто лайкнул
    liked_ids = set()
    if user_id:
        liked_result = await session.execute(
            select(PostLike.post_id).where(
                PostLike.user_id == user_id, PostLike.post_id.in_(post_ids)
            )
        )
        liked_ids = {r[0] for r in liked_result.all()}

    # Закреплённый пост
    is_pin = None
    if user_id:
        pin_result = await session.execute(
            select(PostPins.post_id).where(
                PostPins.user_id == user_id, PostPins.post_id.in_(post_ids)
            )
        )
        is_pin = pin_result.scalar_one_or_none()

    # Заполняем виртуальные поля + файлы уже загружены через joinedload
    for post in posts:
        post.likes_count = likes_map.get(post.id, 0)
        post.comments_count = comments_map.get(post.id, 0)
        post.liked = post.id in liked_ids
        post.is_pin = post.id == is_pin

    return posts


# === УДАЛИТЬ ПОСТ ===
async def delete_post(session: AsyncSession, post_id: int, user_id: int) -> bool:
    """Удаляет пост, если он принадлежит пользователю"""
    result = await session.execute(
        delete(Post)
        .where(Post.id == post_id, Post.user_id == user_id)
        .returning(Post.id)
    )
    deleted = result.scalar_one_or_none()
    if not deleted:
        return False

    await session.commit()
    return True


# === ПОЛУЧИТЬ ЛАЙКИ К ПОСТУ ===
async def get_likes_for_post(session: AsyncSession, post_id: int) -> int:
    """Получить количество лайков у поста"""
    result = await session.execute(
        select(func.count(PostLike.id)).where(PostLike.post_id == post_id)
    )
    return result.scalar() or 0


# === ПЕРЕКЛЮЧИТЬ ЛАЙК (toggle) ===
async def toggle_like(session: AsyncSession, user_id: int, post_id: int) -> dict:
    """
    Переключает лайк: если есть — удаляет, если нет — добавляет.
    Возвращает { 'liked': bool, 'likes_count': int }
    """
    result = await session.execute(
        select(PostLike).where(PostLike.user_id == user_id, PostLike.post_id == post_id)
    )
    existing_like = result.scalar_one_or_none()

    if existing_like:
        # уже лайкнул → снимаем лайк
        await session.execute(
            delete(PostLike).where(
                PostLike.user_id == user_id, PostLike.post_id == post_id
            )
        )
        await session.commit()
        liked = False
    else:
        # ставим лайк
        like = PostLike(user_id=user_id, post_id=post_id)
        session.add(like)
        await items_crud.update_item(session, like)
        liked = True

    likes_count = await get_likes_for_post(session, post_id)
    return {"liked": liked, "likes_count": likes_count}


# === СОЗДАТЬ КОММЕНТ ===
async def create_comment(
    session: AsyncSession, user_id: int, post_id: int, text: str
) -> PostComment:
    """Создать комментарий к посту"""
    comment = PostComment(user_id=user_id, post_id=post_id, text=text)
    session.add(comment)
    return await items_crud.update_item(session, comment)


# === КОММЕНТАРИИ К ПОСТУ ===
async def get_comments_for_post(session: AsyncSession, post_id: int) -> list[dict]:
    """Получить комментарии под постом с именами пользователей"""
    result = await session.execute(
        select(
            PostComment.id,
            PostComment.text,
            PostComment.created_at,
            UserBase.id.label("user_id"),
            UserBase.username,
        )
        .join(UserBase, UserBase.id == PostComment.user_id)
        .where(PostComment.post_id == post_id)
        .order_by(PostComment.created_at.asc())
    )

    comments = [
        {
            "id": row.id,
            "user_id": row.user_id,
            "username": row.username,
            "text": row.text,
            "created_at": row.created_at,
        }
        for row in result.all()
    ]

    return comments
