from app.db.models import Post
from app.db.repositories.posts import PostsRepository


class RetrievalService:
    def __init__(self, posts_repository: PostsRepository) -> None:
        self.posts_repository = posts_repository

    async def find_style_examples(
        self,
        *,
        topic: str,
        query_embedding: list[float] | None,
        custom_topic: str | None = None,
        limit: int = 5,
    ) -> list[Post]:
        if query_embedding is None:
            return await self.posts_repository.list_by_topic(
                topic=topic,
                custom_topic=custom_topic,
                limit=limit,
            )
        return await self.posts_repository.find_similar(
            topic=topic,
            custom_topic=custom_topic,
            query_embedding=query_embedding,
            limit=limit,
        )
