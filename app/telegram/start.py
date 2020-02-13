from app.settings import dp, ADMIN_USERNAME
from aiogram.types import Message
from aiogram.types.reply_keyboard import ReplyKeyboardMarkup, KeyboardButton
from aiogram.types.inline_keyboard import InlineKeyboardMarkup, InlineKeyboardButton
from app.models import User
from app.telegram.states import AuthenticateForm
from app.helpers import get_phone
from aiogram.dispatcher import FSMContext


@dp.message_handler(commands=['start', 'login'])
async def start(message: Message):
    user = await User.filter(chat_id=message.chat.id).first()
    if user:
        return await message.reply(f'С возвращением {user.name}!')
    await message.reply('Я Perco-бот! Могу для вас открыть или закрыть дверь.\n'
                        'Чтобы пользоваться моими услугами, пожалуйста авторизуйтесь.\n'
                        f'Если вас еще не внесли в систему, пожалуйста обратитесь админу: @{ADMIN_USERNAME}')
    await AuthenticateForm.phone.set()
    await message.reply(
        'Для авторизации отправьте пожалуйста номер телефона',
        reply_markup=ReplyKeyboardMarkup(
            [[KeyboardButton('Отправить номер', request_contact=True)]],
            one_time_keyboard=True
        )
    )


@dp.message_handler(commands=['/group'])
async def groups(message: Message):
    user = await User.filter(chat_id=message.chat.id).first()
    if message.chat.username != ADMIN_USERNAME or not user or not user.is_admin:
        return await message.reply('Только админ может управлять группой')
    await message.reply(
        'Что будем делать?',
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton('Добавить', callback_data='group_add'),
                 InlineKeyboardButton('Удалить', callback_data='group_delete')],
                [InlineKeyboardButton('Изменить', callback_data='group_edit'),
                 InlineKeyboardButton('Отмена', callback_data='cancel')]
            ],
        )
    )


@dp.message_handler(state=AuthenticateForm.phone)
async def login(message: Message, state: FSMContext):
    if message.contact:
        phone = get_phone(message.contact.phone_number)
    else:
        phone = get_phone(message.text)
    if not phone:
        return await message.reply('Не корректный номер!')
    user = await User.filter(phone=phone).first()
    if not user:
        await state.finish()
        return await message.reply('Извините, нет вашего номера в базе. Обратитесь администратору.')
    await AuthenticateForm.next()
    async with state.proxy() as data:
        data['phone'] = phone
    await message.reply('Жду проверочный код')


@dp.message_handler(state=AuthenticateForm.code)
async def authorize(message: Message, state: FSMContext):
    phone = ''
    async with state.proxy() as data:
        phone = data['phone']
        if data.get('ban'):
            return await message.reply('Вы исчерпали все попытки авторизации')
    user = await User.filter(phone=phone).first()
    if not user:
        return await message.reply('Извините, нет вашего номера в базе. Обратитесь администратору.')
    if message.text.strip() != user.code:
        async with state.proxy() as data:
            data['fail_count'] = data.get('fail_count', 0) + 1
            if data['fail_count'] > 3:
                data['ban'] = True
        return await message.reply('Не правильный код. Повторите попытку.')
    await state.finish()
    await AuthenticateForm.next()
    await state.update_data(phone=phone)
    await message.reply('Жду проверочный код')

