from asyncio import sleep

from app.helpers import send_available_doors
from app.models import DoorMessage
from app.settings import logger, perco


async def update_messages():
    logger.info('update messages is started')
    await sleep(10)

    chats = await DoorMessage.all().distinct().values_list('user__chat_id', flat=True)
    for chat in chats:
        try:
            await send_available_doors(chat, True)
        except Exception as err:
            logger.info(f'Error: {err}')

    while True:
        await sleep(1)
        if not perco.last_updated:
            continue
        chats = await DoorMessage.filter(
            door_id__in=perco.last_updated
        ).distinct().values_list('user__chat_id', flat=True)
        for chat in chats:
            try:
                await send_available_doors(chat, True)
            except Exception as err:
                logger.info(f'Error: {err}')
