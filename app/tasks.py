from asyncio import sleep

from app.helpers import send_available_doors
from app.models import DoorMessage
from app.perco import PercoClient
from app.settings import logger


async def update_messages(perco: PercoClient):
    logger.info('update messages is started')
    await sleep(10)

    while True:
        await sleep(0.9)

        if not perco.last_updated:
            continue

        chats = await DoorMessage.filter(
            door_id__in=perco.last_updated
        ).distinct().values_list('user__chat_id', flat=True)

        for chat in chats:
            await send_available_doors(chat, perco, True)


async def force_update_doors_on_chat(perco: PercoClient):
    while True:
        await sleep(5)

        chats = await DoorMessage.filter(
            door_id__in=list(perco.door_states.keys())
        ).distinct().values_list('user__chat_id', flat=True)

        for chat in chats:
            await send_available_doors(chat, perco, True)
