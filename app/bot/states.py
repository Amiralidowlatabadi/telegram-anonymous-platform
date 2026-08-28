from aiogram.fsm.state import State, StatesGroup

class PersonalChatStates(StatesGroup):
    composing_message = State()
    replying_to_message = State()

class ChannelChatStates(StatesGroup):
    composing_post = State()

class NicknameStates(StatesGroup):
    waiting_for_nickname = State()

class CustomSlugStates(StatesGroup):
    waiting_for_personal_slug = State()
    waiting_for_channel_slug = State()

class ReportStates(StatesGroup):
    waiting_for_reason = State()