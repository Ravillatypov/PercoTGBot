import logging
from os.path import isfile

from aiogram import Bot, Dispatcher
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from envparse import env

if isfile('.env'):
    env.read_envfile('.env')

ADMIN_PHONES = env.list('ADMIN_PHONES', default=[])
ADMIN_CODE = env.str('ADMIN_CODE')
ADMIN_USERNAME = env.str('ADMIN_USERNAME')

DB_DSN = env.str('DB_DSN', default='sqlite:///db/sqlite.db')

API_TOKEN = env.str('API_TOKEN')
PROXY_URL = env.str('PROXY_URL', default='')

# logging settings
LOG_LEVEL = env.str('LOG_LEVEL', default='WARNING')

formatter = logging.Formatter('{"time": "%(asctime)s", "level": "%(levelname)s", "file": "%(filename)s", '
                              '"function": "%(funcName)s", "message": "%(message)s"}')
stream = logging.StreamHandler()
stream.setFormatter(formatter)

logger = logging.getLogger()
logger.setLevel(LOG_LEVEL)
# ----------------

# Initialize bot and dispatcher
if PROXY_URL:
    bot = Bot(token=API_TOKEN, proxy=PROXY_URL)
else:
    bot = Bot(token=API_TOKEN)

dp = Dispatcher(bot, storage=MemoryStorage())

