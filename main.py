from tortoise import Tortoise
from app.settings import DB_DSN


async def init_db():
    await Tortoise.init(db_url=DB_DSN, modules={'models': ['app.models']})
    await Tortoise.generate_schemas()


if __name__ == '__main__':
    pass
