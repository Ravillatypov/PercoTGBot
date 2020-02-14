from aiogram.dispatcher import Dispatcher
from aiogram.utils import executor
from tortoise import Tortoise

from app import settings
from app.helpers import check_admin_user
from app.telegram import dp


async def on_startup(dispatcher: Dispatcher):
    await Tortoise.init(db_url=settings.DB_DSN, modules={'models': ['app.models']})
    await Tortoise.generate_schemas()
    await check_admin_user()


async def on_shutdown(dispatcher: Dispatcher):
    await Tortoise.close_connections()


if __name__ == '__main__':
    executor.start_polling(dp, on_startup=on_startup, on_shutdown=on_shutdown)
