from aiogram.types import Message

from app.models import User, Door
from app.perco import PercoClient
from app.settings import dp, ADMIN_USERNAME


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
    perco = PercoClient()
    await perco.login()
    doors = await perco.get_doors()
    for data in doors:
        await Door.get_or_create(id=data.get('id', 0), name=data.get('name', '-'))


@dp.message_handler(commands=['getDoors'])
async def get_doors(message: Message):
    if message.chat.username == ADMIN_USERNAME:
        doors = await Door.all()
        await message.reply(', '.join((i.name for i in doors)))
