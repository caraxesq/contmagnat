STANDARD_TOPICS: tuple[str, ...] = (
    "кулинария",
    "отношения",
    "здоровье",
    "красота",
    "дом",
)

CUSTOM_TOPIC = "кастом"
PROFILE_BUTTON_PREFIX = "Профиль: "
BACK_TO_MAIN_MENU = "В главное меню"
BACK_TO_ADMIN_MENU = "В главное меню Админки"

MAIN_MENU_SELECT_TOPIC = "Выбрать тематику"
MAIN_MENU_GENERATE = "Сгенерировать пост"
MAIN_MENU_EDIT = "Редактировать пост"
MAIN_MENU_REGENERATE = "Сгенерировать заново"
MAIN_MENU_ABOUT = "О боте"
MAIN_MENU_ADMIN = "Админка"

MAIN_MENU_UPLOAD = "Загрузить посты"

ADMIN_MENU_SELECT_TOPIC = "Выбрать тематику"
ADMIN_MENU_ADD_TOPIC = "Добавить тематику"
ADMIN_MENU_ADD_POSTS = "Добавить посты"
ADMIN_MENU_CHECK_DATA = "Проверить данные"
ADMIN_MENU_ADD_PROFILE = "Добавить профиль канала"
ADMIN_MENU_SELECT_PROFILE = "Выбрать профиль канала"
ADMIN_MENU_ADD_PROFILE_POSTS = "Добавить посты в профиль"
ADMIN_MENU_CHECK_PROFILE = "Проверить профиль"
ADMIN_MENU_SAVE_AND_TRAIN = "Сохранить и обучить"


def is_standard_topic(topic: str) -> bool:
    return topic in STANDARD_TOPICS


def all_topic_buttons() -> tuple[str, ...]:
    return (*STANDARD_TOPICS, CUSTOM_TOPIC)
