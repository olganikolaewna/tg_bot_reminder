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

                    # Проверка времени
                    user_time = user_now.time().replace(second=0, microsecond=0)
                    reminder_time = reminder.reminder_time.replace(second=0, microsecond=0)

                    is_time_match = user_time == reminder_time
 

                    if not is_time_match:
                        continue

                    # Проверка частоты
                    send = False

                    if reminder.frequency == 'once':
                        send = True
                        reminder.is_active = False
                    elif reminder.frequency == 'daily':
                        send = True
                    elif reminder.frequency == 'weekly':
                        today = user_now.strftime('%a').lower()
                        days = [d.strip().lower() for d in reminder.days_of_week.split(',')]
                        send = today in days

                    if send:
                        await bot.send_message(
                            reminder.user_id,
                            f"⏰ {reminder.title}\n\n{reminder.description}"
                        )

                except Exception as e:
                    print(f"[ERROR] Ошибка отправки напоминания: {e}")

            await session.commit()

        await asyncio.sleep(60)