def build_generation_prompt(
    *,
    topic: str,
    user_request: str,
    style_examples: list[str],
) -> str:
    examples_block = _format_examples(style_examples)
    return (
        "Ты пишешь Telegram-пост в заданной стилистике.\n\n"
        f"Тематика: {topic}\n"
        f"Задача пользователя: {user_request}\n\n"
        "Похожие посты для анализа стиля:\n"
        f"{examples_block}\n\n"
        "Сохрани общий стиль, ритм и подачу примеров. "
        "Не копируй фразы дословно и не пересказывай примеры. "
        "Сгенерируй один готовый пост."
    )


def _format_examples(style_examples: list[str]) -> str:
    if not style_examples:
        return "Похожих постов пока нет. Опирайся только на задачу пользователя."
    return "\n\n".join(
        f"Пример {index}:\n{example}" for index, example in enumerate(style_examples, start=1)
    )
