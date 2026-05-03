import re
from dataclasses import dataclass
from typing import Protocol


class PostsRepositoryProtocol(Protocol):
    async def add_post(
        self,
        *,
        topic: str,
        text: str,
        custom_topic: str | None = None,
        embedding: list[float] | None = None,
        source_type: str = "manual",
        source_title: str | None = None,
        forward_metadata: dict[str, object] | None = None,
        style_scope: str = "topic",
    ) -> object:
        pass


@dataclass(frozen=True)
class PostIngestionResult:
    created_count: int
    skipped_count: int


def normalize_post_text(text: str) -> str:
    lines = [line.strip() for line in text.strip().splitlines()]
    return "\n".join(line for line in lines if line)


def split_posts(raw_text: str) -> list[str]:
    chunks = re.split(r"\n\s*\n+", raw_text.strip())
    return [normalized for chunk in chunks if (normalized := normalize_post_text(chunk))]


class PostIngestionService:
    def __init__(self, posts_repository: PostsRepositoryProtocol) -> None:
        self.posts_repository = posts_repository

    async def ingest_text(
        self,
        *,
        topic: str,
        raw_text: str,
        custom_topic: str | None = None,
        source_type: str = "manual",
        source_title: str | None = None,
        forward_metadata: dict[str, object] | None = None,
        style_scope: str = "topic",
    ) -> PostIngestionResult:
        posts = split_posts(raw_text)
        if not posts:
            return PostIngestionResult(created_count=0, skipped_count=1)

        for text in posts:
            await self.posts_repository.add_post(
                topic=topic,
                custom_topic=custom_topic,
                text=text,
                embedding=None,
                source_type=source_type,
                source_title=source_title,
                forward_metadata=forward_metadata,
                style_scope=style_scope,
            )

        return PostIngestionResult(created_count=len(posts), skipped_count=0)
