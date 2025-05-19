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



#команда /start
class Registration(StatesGroup):
    waiting_for_location = State()
    waiting_for_timezone = State()


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    username = message.from_user.username or message.from_user.full_name
    await state.update_data(
        user_id=message.from_user.id,
        username = username,
        created_at = datetime.now()
    )

    await message.answer(
        "Я рад, что ты решил стать более организованным!😉\nДавай сначала определим твой часовой пояс, чтобы напоминания приходили вовремя:",
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
            text = f"✅ Отлично! Твой часовой пояс: {timezone}"

        await message.answer(text, reply_markup=ReplyKeyboardRemove())
        await state.clear()

        start_text = ("🎉 Отлично, настройка завершена!\n\n"
                    "Теперь я могу:\n"
                    "   • Напоминать о важных делах (оплата счетов, прием лекарств, звонок маме)\n"
                    "   • Помогать вырабатывать полезные привычки (спорт, чтение, вода)\n"
                    "   • Отслеживать твой прогресс и радоваться успехам вместе с тобой 🎉\n\n"
                    "Выбирай, с чего начнем:"
                      )


        await message.answer(start_text, 
                             reply_markup=kb.main)

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
        "Хорошо! Отправь свое новое местоположение:",
        reply_markup=kb.location
    )
    await state.set_state(Registration.waiting_for_location)




#Команда /about_me
@router.message(Command("about_me"))
async def about_me(message: Message):
    text = ("✨ Я умею:\n"
        "   • Напоминать о важных делах (оплата счетов, прием лекарств, звонок маме)\n"
        "   • Помогать вырабатывать полезные привычки (спорт, чтение, вода)\n"
        "   • Отслеживать твой прогресс и радоваться успехам вместе с тобой 🎉\n\n"
        "📌 Как это работает:\n"
        "   1. Создаешь привычку или напоминание\n"
        "   2. Получаешь уведомления в нужное время\n"
        "   3. Отмечаешь выполнение - я запоминаю\n"
        "   4. Смотришь статистику и улучшаешь результат!\n\n")
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
    await callback.message.answer("📝 Введи название задачи или события, о котором нужно напомнить")
    await state.set_state(AddReminder.waiting_for_title)
    await callback.answer()

@router.message(AddReminder.waiting_for_title)
async def get_title(message: Message, state: FSMContext):
    await state.update_data(title = message.text)
    await message.answer("Введи время напоминания в формате НН:ММ (например: 08:00)")
    await state.set_state(AddReminder.waiting_for_time)

@router.message(AddReminder.waiting_for_time)
async def get_time(message: Message, state: FSMContext):
    try:
        hour, minute = map(int, message.text.split(":"))
        time_obj = datetime.now().replace(hour = hour, minute = minute, second = 0, microsecond=0).time()
        await state.update_data(reminder_time = time_obj)
        await message.answer("✏️ Добавь описание (можно кратко)")
        await state.set_state(AddReminder.waiting_for_description)
    except Exception:
        await message.answer("Неверный формат. Пожалуйста, введи в формате НН:ММ")

@router.message(AddReminder.waiting_for_description)
async def get_desc(message: Message, state: FSMContext):
    await state.update_data(description = message.text)
    await message.answer("🔄 Как часто нужно напоминать?", reply_markup=kb.freq_kb())
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
    time_str = data["reminder_time"].strftime("%H:%M")
    freq_str = {
        "once": "один раз",
        "daily": "каждый день",
        #"weekly": "каждую неделю"
    }.get(frequency, frequency)
    
    await callback.message.answer(
        f"✅ Напоминание успешно добавлено!\n\n"
        f"▪️ Задача: {data['title']}\n"
        f"▪️ Время: {time_str}\n"
        f"▪️ Повтор: {freq_str}\n\n"
        f"Теперь ты не пропустишь важное!",
        reply_markup=kb.main
    )
    await state.clear()
    await callback.answer()



#Команда /add_habit
class AddHabit(StatesGroup):
    waiting_for_title = State()
    waiting_for_time = State()
    waiting_for_desc = State()
    waiting_for_tdays = State()

@router.callback_query(F.data == "add_habit")
async def add_habit(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer("Введи название привычки, которую хочешь освоить")
    await state.set_state(AddHabit.waiting_for_title)
    await callback.answer()

@router.message(AddHabit.waiting_for_title)
async def get_habit_title(message: Message, state: FSMContext):
    await state.update_data(title = message.text)
    await message.answer("Введи время напоминания в формате НН:ММ (например: 08:00)")
    await state.set_state(AddHabit.waiting_for_time)

@router.message(AddHabit.waiting_for_time)
async def get_habit_time(message: Message, state: FSMContext):
    try:
        hour, minute = map(int, message.text.split(":"))
        time_habit = datetime.now().replace(hour = hour, minute = minute, second = 0, microsecond = 0).time()
        await state.update_data(reminder_time = time_habit)
        await message.answer("Введи описание своей привычки")
        await state.set_state(AddHabit.waiting_for_desc)
    except Exception:
        await message.answer("Неверный формат. Пожалуйста, введи в формате НН:ММ")

@router.message(AddHabit.waiting_for_desc)
async def get_habit_desc(message: Message, state: FSMContext):
    await state.update_data(description = message.text)
    await message.answer("На сколько дней ставим цель? Говорят, чтобы оствоить привычку нужно 21 дней, но ты можешь выбрать любое количество дней!")
    await state.set_state(AddHabit.waiting_for_tdays)

@router.message(AddHabit.waiting_for_tdays)
async def get_habit_tdays(message: Message, state: FSMContext):
    try:
        target_days = int(message.text)
        if target_days <= 0:
            raise ValueError
        
        data = await state.get_data()

        reminder = await rq.save_reminder(
            user_id = message.from_user.id,
            title = data['title'],
            reminder_time = data['reminder_time'],
            description= data['description'],
            frequency='daily',
            type='habit'
        )
        await rq.save_habit(
            reminder_id= reminder.reminder_id,
            target_days= target_days
        )
        await message.answer(
            f"✅ Привычка '{data['title']}' успешно создана!\n"
            f"⏰ Время: {data['reminder_time'].strftime('%H:%M')}\n"
            f"🎯 Цель: {target_days} дней",
            reply_markup=kb.main
        )
        await state.clear()
    except ValueError:
        await message.answer("Пожалуйста, введи корректное число дней (больше 0)")





#Команда /reminder_list
@router.callback_query(F.data == "reminder_list")
async def rem_list(callback: CallbackQuery):
    reminders = await rq.get_reminders(callback.from_user.id)
    
    if not reminders:
        await callback.message.answer("📭 У тебя пока нет активных напоминаний", reply_markup=kb.main)
        await callback.answer()
        return
    
    reminders_text = ["📋 Список твоих дел:\n"]
    
    for reminder in reminders:
        time_str = reminder.reminder_time.strftime("%H:%M")
        freq_str = {
            "once": "один раз",
            "daily": "ежедневно",
            "weekly": "еженедельно"
        }.get(reminder.frequency, reminder.frequency)
        
        reminders_text.append(
            f"▪️ {reminder.title} - {time_str} ({freq_str})\n"
            f"   Описание: {reminder.description or 'нет'}\n"
        )
        
    await callback.message.answer(
        "\n".join(reminders_text),
        reply_markup=kb.reminders_list_kb(reminders)
    )
    await callback.answer("Эта функция находится в стадии доработки.")





#Команда /habit_list
@router.callback_query(F.data == "habit_list")
async def habit_list(callback: CallbackQuery):
    habits_data = await rq.get_habits_with_titles(callback.from_user.id)
    
    
    if not habits_data:
        await callback.message.answer("📭 У тебя пока нет активных привычек", reply_markup=kb.main)
        await callback.answer()
        return
    
    habits_text = ["📋 Список твоих привычек:\n"]
    
    for reminder, habit in habits_data:
        time_str = reminder.reminder_time.strftime("%H:%M")
        
        
        habits_text.append(
            f"▪️ Название: {reminder.title}\n"
            f"   Время: {time_str} \n"
            f"   Описание: {reminder.description or 'нет'}\n"
            f"   Цель: {habit.target_days}\n"
        )
        
    await callback.message.answer(
        "\n".join(habits_text),
        reply_markup=kb.main
    )
    await callback.answer("Эта функция находится в стадии доработки")


#Удаление напоминания
@router.callback_query(F.data.startswith("delete_reminder_"))
async def delete_reminder(callback: CallbackQuery):
    reminder_id = int(callback.data.split("_")[-1])
    await rq.delete_reminder(reminder_id)
    await callback.message.answer("✅ Напоминание удалено", reply_markup=kb.main)
    await callback.answer()




#Кнопка Назад в Главное меню
@router.callback_query(F.data == "back_to_main")
async def back_to_main(callback: CallbackQuery):
    await callback.message.answer("Что будем делать?", reply_markup=kb.main)
    await callback.answer()




#Команда /stat. Пока не реализованa
@router.callback_query(F.data == "stat")
async def back_to_main(callback: CallbackQuery):
    await callback.message.answer("Эта функция пока недоступна. Выбери что-то другое😊", reply_markup=kb.main)
    await callback.answer()

    




#Команды для отметки привычек. Пока не реализованы

@router.callback_query(F.data.startswith("habit_done_"))
async def habit_done(callback: CallbackQuery):
    reminder_id = int(callback.data.split("_")[-1])
    # Логика обработки выполнения привычки
    await callback.message.edit_reply_markup(reply_markup=None)
    await callback.message.answer("Молодец! Привычка засчитана! 👍", reply_markup=kb.main)
    await callback.answer()

@router.callback_query(F.data.startswith("habit_skip_"))
async def habit_skip(callback: CallbackQuery):
    reminder_id = int(callback.data.split("_")[-1])
    # Логика обработки пропуска привычки
    await callback.message.edit_reply_markup(reply_markup=None)
    await callback.message.answer("Пропущено 😕 Но ничего страшного, главное не забывай о своей привычке на совсем!", reply_markup=kb.main)
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