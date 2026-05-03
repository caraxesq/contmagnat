import pytest

from app.db.memory import InMemoryGenerationLogsRepository, InMemoryPostsRepository


@pytest.mark.asyncio
async def test_in_memory_posts_repository_saves_and_lists_posts_by_topic() -> None:
    repository = InMemoryPostsRepository()

    await repository.add_post(topic="дом", text="Пост про дом")
    await repository.add_post(topic="красота", text="Пост про красоту")

    posts = await repository.list_by_topic(topic="дом")

    assert [post.text for post in posts] == ["Пост про дом"]


@pytest.mark.asyncio
async def test_in_memory_generation_logs_repository_stores_requests() -> None:
    repository = InMemoryGenerationLogsRepository()

    await repository.add_log(
        topic="здоровье",
        user_request="Пост про сон",
        generated_text="Ответ",
        status="mock",
    )

    assert repository.logs[0].user_request == "Пост про сон"
    assert repository.logs[0].generated_text == "Ответ"
