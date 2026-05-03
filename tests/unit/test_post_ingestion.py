import pytest

from app.services.post_ingestion import PostIngestionService, split_posts


class FakePostsRepository:
    def __init__(self) -> None:
        self.saved: list[dict[str, str | None]] = []

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
        self.saved.append(
            {
                "topic": topic,
                "custom_topic": custom_topic,
                "text": text,
                "source_type": source_type,
                "source_title": source_title,
                "style_scope": style_scope,
            }
        )
        return object()


def test_split_posts_separates_by_blank_lines_and_normalizes_text() -> None:
    raw_text = " Первый пост  \nс переносом \n\n\n Второй пост\t\n\n"

    assert split_posts(raw_text) == ["Первый пост\nс переносом", "Второй пост"]


@pytest.mark.asyncio
async def test_ingest_posts_saves_each_post_with_topic() -> None:
    repository = FakePostsRepository()
    service = PostIngestionService(repository)

    result = await service.ingest_text(
        topic="кулинария",
        raw_text="Пост один\n\nПост два",
    )

    assert result.created_count == 2
    assert result.skipped_count == 0
    assert repository.saved == [
        {
            "topic": "кулинария",
            "custom_topic": None,
            "text": "Пост один",
            "source_type": "manual",
            "source_title": None,
            "style_scope": "topic",
        },
        {
            "topic": "кулинария",
            "custom_topic": None,
            "text": "Пост два",
            "source_type": "manual",
            "source_title": None,
            "style_scope": "topic",
        },
    ]


@pytest.mark.asyncio
async def test_ingest_posts_tracks_empty_input_as_skipped() -> None:
    repository = FakePostsRepository()
    service = PostIngestionService(repository)

    result = await service.ingest_text(topic="дом", raw_text=" \n\n ")

    assert result.created_count == 0
    assert result.skipped_count == 1
    assert repository.saved == []


@pytest.mark.asyncio
async def test_ingest_posts_passes_source_metadata_and_style_scope() -> None:
    repository = FakePostsRepository()
    service = PostIngestionService(repository)

    await service.ingest_text(
        topic="Канал красоты",
        raw_text="Профильный пост",
        source_type="forward",
        source_title="Beauty channel",
        forward_metadata={"chat_id": -100},
        style_scope="profile",
    )

    assert repository.saved == [
        {
            "topic": "Канал красоты",
            "custom_topic": None,
            "text": "Профильный пост",
            "source_type": "forward",
            "source_title": "Beauty channel",
            "style_scope": "profile",
        }
    ]
