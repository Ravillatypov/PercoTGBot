from aiogram.dispatcher.filters.state import StatesGroup, State

cancel = State('cancel')


class AuthenticateForm(StatesGroup):
    phone = State()
    code = State()


class AdminActionForm(StatesGroup):
    menu_action = State()


class DoorAddForm(StatesGroup):
    name = State()
    id = State()


class DoorEditForm(StatesGroup):
    add_to_groups = State()


class GroupEditForm(StatesGroup):
    select_group = State()
    select_members = State()
    select_doors = State()


class GroupDeleteForm(StatesGroup):
    select_group = State()
    confirm = State()


class UserAddForm(StatesGroup):
    name = State()
    phone = State()
    group = State()
