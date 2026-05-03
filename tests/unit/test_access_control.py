from app.services.access_control import is_user_allowed


def test_user_is_allowed_when_id_is_in_whitelist() -> None:
    assert is_user_allowed(42, (1, 42, 100)) is True


def test_user_is_denied_when_id_is_not_in_whitelist() -> None:
    assert is_user_allowed(7, (1, 42, 100)) is False


def test_user_is_denied_when_whitelist_is_empty() -> None:
    assert is_user_allowed(7, ()) is False
