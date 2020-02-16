from asyncio import sleep

from app.helpers import send_available_doors
from app.models import DoorMessage
from app.settings import logger


async def update_messages():
    logger.info('update messages is started')
    while True:
        chats = await DoorMessage.all().distinct().values_list('user__chat_id', flat=True)
        for chat in chats:
            try:
                await send_available_doors(chat, True)
            except Exception as err:
                logger.info(f'Error: {err}')
        await sleep(3)
