from envparse import env
from os.path import isfile

if isfile('.env'):
    env.read_envfile('.env')

ADMIN_PHONES = env.list('ADMIN_PHONES', default=[])
ADMIN_CODE = env.str('ADMIN_CODE')

DB_DSN = env.str('DB_DSN', default='sqlite:///db/sqlite.db')

