import asyncio
from datetime import datetime
from sqlalchemy import select
from aiogram import Bot
from app.database.models import Reminder, User, async_session
import pytz


async def reminder_worker(bot: Bot):
    while True:
        now_utc = datetime.utcnow()

        async with async_session() as session:
            result = await session.execute(
                select(Reminder, User)
                .join(User, Reminder.user_id == User.user_id)
                .where(Reminder.is_active == True)
            )
            reminders = result.all()

            for reminder, user in reminders:
                try:
                    # Проверяем часовой пояс
                    try:
                        user_tz = pytz.timezone(user.timezone)
                    except Exception as e:
                        print(f"[ERROR] Неверный часовой пояс: {user.timezone} — {e}")
                        continue

                    user_now = pytz.utc.localize(now_utc).astimezone(user_tz)
                    user_time = user_now.time().replace(second=0, microsecond=0)
                    reminder_time = reminder.reminder_time.replace(second=0, microsecond=0)

                    if user_time != reminder_time:
                        continue

                    # Раздельная обработка по типам
                    if reminder.type == 'habit':
                        # Отправка с клавиатурой для привычек
                        from app.keyboards import habit_confirmation_kb
                        await bot.send_message(
                            chat_id=reminder.user_id,
                            text=f"🔔 Привычка: {reminder.title}\n{reminder.description}",
                            reply_markup=habit_confirmation_kb(reminder.reminder_id)
                        )
                    else:
                        # Обычное напоминание
                        await bot.send_message(
                            chat_id=reminder.user_id,
                            text=f"⏰ Напоминание: {reminder.title}\n{reminder.description}"
                        )

                    # Обработка частоты (для одноразовых напоминаний)
                    if reminder.frequency == 'once':
                        reminder.is_active = False

                except Exception as e:
                    print(f"[ERROR] Ошибка отправки напоминания: {e}")

            await session.commit()
        await asyncio.sleep(60)