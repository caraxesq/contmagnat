import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.services.topic_registry import _safe_dir_name


@dataclass
class FilePost:
    id: int
    topic: str
    text: str
    custom_topic: str | None = None
    embedding: list[float] | None = None
    source_type: str = "manual"
    source_title: str | None = None
    forward_metadata: dict[str, Any] | None = None
    style_scope: str = "topic"
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class FilePostsRepository:
    def __init__(self, base_dir: str | Path) -> None:
        self.base_dir = Path(base_dir)

    async def add_post(
        self,
        *,
        topic: str,
        text: str,
        custom_topic: str | None = None,
        embedding: list[float] | None = None,
        source_type: str = "manual",
        source_title: str | None = None,
        forward_metadata: dict[str, Any] | None = None,
        style_scope: str = "topic",
    ) -> FilePost:
        posts = self._read_posts(topic=topic, custom_topic=custom_topic, style_scope=style_scope)
        next_id = self._next_id()
        post = FilePost(
            id=next_id,
            topic=topic,
            custom_topic=custom_topic,
            text=text,
            embedding=embedding,
            source_type=source_type,
            source_title=source_title,
            forward_metadata=forward_metadata,
            style_scope=style_scope,
        )
        posts.append(post)
        self._write_posts(topic=topic, custom_topic=custom_topic, style_scope=style_scope, posts=posts)
        return post

    async def list_by_topic(
        self,
        *,
        topic: str,
        custom_topic: str | None = None,
        limit: int = 20,
        style_scope: str = "topic",
    ) -> list[FilePost]:
        posts = self._read_posts(topic=topic, custom_topic=custom_topic, style_scope=style_scope)
        return list(reversed(posts))[:limit]

    async def delete_by_id(self, post_id: int) -> bool:
        for path in self.base_dir.glob("**/posts.jsonl"):
            posts = self._read_posts_from_path(path)
            kept = [post for post in posts if post.id != post_id]
            if len(kept) != len(posts):
                self._write_posts_to_path(path, kept)
                return True
        return False

    async def find_similar(
        self,
        *,
        topic: str,
        query_embedding: list[float],
        custom_topic: str | None = None,
        limit: int = 5,
        style_scope: str = "topic",
    ) -> list[FilePost]:
        return await self.list_by_topic(
            topic=topic,
            custom_topic=custom_topic,
            limit=limit,
            style_scope=style_scope,
        )

    def _next_id(self) -> int:
        max_id = 0
        for path in self.base_dir.glob("**/posts.jsonl"):
            for post in self._read_posts_from_path(path):
                max_id = max(max_id, post.id)
        return max_id + 1

    def _posts_path(
        self,
        *,
        topic: str,
        custom_topic: str | None = None,
        style_scope: str = "topic",
    ) -> Path:
        collection = "profiles" if style_scope == "profile" else "topics"
        name = custom_topic or topic
        return self.base_dir / collection / _safe_dir_name(name) / "posts.jsonl"

    def _read_posts(
        self,
        *,
        topic: str,
        custom_topic: str | None = None,
        style_scope: str = "topic",
    ) -> list[FilePost]:
        return self._read_posts_from_path(
            self._posts_path(topic=topic, custom_topic=custom_topic, style_scope=style_scope)
        )

    def _write_posts(
        self,
        *,
        topic: str,
        custom_topic: str | None = None,
        style_scope: str = "topic",
        posts: list[FilePost],
    ) -> None:
        self._write_posts_to_path(
            self._posts_path(topic=topic, custom_topic=custom_topic, style_scope=style_scope),
            posts,
        )

    @staticmethod
    def _read_posts_from_path(path: Path) -> list[FilePost]:
        if not path.exists():
            return []
        posts: list[FilePost] = []
        for line in path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            data = json.loads(line)
            created_at = data.get("created_at")
            posts.append(
                FilePost(
                    id=int(data["id"]),
                    topic=str(data["topic"]),
                    custom_topic=data.get("custom_topic"),
                    text=str(data["text"]),
                    embedding=data.get("embedding"),
                    source_type=str(data.get("source_type", "manual")),
                    source_title=data.get("source_title"),
                    forward_metadata=data.get("forward_metadata"),
                    style_scope=str(data.get("style_scope", "topic")),
                    created_at=datetime.fromisoformat(created_at)
                    if created_at
                    else datetime.now(timezone.utc),
                )
            )
        return posts

    @staticmethod
    def _write_posts_to_path(path: Path, posts: list[FilePost]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        lines = []
        for post in posts:
            lines.append(
                json.dumps(
                    {
                        "id": post.id,
                        "topic": post.topic,
                        "custom_topic": post.custom_topic,
                        "text": post.text,
                        "embedding": post.embedding,
                        "source_type": post.source_type,
                        "source_title": post.source_title,
                        "forward_metadata": post.forward_metadata,
                        "style_scope": post.style_scope,
                        "created_at": post.created_at.isoformat(),
                    },
                    ensure_ascii=False,
                )
            )
        path.write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")


class FileGenerationLogsRepository:
    def __init__(self, base_dir: str | Path) -> None:
        self.path = Path(base_dir) / "generation_logs.jsonl"

    async def add_log(
        self,
        *,
        topic: str,
        user_request: str,
        generated_text: str | None,
        status: str,
        custom_topic: str | None = None,
        prompt: str | None = None,
        **kwargs: object,
    ) -> object:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        existing = self.path.read_text(encoding="utf-8") if self.path.exists() else ""
        record = {
            "topic": topic,
            "custom_topic": custom_topic,
            "user_request": user_request,
            "prompt": prompt,
            "generated_text": generated_text,
            "status": status,
            "metadata": kwargs,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        self.path.write_text(
            existing + json.dumps(record, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        return record
