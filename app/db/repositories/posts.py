from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Post


class PostsRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def add_post(
        self,
        *,
        topic: str,
        text: str,
        custom_topic: str | None = None,
        embedding: list[float] | None = None,
        **_: object,
    ) -> Post:
        post = Post(
            topic=topic,
            custom_topic=custom_topic,
            text=text,
            embedding=embedding,
        )
        self.session.add(post)
        await self.session.flush()
        return post

    async def list_by_topic(
        self,
        *,
        topic: str,
        custom_topic: str | None = None,
        limit: int = 20,
    ) -> list[Post]:
        statement = select(Post).where(Post.topic == topic).order_by(Post.created_at.desc()).limit(limit)
        if custom_topic is not None:
            statement = statement.where(Post.custom_topic == custom_topic)

        result = await self.session.execute(statement)
        return list(result.scalars().all())

    async def delete_by_id(self, post_id: int) -> bool:
        post = await self.session.get(Post, post_id)
        if post is None:
            return False

        await self.session.delete(post)
        await self.session.flush()
        return True

    async def find_similar(
        self,
        *,
        topic: str,
        query_embedding: list[float],
        custom_topic: str | None = None,
        limit: int = 5,
    ) -> list[Post]:
        statement = (
            select(Post)
            .where(Post.topic == topic, Post.embedding.is_not(None))
            .order_by(Post.embedding.cosine_distance(query_embedding))
            .limit(limit)
        )
        if custom_topic is not None:
            statement = statement.where(Post.custom_topic == custom_topic)

        result = await self.session.execute(statement)
        return list(result.scalars().all())
