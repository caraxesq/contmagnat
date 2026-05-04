import json
import math
import re
from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.db.file_storage import FilePostsRepository
from app.services.topic_registry import TopicRegistry, _safe_dir_name


@dataclass(frozen=True)
class RagBuildResult:
    indexed_count: int


@dataclass(frozen=True)
class RagExample:
    post_id: int
    text: str
    score: float


class RagIndexService:
    def __init__(self, base_dir: str | Path) -> None:
        self.base_dir = Path(base_dir)
        self.repository = FilePostsRepository(self.base_dir)
        self.registry = TopicRegistry(self.base_dir)

    async def rebuild_collection(
        self,
        *,
        topic: str,
        custom_topic: str | None = None,
        style_scope: str = "topic",
    ) -> RagBuildResult:
        posts = await self.repository.list_by_topic(
            topic=topic,
            custom_topic=custom_topic,
            limit=100_000,
            style_scope=style_scope,
        )
        posts = list(reversed(posts))
        items = [_index_item(post) for post in posts]
        self._write_index(
            topic=topic,
            custom_topic=custom_topic,
            style_scope=style_scope,
            items=items,
        )
        return RagBuildResult(indexed_count=len(items))

    async def rebuild_all(self) -> RagBuildResult:
        total = 0
        for topic in self.registry.list_topics():
            result = await self.rebuild_collection(topic=topic)
            total += result.indexed_count
        for profile in self.registry.list_profiles():
            result = await self.rebuild_collection(topic=profile, style_scope="profile")
            total += result.indexed_count
        return RagBuildResult(indexed_count=total)

    async def find_examples(
        self,
        *,
        topic: str,
        user_request: str,
        custom_topic: str | None = None,
        style_scope: str = "topic",
        limit: int = 8,
    ) -> list[RagExample]:
        index = self._read_index(topic=topic, custom_topic=custom_topic, style_scope=style_scope)
        items = index.get("items", [])
        if not isinstance(items, list) or not items:
            return []

        query_terms = Counter(_tokenize(user_request))
        scored: list[tuple[float, dict[str, Any]]] = []
        for item in items:
            if not isinstance(item, dict):
                continue
            term_frequencies = item.get("term_frequencies", {})
            if not isinstance(term_frequencies, dict):
                term_frequencies = {}
            score = _score(query_terms, term_frequencies)
            scored.append((score, item))

        similar = [
            (score, item)
            for score, item in sorted(
                scored,
                key=lambda pair: (pair[0], _created_at(pair[1])),
                reverse=True,
            )
            if score > 0
        ]
        fresh = sorted(scored, key=lambda pair: _created_at(pair[1]), reverse=True)

        selected: list[tuple[float, dict[str, Any]]] = []
        seen_ids: set[int] = set()
        for score, item in [*similar, *fresh]:
            post_id = int(item["post_id"])
            if post_id in seen_ids:
                continue
            selected.append((score, item))
            seen_ids.add(post_id)
            if len(selected) >= limit:
                break

        return [
            RagExample(post_id=int(item["post_id"]), text=str(item["text"]), score=score)
            for score, item in selected
        ]

    def _index_path(
        self,
        *,
        topic: str,
        custom_topic: str | None = None,
        style_scope: str = "topic",
    ) -> Path:
        collection = "profiles" if style_scope == "profile" else "topics"
        name = custom_topic or topic
        return self.base_dir / collection / _safe_dir_name(name) / "rag_index.json"

    def _read_index(
        self,
        *,
        topic: str,
        custom_topic: str | None = None,
        style_scope: str = "topic",
    ) -> dict[str, Any]:
        path = self._index_path(topic=topic, custom_topic=custom_topic, style_scope=style_scope)
        if not path.exists():
            return {"items": []}
        return dict(json.loads(path.read_text(encoding="utf-8")))

    def _write_index(
        self,
        *,
        topic: str,
        custom_topic: str | None = None,
        style_scope: str = "topic",
        items: list[dict[str, Any]],
    ) -> None:
        path = self._index_path(topic=topic, custom_topic=custom_topic, style_scope=style_scope)
        path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "topic": topic,
            "custom_topic": custom_topic,
            "style_scope": style_scope,
            "rebuilt_at": datetime.now(timezone.utc).isoformat(),
            "items": items,
        }
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _index_item(post: Any) -> dict[str, Any]:
    term_frequencies = Counter(_tokenize(post.text))
    return {
        "post_id": post.id,
        "text": post.text,
        "created_at": post.created_at.isoformat(),
        "source_type": post.source_type,
        "source_title": post.source_title,
        "term_frequencies": dict(term_frequencies),
        "keywords": [term for term, _ in term_frequencies.most_common(20)],
    }


def _tokenize(text: str) -> list[str]:
    return [
        _normalize_token(token)
        for token in re.findall(r"[a-zA-Zа-яА-ЯёЁ0-9]+", text.lower())
        if len(token) > 2
    ]


def _normalize_token(token: str) -> str:
    if re.search(r"[а-яё]", token) and len(token) > 5:
        for suffix in (
            "ами",
            "ями",
            "ого",
            "ему",
            "ыми",
            "ими",
            "ая",
            "яя",
            "ое",
            "ее",
            "ые",
            "ие",
            "ой",
            "ей",
            "ам",
            "ям",
            "ах",
            "ях",
            "ом",
            "ем",
            "ов",
            "ев",
            "а",
            "я",
            "ы",
            "и",
            "у",
            "ю",
            "е",
        ):
            if token.endswith(suffix) and len(token) - len(suffix) >= 4:
                return token[: -len(suffix)]
    return token


def _score(query_terms: Counter[str], term_frequencies: dict[str, Any]) -> float:
    if not query_terms:
        return 0.0
    score = 0.0
    for term, query_count in query_terms.items():
        try:
            post_count = float(term_frequencies.get(term, 0))
        except (TypeError, ValueError):
            post_count = 0.0
        if post_count:
            score += (1.0 + math.log(query_count)) * (1.0 + math.log(post_count))
    return score


def _created_at(item: dict[str, Any]) -> str:
    return str(item.get("created_at") or "")
