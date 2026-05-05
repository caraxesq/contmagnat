from app.services.prompt_builder import build_generation_prompt


def test_build_generation_prompt_contains_smm_er_instructions_and_examples() -> None:
    prompt = build_generation_prompt(
        topic="красота",
        user_request="Пост про уход за кожей зимой",
        style_examples=["Пример 1", "Пример 2"],
    )

    assert "Ты — опытный SMM-копирайтер" in prompt
    assert "## КОНТЕКСТ" in prompt
    assert "красота" in prompt
    assert "Пост про уход за кожей зимой" in prompt
    assert "## ПРИМЕРЫ ДЛЯ АНАЛИЗА СТИЛЯ" in prompt
    assert "Пример 1" in prompt
    assert "Пример 2" in prompt
    assert "## ПРАВИЛА ВЫСОКОГО ER" in prompt
    assert "Первая строка должна остановить скролл" in prompt
    assert "Не копируй" in prompt
    assert "Только сам пост, без пояснений" in prompt


def test_build_generation_prompt_handles_missing_examples() -> None:
    prompt = build_generation_prompt(
        topic="кастом: финансы",
        user_request="Пост про накопления",
        style_examples=[],
    )

    assert "кастом: финансы" in prompt
    assert "Пост про накопления" in prompt
    assert "Похожих постов пока нет" in prompt
