from aiogram.types import (ReplyKeyboardMarkup, KeyboardButton,
                           InlineKeyboardMarkup, InlineKeyboardButton)
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder


main = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text = 'Добавить напоминание', callback_data= 'add_reminder'), InlineKeyboardButton(text="Список задач", callback_data='reminder_list')],
    [InlineKeyboardButton(text = 'Добавить привычку', callback_data= 'add_habit'), InlineKeyboardButton(text="Список привычек", callback_data='habit_list') ],
     [InlineKeyboardButton(text = 'Посмотреть статитику', callback_data='stat')]
])


location = ReplyKeyboardMarkup(
    keyboard=[[KeyboardButton(text = "Отправить местоположение", request_location=True)]],
    resize_keyboard= True,
    one_time_keyboard=True
)

def freq_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text = 'Один раз', callback_data= "freq_once"), InlineKeyboardButton(text = 'Каждый день', callback_data='freq_daily')]
        #[InlineKeyboardButton(text='По дням недели', callback_data='freq_weekly')]
    ])


def reminders_list_kb(reminders):
    builder = InlineKeyboardBuilder()
    
    for reminder in reminders:
        builder.add(InlineKeyboardButton(
            text=f"❌Удалить: {reminder.title[:15]}",
            callback_data=f"delete_reminder_{reminder.reminder_id}"
        ))
    
    builder.adjust(2)  # 2 кнопки в ряд
    builder.row(InlineKeyboardButton(
        text="🔙 Назад",
        callback_data="back_to_main"
    ))
    
    return builder.as_markup()



def habit_confirmation_kb(reminder_id: int):
    builder = InlineKeyboardBuilder()
    builder.add(
        InlineKeyboardButton(text="✅ Выполнил", callback_data=f"habit_done_{reminder_id}"),
        InlineKeyboardButton(text="❌ Пропустил", callback_data=f"habit_skip_{reminder_id}")
    )
    return builder.as_markup()









































# reply_main = ReplyKeyboardMarkup(keyboard= [
#     [KeyboardButton(text = 'Добавить привычку'), KeyboardButton(text='Отметить как выполненное')],
#     [KeyboardButton(text = 'Посмотреть прогресс')],
#     [KeyboardButton(text='Узнать обо мне')]],
#     resize_keyboard=True,
#     input_field_placeholder='Выберите, что вы хотите сделать...')



# habits = ['Пить много воды', 'читать по 10 страниц в день', 'бегать']

# async def inline_habit():
#     keyboard = InlineKeyboardBuilder()
#     for habit in habits:
#         keyboard.add(InlineKeyboardButton(text = habit, callback_data=f'habit_{habit}'))
#     return keyboard.adjust(2).as_markup()

