from datetime import datetime, timedelta

from aiogram.types import Message, CallbackQuery

from app import settings
from app.decorators import admin
from app.helpers import (get_user_doors_markup, send_available_doors, get_users_markup, send_user_edit_message,
                         check_admin_user)
from app.models import User, Door
from app.perco import PercoClient
from app.settings import dp, ADMIN_USERNAME, bot, logger
from asyncio import sleep

perco = PercoClient()


@dp.message_handler(commands=['start'])
async def start(message: Message):
    await check_admin_user()
    user, created = await User.get_or_create(
        chat_id=message.chat.id,
        defaults={
            'username': message.chat.username or '',
            'first_name': message.chat.first_name or '',
            'last_name': message.chat.last_name or '',
            'is_active': message.chat.username == ADMIN_USERNAME or None
        }
    )
    if user.is_active:
        return await message.reply(f'С возвращением {user.full_name}!')
    msg = 'Я Perco-бот! Могу для вас открыть или закрыть дверь.\n'
    if message.chat.username == ADMIN_USERNAME:
        msg += 'Вы администратор, поздавляю!'
    else:
        msg += 'Ваш запрос ожидает подтверждения администратором.'
        if settings.ADMIN_CHAT_ID:
            await send_user_edit_message(user, settings.ADMIN_CHAT_ID, is_new=True)
    await message.reply(msg)


@dp.message_handler(commands=['updateDoors'])
@admin
async def update_doors(message: Message, **kwargs):
    doors = await perco.get_doors()
    for data in doors:
        door, _ = await Door.get_or_create(id=data.get('id', 0), defaults={'name': data.get('name', '-')})
        if door.name != data.get('name', '-'):
            door.name = data.get('name', '-')
            await door.save(update_fields=['name'])
    await message.reply('Обновил')


@dp.message_handler(commands=['doors'])
async def get_doors(message: Message):
    await send_available_doors(message.chat.id)


@dp.message_handler(commands=['users'])
@admin
async def get_users(message: Message, **kwargs):
    markup = await get_users_markup()
    if markup:
        await message.reply('Список пользователей:', reply_markup=markup)
    else:
        await message.reply('На данный момент вы единственный пользователь')


@dp.callback_query_handler(lambda x: 'door_open_' in x.data)
async def callback_door_open(callback_query: CallbackQuery):
    logger.info(f'callback data: {callback_query.data}')
    door_id = int(callback_query.data.replace('door_open_', ''))
    await perco.open_door(door_id)
    await bot.answer_callback_query(callback_query.id, 'Дверь открыта', show_alert=True)


@dp.callback_query_handler(lambda x: 'door_close_' in x.data)
async def callback_door_close(callback_query: CallbackQuery):
    logger.info(f'callback data: {callback_query.data}')
    door_id = int(callback_query.data.replace('door_close_', ''))
    await perco.close_door(door_id)
    await bot.answer_callback_query(callback_query.id, 'Дверь закрыта', show_alert=True)


@dp.callback_query_handler(lambda x: 'door_skip_' in x.data)
async def callback_door_skip(callback_query: CallbackQuery):
    logger.info(f'callback data: {callback_query.data}')
    door_id = int(callback_query.data.replace('door_skip_', ''))
    await perco.open_door(door_id)
    await bot.answer_callback_query(callback_query.id, 'Дверь открыта', show_alert=True)
    await sleep(8)
    await perco.close_door(door_id)
    await bot.answer_callback_query(callback_query.id, 'Дверь закрыта', show_alert=True)


@dp.callback_query_handler(lambda x: 'doors_refresh' == x.data)
async def callback_doors_refresh(callback_query: CallbackQuery):
    logger.info(f'callback data: {callback_query.data}')
    states = await perco.get_doors_labels()
    await bot.answer_callback_query(callback_query.id, 'данные обновлены', show_alert=True)


@dp.callback_query_handler(lambda x: 'user_activate_' in x.data)
@admin
async def callback_user_activate(callback_query: CallbackQuery, **kwargs):
    logger.info(f'callback data: {callback_query.data}')
    chat_id, activate = callback_query.data.replace('user_activate_', '').split('_')
    user = await User.get_or_none(chat_id=int(chat_id))
    if not user:
        logger.warning(f'bad callback data: {callback_query.data}')
        return
    user.is_active = activate == '1'
    await user.save(update_fields=['is_active'])
    await bot.delete_message(callback_query.message.chat.id, callback_query.message.message_id)

    if user.is_active:
        markup = await get_user_doors_markup(user.chat_id, user)
        await bot.send_message(
            callback_query.message.chat.id,
            f'Какие двери доступны для пользователя {user.full_name}?',
            reply_markup=markup
        )


@dp.callback_query_handler(lambda x: 'user_door_' in x.data)
@admin
async def callback_user_door_edit(callback_query: CallbackQuery, **kwargs):
    logger.info(f'callback data: {callback_query.data}')
    if 'finished' in callback_query.data:
        chat_id = int(callback_query.data.replace('user_door_finished_', ''))
        user = await User.get_or_none(chat_id=chat_id)
        if user and user.updated_at and datetime.now() - user.updated_at < timedelta(minutes=5):
            await bot.send_message(chat_id, 'Поздравляю, ваша учетная запись активирована!')
        await send_available_doors(chat_id)
        return await bot.delete_message(callback_query.message.chat.id, callback_query.message.message_id)
    chat_id, door_id, state = callback_query.data.replace('user_door_', '').split('_')
    door = await Door.get(id=int(door_id))
    user = await User.get(chat_id=int(chat_id))
    if state == '0':
        await user.doors.remove(door)
    else:
        await user.doors.add(door)
    markup = await get_user_doors_markup(user.chat_id, user)
    await bot.edit_message_reply_markup(
        callback_query.message.chat.id,
        callback_query.message.message_id,
        callback_query.inline_message_id,
        markup
    )


@dp.callback_query_handler(lambda x: x.data == 'cancel')
async def callback_cancel(callback_query: CallbackQuery):
    await bot.delete_message(callback_query.message.chat.id, callback_query.message.message_id)


@dp.callback_query_handler(lambda x: 'user_edit_' in x.data)
async def callback_user_edit(callback_query: CallbackQuery):
    await bot.delete_message(callback_query.message.chat.id, callback_query.message.message_id)
    chat_id = int(callback_query.data.replace('user_edit_', ''))
    user = await User.get(chat_id=chat_id)
    await send_user_edit_message(user, settings.ADMIN_CHAT_ID)
