from asyncio import ensure_future

from aiogram.dispatcher import Dispatcher
from aiogram.utils import executor
from tortoise import Tortoise

from app import settings
from app.helpers import check_admin_user
from app.settings import perco
from app.tasks import update_messages
from app.telegram import dp


async def on_startup(dispatcher: Dispatcher):
    await Tortoise.init(db_url=settings.DB_DSN, modules={'models': ['app.models']})
    await Tortoise.generate_schemas()
    await check_admin_user()
    dispatcher['tasks'] = []
    dispatcher['tasks'].append(ensure_future(perco.states_updater_task()))
    dispatcher['tasks'].append(ensure_future(update_messages()))


async def on_shutdown(dispatcher: Dispatcher):
    await Tortoise.close_connections()
    for task in dispatcher['tasks']:
        task.cancel()


if __name__ == '__main__':
    executor.start_polling(dp, on_startup=on_startup, on_shutdown=on_shutdown)
