from app.services.topic_registry import TopicRegistry


def test_topic_registry_creates_default_topics(tmp_path) -> None:
    registry = TopicRegistry(tmp_path)

    assert registry.list_topics() == ["кулинария", "отношения", "здоровье", "красота", "дом"]
    assert (tmp_path / "topics" / "index.json").exists()


def test_topic_registry_adds_topic_once_and_creates_folder(tmp_path) -> None:
    registry = TopicRegistry(tmp_path)

    first = registry.add_topic("маркетинг")
    second = registry.add_topic("маркетинг")

    assert first is True
    assert second is False
    assert registry.list_topics().count("маркетинг") == 1
    assert (tmp_path / "topics" / "маркетинг").is_dir()


def test_topic_registry_adds_channel_profiles_once(tmp_path) -> None:
    registry = TopicRegistry(tmp_path)

    first = registry.add_profile("Канал про красоту")
    second = registry.add_profile("Канал про красоту")

    assert first is True
    assert second is False
    assert registry.list_profiles() == ["Канал про красоту"]
    assert (tmp_path / "profiles" / "Канал про красоту").is_dir()
