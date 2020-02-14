from aiogram.types import Message

from app.models import User
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
