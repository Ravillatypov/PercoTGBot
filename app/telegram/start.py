from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery

from app.models import User, Door
from app.perco import PercoClient
from app.settings import dp, ADMIN_USERNAME, bot

perco = PercoClient()


@dp.message_handler(commands=['start'])
async def start(message: Message):
    user = await User.filter(chat_id=message.chat.id).first()
    if user:
        return await message.reply(f'С возвращением {user.full_name}!')
    await User.get_or_create(
        chat_id=message.chat.id,
        username=message.chat.username,
        first_name=message.chat.first_name,
        last_name=message.chat.last_name,
        is_active=message.chat.username == ADMIN_USERNAME or None,
    )
    msg = 'Я Perco-бот! Могу для вас открыть или закрыть дверь.\n'
    if message.chat.username == ADMIN_USERNAME:
        msg += 'Вы администратор, поздавляю!'
    else:
        msg += 'После подверждения учетной записи администратором я вас проинформирую'
    await message.reply(msg)


@dp.message_handler(commands=['updateDoors'])
async def update_doors(message: Message):
    if message.chat.username != ADMIN_USERNAME:
        return await message.reply('У вас не достаточно прав для данной операции')
    doors = await perco.get_doors()
    for data in doors:
        await Door.get_or_create(id=data.get('id', 0), defaults={'name': data.get('name', '-')})


@dp.message_handler(commands=['getDoors'])
async def get_doors(message: Message):
    if message.chat.username == ADMIN_USERNAME:
        doors = await Door.all()
        markup = InlineKeyboardMarkup(row_width=1)
        for door in doors:
            markup.add(InlineKeyboardButton(f'Открыть "{door.name}"', callback_data=f'door_open_{door.id}'))
            markup.add(InlineKeyboardButton(f'Закрыть "{door.name}"', callback_data=f'door_close_{door.id}'))
        await bot.send_message(message.chat.id, 'Доступные двери:', reply_markup=markup)


@dp.callback_query_handler(lambda x: 'door_open_' in x.data)
async def callback_door_open(callback_query: CallbackQuery):
    door_id = int(callback_query.data.replace('door_open_', ''))
    await perco.open_door(door_id)
    await bot.answer_callback_query(callback_query.id, 'Дверь открыта')


@dp.callback_query_handler(lambda x: 'door_close_' in x.data)
async def callback_door_close(callback_query: CallbackQuery):
    door_id = int(callback_query.data.replace('door_close_', ''))
    await perco.close_door(door_id)
    await bot.answer_callback_query(callback_query.id, 'Дверь закрыта')

