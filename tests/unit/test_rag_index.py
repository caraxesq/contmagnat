import json

import pytest

from app.db.file_storage import FilePostsRepository
from app.services.rag import RagIndexService


@pytest.mark.asyncio
async def test_rag_index_builds_index_from_topic_posts(tmp_path) -> None:
    repository = FilePostsRepository(tmp_path)
    await repository.add_post(topic="кулинария", text="Паста с томатами и базиликом")

    service = RagIndexService(tmp_path)
    result = await service.rebuild_collection(topic="кулинария")

    index_path = tmp_path / "topics" / "кулинария" / "rag_index.json"
    data = json.loads(index_path.read_text(encoding="utf-8"))
    assert result.indexed_count == 1
    assert data["items"][0]["post_id"] == 1
    assert data["items"][0]["term_frequencies"]["паста"] == 1


@pytest.mark.asyncio
async def test_rag_index_returns_similar_posts_before_fresh_posts(tmp_path) -> None:
    repository = FilePostsRepository(tmp_path)
    await repository.add_post(topic="кулинария", text="Старый пост про завтрак и овсянку")
    await repository.add_post(topic="кулинария", text="Свежий пост про ремонт кухни")
    await repository.add_post(topic="кулинария", text="Пост про быстрый завтрак с яйцами")
    service = RagIndexService(tmp_path)
    await service.rebuild_collection(topic="кулинария")

    examples = await service.find_examples(topic="кулинария", user_request="идеи для завтрака")

    assert [example.post_id for example in examples[:2]] == [3, 1]
    assert 2 in [example.post_id for example in examples]


@pytest.mark.asyncio
async def test_rag_index_does_not_mix_topics_and_profiles(tmp_path) -> None:
    repository = FilePostsRepository(tmp_path)
    await repository.add_post(topic="дом", text="Пост про уютный завтрак дома")
    await repository.add_post(
        topic="Канал еды",
        text="Профильный пост про завтрак",
        style_scope="profile",
    )
    service = RagIndexService(tmp_path)
    await service.rebuild_collection(topic="дом")
    await service.rebuild_collection(topic="Канал еды", style_scope="profile")

    topic_examples = await service.find_examples(topic="дом", user_request="завтрак")
    profile_examples = await service.find_examples(
        topic="Канал еды",
        user_request="завтрак",
        style_scope="profile",
    )

    assert [example.text for example in topic_examples] == ["Пост про уютный завтрак дома"]
    assert [example.text for example in profile_examples] == ["Профильный пост про завтрак"]


@pytest.mark.asyncio
async def test_rag_index_returns_empty_list_for_empty_collection(tmp_path) -> None:
    service = RagIndexService(tmp_path)

    examples = await service.find_examples(topic="красота", user_request="уход")

    assert examples == []
