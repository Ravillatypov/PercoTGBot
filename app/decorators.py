from aiogram.types import Message, CallbackQuery

from app.settings import ADMIN_USERNAME, bot, logger


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
