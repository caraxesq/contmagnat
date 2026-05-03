import pytest

from app.db.file_storage import FilePostsRepository


@pytest.mark.asyncio
async def test_file_posts_repository_persists_topic_posts_between_instances(tmp_path) -> None:
    repository = FilePostsRepository(tmp_path)

    post = await repository.add_post(
        topic="кулинария",
        text="Пост про пасту",
        source_type="forward",
        source_title="Канал еды",
        forward_metadata={"chat_id": -100},
    )

    reloaded = FilePostsRepository(tmp_path)
    posts = await reloaded.list_by_topic(topic="кулинария")

    assert post.id == 1
    assert posts[0].text == "Пост про пасту"
    assert posts[0].source_type == "forward"
    assert posts[0].source_title == "Канал еды"
    assert posts[0].forward_metadata == {"chat_id": -100}


@pytest.mark.asyncio
async def test_file_posts_repository_separates_profiles_from_topics(tmp_path) -> None:
    repository = FilePostsRepository(tmp_path)

    await repository.add_post(topic="кулинария", text="Общий пост")
    await repository.add_post(
        topic="Канал красоты",
        text="Профильный пост",
        style_scope="profile",
    )

    topic_posts = await repository.list_by_topic(topic="кулинария")
    profile_posts = await repository.list_by_topic(topic="Канал красоты", style_scope="profile")

    assert [post.text for post in topic_posts] == ["Общий пост"]
    assert [post.text for post in profile_posts] == ["Профильный пост"]


@pytest.mark.asyncio
async def test_file_posts_repository_deletes_post_by_id(tmp_path) -> None:
    repository = FilePostsRepository(tmp_path)
    post = await repository.add_post(topic="дом", text="Удалить")

    deleted = await repository.delete_by_id(post.id)
    posts = await repository.list_by_topic(topic="дом")

    assert deleted is True
    assert posts == []
