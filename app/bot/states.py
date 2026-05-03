from aiogram.fsm.state import State, StatesGroup


class UploadStates(StatesGroup):
    choosing_topic = State()
    entering_custom_topic = State()
    waiting_posts = State()


class GenerateStates(StatesGroup):
    choosing_topic = State()
    entering_custom_topic = State()
    waiting_request = State()


class UserFlowStates(StatesGroup):
    choosing_topic = State()
    choosing_topic_for_generation = State()
    entering_custom_topic = State()
    entering_custom_topic_for_generation = State()
    waiting_request = State()
    editing_post = State()


class AdminFlowStates(StatesGroup):
    menu = State()
    entering_password = State()
    adding_topic = State()
    choosing_topic = State()
    entering_custom_topic = State()
    adding_profile = State()
    choosing_profile = State()
    waiting_posts = State()
