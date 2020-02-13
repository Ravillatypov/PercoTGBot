from aiogram.utils import executor
from tortoise import Tortoise

from app.settings import DB_DSN
from app.telegram import dp


async def on_startup(dispatcher):
    await Tortoise.init(db_url=DB_DSN, modules={'models': ['app.models']})
    await Tortoise.generate_schemas()


if __name__ == '__main__':
    executor.start_polling(dp, on_startup=on_startup)
