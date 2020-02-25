import logging
from os.path import isfile

import sentry_sdk
from aiogram import Bot, Dispatcher
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from envparse import env
from sentry_sdk.integrations.aiohttp import AioHttpIntegration
from sentry_sdk.integrations.logging import LoggingIntegration

from app.perco import PercoClient

if isfile('.env'):
    env.read_envfile('.env')

ADMIN_USERNAME = env.str('ADMIN_USERNAME')
ADMIN_CHAT_ID = env.int('ADMIN_CHAT_ID', default=0)

DB_DSN = env.str('DB_DSN', default='sqlite:///db/sqlite.db')

API_TOKEN = env.str('API_TOKEN')
PROXY_URL = env.str('PROXY_URL', default='')

PERCO_URL = env.str('PERCO_URL', default='')
PERCO_LOGIN = env.str('PERCO_LOGIN', default='')
PERCO_PASS = env.str('PERCO_PASS', default='')

SENTRY_DSN = env.str('SENTRY_SDN', default='')
if SENTRY_DSN:
    sentry_sdk.init(
        dsn=SENTRY_DSN,
        integrations=[AioHttpIntegration(), LoggingIntegration()]
    )

# logging settings
LOG_LEVEL = env.str('LOG_LEVEL', default='WARNING')
logging.basicConfig(level=getattr(logging, LOG_LEVEL, logging.WARNING))

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

perco = PercoClient(PERCO_URL, PERCO_LOGIN, PERCO_PASS)
