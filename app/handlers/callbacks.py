from asyncio import sleep
from datetime import datetime, timedelta

from aiogram.types import CallbackQuery

from app import settings
from app.decorators import admin, check_permission
from app.helpers import (get_user_doors_markup, send_available_doors, send_user_edit_message)
from app.models import User, Door
from app.settings import dp, logger
from app.utils import send_message, delete_message, answer_callback_query, edit_message_reply_markup, get_int


@dp.callback_query_handler(lambda x: 'door_open_' in x.data)
@check_permission
async def callback_door_open(callback_query: CallbackQuery, **kwargs):
    logger.info(f'callback data: {callback_query.data}')
    door_id = get_int(callback_query.data.replace('door_open_', ''))
    perco = dp['perco']
    await perco.open_door(door_id)
    is_closed = await perco.door_is_closed(door_id)
    if is_closed is None:
        message = 'Не удалось подключиться к Perco-WEB'
    elif is_closed:
        message = 'Не удалось открыть'
    else:
        message = 'Дверь открыта'
    await answer_callback_query(callback_query.id, message)


@dp.callback_query_handler(lambda x: 'door_close_' in x.data)
@check_permission
async def callback_door_close(callback_query: CallbackQuery, **kwargs):
    logger.info(f'callback data: {callback_query.data}')
    door_id = get_int(callback_query.data.replace('door_close_', ''))
    perco = dp['perco']
    await perco.close_door(door_id)
    is_closed = await perco.door_is_closed(door_id)
    if is_closed is None:
        message = 'Не удалось подключиться к Perco-WEB'
    elif is_closed:
        message = 'Дверь закрыта'
    else:
        message = 'Не удалось закрыть'
    await answer_callback_query(callback_query.id, message)


@dp.callback_query_handler(lambda x: 'door_skip_' in x.data)
@check_permission
async def callback_door_skip(callback_query: CallbackQuery, **kwargs):
    logger.info(f'callback data: {callback_query.data}')
    door_id = get_int(callback_query.data.replace('door_skip_', ''))
    perco = dp['perco']
    await perco.open_door(door_id)
    await answer_callback_query(callback_query.id, 'Дверь открыта, через 8 сек закроется автоматически')
    await sleep(8)
    await perco.close_door(door_id)


@dp.callback_query_handler(lambda x: 'user_activate_' in x.data)
@admin
async def callback_user_activate(callback_query: CallbackQuery, **kwargs):
    logger.info(f'callback data: {callback_query.data}')
    chat_id, activate = callback_query.data.replace('user_activate_', '').split('_')
    user = await User.get_or_none(chat_id=get_int(chat_id))
    if not user:
        logger.warning(f'bad callback data: {callback_query.data}')
        return
    user.is_active = activate == '1'
    await user.save(update_fields=['is_active'])
    await delete_message(callback_query.message.chat.id, callback_query.message.message_id)

    if user.is_active:
        markup = await get_user_doors_markup(user.chat_id, user)
        await send_message(
            callback_query.message.chat.id,
            f'Какие двери доступны для пользователя {user.full_name}?',
            reply_markup=markup
        )


@dp.callback_query_handler(lambda x: 'user_door_' in x.data)
@admin
async def callback_user_door_edit(callback_query: CallbackQuery, **kwargs):
    logger.info(f'callback data: {callback_query.data}')
    if 'finished' in callback_query.data:
        return await callback_user_door_edit_finished(callback_query, **kwargs)

    chat_id, door_id, state = callback_query.data.replace('user_door_', '').split('_')
    door = await Door.get(id=get_int(door_id))
    user = await User.get(chat_id=get_int(chat_id))

    if state == '0':
        await user.doors.remove(door)
    else:
        await user.doors.add(door)

    markup = await get_user_doors_markup(user.chat_id, user)
    await edit_message_reply_markup(
        callback_query.message.chat.id,
        callback_query.message.message_id,
        callback_query.inline_message_id,
        markup
    )


async def callback_user_door_edit_finished(callback_query: CallbackQuery, **kwargs):
    chat_id = get_int(callback_query.data.replace('user_door_finished_', ''))
    user = await User.get_or_none(chat_id=chat_id)

    if user and user.updated_at and datetime.utcnow() - user.updated_at.replace(tzinfo=None) < timedelta(minutes=5):
        await send_message(chat_id, 'Поздравляю, ваша учетная запись активирована!')

    await send_available_doors(chat_id, dp['perco'])
    return await delete_message(callback_query.message.chat.id, callback_query.message.message_id)


@dp.callback_query_handler(lambda x: x.data == 'cancel')
async def callback_cancel(callback_query: CallbackQuery):
    await delete_message(callback_query.message.chat.id, callback_query.message.message_id)


@dp.callback_query_handler(lambda x: 'user_edit_' in x.data)
@admin
async def callback_user_edit(callback_query: CallbackQuery, **kwargs):
    await delete_message(callback_query.message.chat.id, callback_query.message.message_id)
    chat_id = get_int(callback_query.data.replace('user_edit_', ''))
    user = await User.get(chat_id=chat_id)
    await send_user_edit_message(user, settings.ADMIN_CHAT_ID)
