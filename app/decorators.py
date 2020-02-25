from aiogram.types import Message, CallbackQuery

from app.models import User
from app.settings import ADMIN_USERNAME, logger
from app.utils import delete_message


def admin(func):
    async def wrapper(*args, **kwargs):
        message = args[0]
        if isinstance(message, CallbackQuery):
            message = message.message
        if not isinstance(message, Message):
            logger.info(f'func: {func.__name__}, args: {args}')
            return
        if not message or message.chat.username != ADMIN_USERNAME:
            return await message.reply('У вас не достаточно прав для данной операции')
        logger.info(f'args: {args}, kwargs: {kwargs}')
        return await func(*args, **kwargs)
    return wrapper


def check_permission(func):
    async def wrapper(*args, **kwargs):
        callback = args[0]
        if isinstance(callback, CallbackQuery) and callback.message.chat.username != ADMIN_USERNAME:
            *_, door_id = callback.data.split('_')
            user_doors = await User.filter(chat_id=callback.message.chat.id).values_list('doors__id', flat=True)
            if int(door_id) not in user_doors:
                return await delete_message(callback.message.chat.id, callback.message.message_id)
        return await func(*args, **kwargs)
    return wrapper
