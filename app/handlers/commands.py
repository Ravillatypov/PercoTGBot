from aiogram.types import Message
from aiogram.utils import exceptions
from app import settings
from app.decorators import admin
from app.helpers import check_admin_user, send_user_edit_message, send_available_doors, get_users_markup
from app.models import User, Door
from app.settings import dp, ADMIN_USERNAME, logger
from app.perco import PercoClient


@dp.message_handler(commands=['start'])
async def start(message: Message):
    await check_admin_user()
    user, created = await User.get_or_create(
        chat_id=message.chat.id,
        defaults={
            'username': message.chat.username or '',
            'first_name': message.chat.first_name or '',
            'last_name': message.chat.last_name or '',
            'is_active': message.chat.username == ADMIN_USERNAME or None
        }
    )
    if user.is_active:
        return await message.reply(f'С возвращением {user.full_name}!')
    msg = 'Я Perco-бот! Могу для вас открыть или закрыть дверь.\n'
    if message.chat.username == ADMIN_USERNAME:
        msg += 'Вы администратор, поздавляю!'
    else:
        msg += 'Ваш запрос ожидает подтверждения администратором.'
        if settings.ADMIN_CHAT_ID:
            await send_user_edit_message(user, settings.ADMIN_CHAT_ID, is_new=True)
    await message.reply(msg)


@dp.message_handler(commands=['updateDoors', 'sync_doors'])
@admin
async def update_doors(message: Message, **kwargs):
    perco: PercoClient = dp['perco']

    for data in await perco.get_doors():
        door, _ = await Door.get_or_create(id=data.get('id', 0), defaults={'name': data.get('name', '-')})
        if door.name != data.get('name', '-'):
            door.name = data.get('name', '-')
            await door.save(update_fields=['name'])

    await message.reply('Обновил')


@dp.message_handler(commands=['doors'])
async def get_doors(message: Message):
    await send_available_doors(message.chat.id, dp['perco'])


@dp.message_handler(commands=['users'])
@admin
async def get_users(message: Message, **kwargs):
    markup = await get_users_markup()
    if markup:
        await message.reply('Список пользователей:', reply_markup=markup)
    else:
        await message.reply('На данный момент вы единственный пользователь')


@dp.message_handler(commands=['force_update_doors'])
@admin
async def force_update_doors(message: Message, **kwargs):
    chats = await User.all().values_list('chat_id', flat=True)

    errors = []
    success = 0

    for chat_id in chats:
        try:
            await send_available_doors(chat_id, dp['perco'])
        except Exception as e:
            logger.warning(f'cant update doors for chat_id={chat_id}, error="{e}"')
            errors.append(f'"{e}"')

    fail = len(errors)
    errors = ', '.join(set(errors))
    text = 'Список дверей не отправлено'

    if success:
        text = f'Успешно отправлено {success} пользователям.'

    if fail:
        text = f'{text}\nВозникли ошибки при отправке {fail} пользователям.\nОшибки: {errors}'

    await message.reply(text)
