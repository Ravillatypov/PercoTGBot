import typing

from aiogram.types import Message, InlineKeyboardMarkup, ReplyKeyboardMarkup, ReplyKeyboardRemove, ForceReply

from app.settings import bot, logger


async def delete_message(chat_id: int, message_id: int):
    try:
        await bot.delete_message(chat_id, message_id)
    except Exception as err:
        logger.warn(f'Error on delete message: {err}')


async def send_message(chat_id: int, text: str,
                       parse_mode: typing.Union[str, None] = None,
                       disable_web_page_preview: typing.Union[bool, None] = None,
                       disable_notification: typing.Union[bool, None] = None,
                       reply_to_message_id: typing.Union[int, None] = None,
                       reply_markup: typing.Union[InlineKeyboardMarkup,
                                                  ReplyKeyboardMarkup,
                                                  ReplyKeyboardRemove,
                                                  ForceReply, None] = None) -> typing.Union[Message, None]:
    try:
        res = await bot.send_message(chat_id, text, parse_mode, disable_web_page_preview,
                                     disable_notification, reply_to_message_id, reply_markup)
    except Exception as err:
        logger.warn(f'Error on send message: {err}')
    else:
        return res


async def answer_callback_query(callback_query_id: str,
                                text: typing.Union[str, None] = None,
                                show_alert: typing.Union[bool, None] = None,
                                url: typing.Union[str, None] = None,
                                cache_time: typing.Union[int, None] = None) -> bool:
    try:
        res = await bot.answer_callback_query(callback_query_id, text, show_alert, url, cache_time)
    except Exception as err:
        logger.warn(f'Error on send answer_callback_query: {err}')
        return False
    else:
        return res


async def edit_message_text(text: str,
                            chat_id: typing.Union[int, str, None] = None,
                            message_id: typing.Union[int, None] = None,
                            inline_message_id: typing.Union[str, None] = None,
                            parse_mode: typing.Union[str, None] = None,
                            disable_web_page_preview: typing.Union[str, None] = None,
                            reply_markup: typing.Union[InlineKeyboardMarkup, None] = None) -> bool:
    try:
        res = await bot.edit_message_text(text, chat_id, message_id, inline_message_id,
                                          parse_mode, disable_web_page_preview, reply_markup)
    except Exception as err:
        logger.warn(f'Error on edit_message_text: {err}')
        return False
    else:
        return res


async def edit_message_reply_markup(chat_id: typing.Union[int, str, None] = None,
                                    message_id: typing.Union[int, None] = None,
                                    inline_message_id: typing.Union[str, None] = None,
                                    reply_markup: typing.Union[InlineKeyboardMarkup, None] = None) -> bool:
    try:
        res = await bot.edit_message_reply_markup(chat_id, message_id, inline_message_id, reply_markup)
    except Exception as err:
        logger.warn(f'Error on edit_message_reply_markup: {err}')
        return False
    else:
        return res
