from app.core.constants import CUSTOM_TOPIC, STANDARD_TOPICS, is_standard_topic


def test_standard_topics_match_mvp_list() -> None:
    assert STANDARD_TOPICS == (
        "кулинария",
        "отношения",
        "здоровье",
        "красота",
        "дом",
    )
    assert CUSTOM_TOPIC == "кастом"


def test_is_standard_topic_accepts_only_builtin_topics() -> None:
    assert is_standard_topic("здоровье") is True
    assert is_standard_topic("спорт") is False
    assert is_standard_topic("кастом") is False
