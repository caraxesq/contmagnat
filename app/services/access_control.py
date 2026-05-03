def is_user_allowed(user_id: int, allowed_ids: tuple[int, ...]) -> bool:
    return user_id in allowed_ids
