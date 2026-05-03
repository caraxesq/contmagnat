from app.bot.command_parsing import parse_generate_command


def test_parse_generate_command_extracts_text_after_command() -> None:
    assert parse_generate_command("/generate пост про ужин") == "пост про ужин"


def test_parse_generate_command_handles_empty_request() -> None:
    assert parse_generate_command("/generate") == ""
