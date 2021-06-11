from typing import Union, List

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from app import settings
from app.const import SELECTED, NOT_SELECTED
from app.models import User, Door, DoorMessage
from app.perco import PercoClient
from app.utils import send_message, delete_message, edit_message_text

_last_state_cache = {}


async def get_user_doors_markup(chat_id: int, user: User = None) -> InlineKeyboardMarkup:
    markup = InlineKeyboardMarkup(row_width=1)
    if not user:
        user = await User.get(chat_id=chat_id)
    user_doors_ids = await user.doors.all().values_list('id', flat=True)
    doors = await Door.all()
    for door in doors:
        marker = 0 if door.id in user_doors_ids else 1
        label = NOT_SELECTED if marker else SELECTED
        markup.add(InlineKeyboardButton(
            f'{label} {door.name}',
            callback_data=f'user_door_{user.chat_id}_{door.id}_{marker}'
        ))
    markup.add(InlineKeyboardButton(
        'Сохранить и отправить уведомление',
        callback_data=f'user_door_finished_{user.chat_id}'
    ))
    markup.add(InlineKeyboardButton(
        'Сохранить',
        callback_data='cancel'
    ))
    return markup


async def get_user_available_doors_markup(chat_id: int, perco: PercoClient, user: User = None) -> list:
    if not user:
        user = await User.get_or_none(chat_id=chat_id)
    if not user:
        return []
    if user.is_admin:
        doors = await Door.all()
    else:
        doors = await user.doors.all()
    result = []
    for door in doors:
        door_name = f'{perco.door_states.get(door.id, "")} {door.name}'
        markup = InlineKeyboardMarkup(
            row_width=3,
            inline_keyboard=[
                [
                    InlineKeyboardButton('Открыть', callback_data=f'door_open_{door.id}'),
                    InlineKeyboardButton('Закрыть', callback_data=f'door_close_{door.id}'),
                    InlineKeyboardButton('Пропустить', callback_data=f'door_skip_{door.id}'),
                ]
            ])
        result.append((door.id, door_name, markup))
    return result


async def send_available_doors(chat_id: int, perco: PercoClient, update=False):
    messages = await get_user_available_doors_markup(chat_id, perco)
    qs: List[DoorMessage] = await DoorMessage.filter(user__chat_id=chat_id)
    door_messages = {i.door_id: i.message_id for i in qs}

    if not messages:
        await send_message(chat_id, 'Извините, у вас нет прав на управление дверьми')

    for door_id, msg, markup in messages:
        message_id = door_messages.get(door_id)
        if message_id and not update:
            await delete_message(chat_id, message_id)

            new_message = await send_message(chat_id, msg, reply_markup=markup)
            if new_message:
                await DoorMessage.filter(
                    user_id=chat_id,
                    message_id=message_id,
                    door_id=door_id
                ).update(message_id=new_message.message_id)

        elif not message_id:
            new_message = await send_message(chat_id, msg, reply_markup=markup)
            if new_message:
                await DoorMessage.create(user_id=chat_id, message_id=new_message.message_id, door_id=door_id)

        elif _last_state_cache.get(f'{chat_id}{door_id}', '') != msg and \
                not await edit_message_text(msg, chat_id, message_id, reply_markup=markup):

            new_message = await send_message(chat_id, msg, reply_markup=markup)
            await DoorMessage.filter(user_id=chat_id, door_id=door_id).delete()
            await DoorMessage.create(user_id=chat_id, message_id=new_message.message_id, door_id=door_id)

        _last_state_cache[f'{chat_id}{door_id}'] = msg


async def get_users_markup() -> Union[InlineKeyboardMarkup, None]:
    users = await User.all()
    if not users:
        return None
    markup = InlineKeyboardMarkup(row_width=1)
    users_count = 0
    for user in users:
        if user.is_admin:
            continue
        markup.add(InlineKeyboardButton(user.full_name, callback_data=f'user_edit_{user.chat_id}'))
        users_count += 1
    markup.add(InlineKeyboardButton('Отмена', callback_data='cancel'))
    return markup if users_count else None


async def send_user_edit_message(user: User, admin_chat_id: int, is_new=False):
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton('Разрешить', callback_data=f'user_activate_{user.chat_id}_1'))
    markup.add(InlineKeyboardButton('Запретить', callback_data=f'user_activate_{user.chat_id}_0'))
    markup.add(InlineKeyboardButton('Отмена', callback_data='cancel'))
    msg = ''
    if is_new:
        msg = 'Новый пользователь: '
    username = f' - @{user.username}' if user.username else ''
    await send_message(
        admin_chat_id,
        f'{msg}{user.full_name} {username}\n',
        reply_markup=markup
    )


async def check_admin_user():
    if not settings.ADMIN_CHAT_ID:
        admin = await User.get_or_none(username=settings.ADMIN_USERNAME)
        if admin:
            settings.ADMIN_CHAT_ID = admin.chat_id
