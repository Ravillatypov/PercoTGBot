from asyncio import ensure_future

from aiogram.dispatcher import Dispatcher
from aiogram.utils import executor
from tortoise import Tortoise

from app import settings
from app.helpers import check_admin_user
from app.perco import PercoClient
from app.settings import WEBHOOK_HOST, WEBHOOK_PATH, PERCO_PASS, PERCO_LOGIN, PERCO_URL, WEB_PORT
from app.tasks import update_messages, force_update_doors_on_chat
from app.handlers import dp


async def on_startup(dispatcher: Dispatcher):
    await Tortoise.init(db_url=settings.DB_DSN, modules={'models': ['app.models']})
    await Tortoise.generate_schemas()
    await check_admin_user()
    perco = PercoClient(PERCO_URL, PERCO_LOGIN, PERCO_PASS)
    dispatcher['perco'] = perco
    dispatcher['tasks'] = []
    dispatcher['tasks'].append(ensure_future(perco.states_updater_task()))
    dispatcher['tasks'].append(ensure_future(perco.check_events()))
    dispatcher['tasks'].append(ensure_future(update_messages(perco)))
    dispatcher['tasks'].append(ensure_future(force_update_doors_on_chat(perco)))


async def on_shutdown(dispatcher: Dispatcher):
    await Tortoise.close_connections()
    for task in dispatcher.get('tasks', []):
        task.cancel()


if __name__ == '__main__':
    if WEBHOOK_HOST:
        executor.start_webhook(
            dispatcher=dp,
            webhook_path=WEBHOOK_PATH,
            on_startup=on_startup,
            on_shutdown=on_shutdown,
            skip_updates=False,
            port=WEB_PORT,
        )
    else:
        executor.start_polling(dp, on_startup=on_startup, on_shutdown=on_shutdown)
