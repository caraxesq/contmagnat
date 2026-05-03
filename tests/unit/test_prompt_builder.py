from app.services.prompt_builder import build_generation_prompt


def test_build_generation_prompt_contains_topic_request_examples_and_copy_warning() -> None:
    prompt = build_generation_prompt(
        topic="красота",
        user_request="Пост про уход за кожей зимой",
        style_examples=["Пример 1", "Пример 2"],
    )

    assert "красота" in prompt
    assert "Пост про уход за кожей зимой" in prompt
    assert "Пример 1" in prompt
    assert "Пример 2" in prompt
    assert "Не копируй" in prompt


def test_build_generation_prompt_handles_missing_examples() -> None:
    prompt = build_generation_prompt(
        topic="кастом: финансы",
        user_request="Пост про накопления",
        style_examples=[],
    )

    assert "кастом: финансы" in prompt
    assert "Пост про накопления" in prompt
    assert "Похожих постов пока нет" in prompt
