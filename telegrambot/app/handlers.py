from aiogram import F, Router
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
import pytz
from timezonefinder import TimezoneFinder
from datetime import datetime

import app.keyboards as kb
from aiogram.types import ReplyKeyboardRemove

import app.database.requests as rq
router = Router()

class Registration(StatesGroup):
    waiting_for_location = State()
    waiting_for_timezone = State()

#команда /start
@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    username = message.from_user.username or message.from_user.full_name
    await state.update_data(
        user_id=message.from_user.id,
        username = username,
        created_at = datetime.now()
    )

    await message.answer(
        "Привет! Для определения твоего часового пояса отправь мне своё местоположение:",
        reply_markup=kb.location  # Используем новую клавиатуру
    )
    await state.set_state(Registration.waiting_for_location)



@router.message(Registration.waiting_for_location, F.location)
async def handle_location(message: Message, state: FSMContext):
    try:
        loc = message.location
        tf = TimezoneFinder()
        timezone_str = tf.timezone_at(lat=loc.latitude, lng=loc.longitude)
        if not timezone_str:
            raise ValueError("Не удалось определить часовой пояс")

        timezone = timezone_str

        # Получаем пользователя напрямую
        user_id = message.from_user.id
        username = message.from_user.username or message.from_user.full_name
        created_at = datetime.now()

        is_update = await rq.user_exists(user_id=user_id)
        await rq.set_user(
            user_id=user_id,
            username=username,
            created_at=created_at,
            timezone=timezone
        )

        if is_update:
            text = f"✅ Местоположение обновлено.\nТвой часовой пояс: {timezone}"
        else:
            text = f"✅ Отлично! Твой часовой пояс: {timezone}\nТеперь можешь начать работу с ботом!"

        await message.answer(text, reply_markup=ReplyKeyboardRemove())
        await state.clear()

        await message.answer("Я бот трекер привычек. Давай начнём!", reply_markup=kb.main)

    except Exception as e:
        print(f"Ошибка: {e}")
        await message.answer(
            "⚠️ Не удалось определить часовой пояс. Введи его вручную (например: GMT+3):",
            reply_markup=ReplyKeyboardRemove()
        )
        await state.set_state(Registration.waiting_for_timezone)


#Команда /help
@router.message(Command("help"))
async def help(message: Message):
    await message.answer("Чем я могу помочь?")


#Команда /edit_location
@router.message(Command("edit_location"))
async def edit_location(message: Message, state: FSMContext):
    await message.answer(
        "Хорошо! Отправь свое новое местоположение",
        reply_markup=kb.location
    )
    await state.set_state(Registration.waiting_for_location)


#Команда /about_me
@router.message(Command("about_me"))
async def about_me(message: Message):
    text = ("✨ <b>Что я умею:</b>\n"
        "• Напоминать о важных делах (оплата счетов, прием лекарств, звонок маме)\n"
        "• Помогать вырабатывать полезные привычки (спорт, чтение, вода)\n"
        "• Отслеживать твой прогресс и радоваться успехам вместе с тобой 🎉\n\n"
        "📌 <b>Как это работает:</b>\n"
        "1. Создаешь привычку или напоминание\n"
        "2. Получаешь уведомления в нужное время\n"
        "3. Отмечаешь выполнение - я запоминаю\n"
        "4. Смотришь статистику и улучшаешь результат!\n\n")
    await message.answer(text, reply_markup= kb.main)


#Команда /add_remind

class AddReminder(StatesGroup):
    waiting_for_title = State()
    waiting_for_time = State()
    waiting_for_description = State()
    waiting_for_frequency = State()
    #waiting_for_weekdays = State()


@router.callback_query(F.data == "add_reminder")
async def add_reminder(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer("Введите задачу")
    await state.set_state(AddReminder.waiting_for_title)
    await callback.answer()

@router.message(AddReminder.waiting_for_title)
async def get_title(message: Message, state: FSMContext):
    await state.update_data(title = message.text)
    await message.answer("Введите время напоминания в формате НН:ММ (например: 08:00):")
    await state.set_state(AddReminder.waiting_for_time)

@router.message(AddReminder.waiting_for_time)
async def get_time(message: Message, state: FSMContext):
    try:
        hour, minute = map(int, message.text.split(":"))
        time_obj = datetime.now().replace(hour = hour, minute = minute, second = 0, microsecond=0).time()
        await state.update_data(reminder_time = time_obj)
        await message.answer("Введите описание напоминания:")
        await state.set_state(AddReminder.waiting_for_description)
    except Exception:
        await message.answer("Неверный формат. Введите в формате НН:ММ")

@router.message(AddReminder.waiting_for_description)
async def get_desc(message: Message, state: FSMContext):
    await state.update_data(description = message.text)
    await message.answer("Один раз или каждый день?", reply_markup=kb.freq_kb())
    await state.set_state(AddReminder.waiting_for_frequency)


@router.callback_query(AddReminder.waiting_for_frequency)
async def get_freq(callback: CallbackQuery, state: FSMContext):
    mapping = {
        "freq_once": "once",
        "freq_daily": "daily",
        "freq_weekly": "weekly"
    }
    freq_key = callback.data
    frequency = mapping.get(freq_key)

    if not frequency:
        await callback.answer("Неверный выбор")
        return
    data = await state.get_data()
    await rq.save_reminder(
        user_id = callback.from_user.id,
        title = data["title"],
        reminder_time = data["reminder_time"],
        description = data["description"],
        frequency = frequency
    )
    await callback.message.answer("Напоминание добавлено!", reply_markup=kb.main)
    await state.clear()
    await callback.answer()

















































# @router.message(Command('help'))
# async def get_help(message: Message):
#     await message.answer('Чем могу вам помочь?')

# @router.message(F.text == 'Как дела?')
# async def how_are_you(message: Message):
#     await message.answer('Отлично!!')

# @router.callback_query(F.data == 'add_habit')
# async def add(callback: CallbackQuery):
#     await callback.answer('')
#     await callback.message.edit_text('Введите свою привычку или выберите из предложенных', reply_markup= await kb.inline_habit())

# @router.message(F.text == 'Добавить привычку')
# async def add_h(message: Message):
#     await message.answer('Введите свою привычку или выберите из предложенных', reply_markup= await kb.inline_habit())

# @router.message(Command('reg'))
# async def reg_one(message: Message, state: FSMContext):
#     await state.set_state(Reg.name)
#     await message.answer('Введите свое имя')

# @router.message(Reg.name)
# async def reg_two(message: Message, state: FSMContext):
#     await state.update_data(name = message.text)
#     await state.set_state(Reg.number)
#     await message.answer('Введите свой номер')

# @router.message(Reg.number)
# async def reg_three(message: Message, state: FSMContext):
#     await state.update_data(number = message.text)
#     data = await state.get_data()
#     await message.answer(f'Спасибо за регистрацию. \nИмя: {data["name"]}\nНомер: {data["number"]}')
#     await state.clear()