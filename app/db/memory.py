from dataclasses import dataclass, field
from datetime import datetime, timezone


@dataclass
class MemoryPost:
    id: int
    topic: str
    text: str
    custom_topic: str | None = None
    embedding: list[float] | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class MemoryGenerationLog:
    id: int
    topic: str
    user_request: str
    generated_text: str | None
    status: str
    custom_topic: str | None = None
    prompt: str | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class InMemoryPostsRepository:
    def __init__(self) -> None:
        self.posts: list[MemoryPost] = []
        self._next_id = 1

    async def add_post(
        self,
        *,
        topic: str,
        text: str,
        custom_topic: str | None = None,
        embedding: list[float] | None = None,
        **_: object,
    ) -> MemoryPost:
        post = MemoryPost(
            id=self._next_id,
            topic=topic,
            custom_topic=custom_topic,
            text=text,
            embedding=embedding,
        )
        self._next_id += 1
        self.posts.append(post)
        return post

    async def list_by_topic(
        self,
        *,
        topic: str,
        custom_topic: str | None = None,
        limit: int = 20,
    ) -> list[MemoryPost]:
        posts = [post for post in self.posts if post.topic == topic]
        if custom_topic is not None:
            posts = [post for post in posts if post.custom_topic == custom_topic]
        return list(reversed(posts))[:limit]

    async def delete_by_id(self, post_id: int) -> bool:
        for index, post in enumerate(self.posts):
            if post.id == post_id:
                del self.posts[index]
                return True
        return False

    async def find_similar(
        self,
        *,
        topic: str,
        query_embedding: list[float],
        custom_topic: str | None = None,
        limit: int = 5,
    ) -> list[MemoryPost]:
        return await self.list_by_topic(topic=topic, custom_topic=custom_topic, limit=limit)


class InMemoryGenerationLogsRepository:
    def __init__(self) -> None:
        self.logs: list[MemoryGenerationLog] = []
        self._next_id = 1

    async def add_log(
        self,
        *,
        topic: str,
        user_request: str,
        generated_text: str | None,
        status: str,
        custom_topic: str | None = None,
        prompt: str | None = None,
        **_: object,
    ) -> MemoryGenerationLog:
        log = MemoryGenerationLog(
            id=self._next_id,
            topic=topic,
            custom_topic=custom_topic,
            user_request=user_request,
            prompt=prompt,
            generated_text=generated_text,
            status=status,
        )
        self._next_id += 1
        self.logs.append(log)
        return log


posts_repository = InMemoryPostsRepository()
generation_logs_repository = InMemoryGenerationLogsRepository()
