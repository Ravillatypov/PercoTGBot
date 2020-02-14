import re
from typing import Union, List, Tuple

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from app import settings
from app.const import SELECTED_LABEL, NOT_SELECTED_LABEL
from app.models import User, Door
from app.settings import bot


def get_phone(text: str) -> str:
    text = text.replace(' ', '').replace('-', '')
    g = re.search(r'\d{10}', text)
    if g is None:
        return ''
    return '7' + g.group()


async def get_user_doors_markup(chat_id: int, user: User = None) -> InlineKeyboardMarkup:
    markup = InlineKeyboardMarkup(row_width=1)
    if not user:
        user = await User.get(chat_id=chat_id)
    user_doors_ids = await user.doors.all().values_list('id', flat=True)
    doors = await Door.all()
    for door in doors:
        marker = 0 if door.id in user_doors_ids else 1
        label = NOT_SELECTED_LABEL if marker else SELECTED_LABEL
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


async def get_user_available_doors_markup(chat_id: int, user: User = None) -> List[Tuple[str, InlineKeyboardMarkup]]:
    if not user:
        user = await User.get(chat_id=chat_id)
    if not user:
        return []
    if user.is_admin:
        doors = await Door.all()
    else:
        doors = await user.doors.all()
    result = []
    for door in doors:
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton('Открыть', callback_data=f'door_open_{door.id}'))
        markup.add(InlineKeyboardButton('Пропустить', callback_data=f'door_skip_{door.id}'))
        markup.add(InlineKeyboardButton('Закрыть', callback_data=f'door_close_{door.id}'))
        result.append((f'{door.name}', markup))
    return result


async def send_available_doors(chat_id: int):
    messages = await get_user_available_doors_markup(chat_id)
    if not messages:
        await bot.send_message(chat_id, 'Извините, у вас нет прав на управление дверьми')
    for msg, markup in messages:
        await bot.send_message(chat_id, msg, reply_markup=markup)


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
    markup.add(InlineKeyboardButton('Отмена', callback_data=f'cancel'))
    return markup if users_count else None


async def send_user_edit_message(user: User, admin_chat_id: int, is_new=False):
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton('Разрешить', callback_data=f'user_activate_{user.chat_id}_1'))
    markup.add(InlineKeyboardButton('Запретить', callback_data=f'user_activate_{user.chat_id}_0'))
    markup.add(InlineKeyboardButton('Отмена', callback_data=f'cancel'))
    msg = ''
    if is_new:
        msg = 'Новый пользователь: '
    username = f' - @{user.username}' if user.username else ''
    await bot.send_message(
        admin_chat_id,
        f'{msg}{user.full_name} {username}\n',
        reply_markup=markup
    )


async def check_admin_user():
    if not settings.ADMIN_CHAT_ID:
        admin = await User.get_or_none(username=settings.ADMIN_USERNAME)
        if admin:
            settings.ADMIN_CHAT_ID = admin.chat_id
