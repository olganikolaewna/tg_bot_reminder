from app.database.models import async_session
from app.database.models import User, Habit, HabitLog, Reminder
from sqlalchemy import select

from datetime import datetime, time

async def set_user(user_id, username=None, created_at=None, timezone=None):
    async with async_session() as session:
        user = await session.scalar(select(User).where(User.user_id == user_id))

        if user:
            if username:
                user.username = username
            if created_at:
                user.created_at = created_at
            if timezone:
                user.timezone = timezone
        else:
            user = User(
                user_id=user_id,
                username=username,
                created_at=created_at or datetime.now(),
                timezone=timezone
            )
            session.add(user)

        await session.commit()


async def user_exists(user_id):
    from .models import  User

    async with async_session() as session:
        user =  await session.get(User, user_id)
        return user is not None


async def save_reminder(user_id: int, title: str, reminder_time: time, 
                      description: str = '', frequency: str = 'daily', 
                      type: str = 'regular'):
    async with async_session() as session:
        reminder = Reminder(
            user_id=user_id,
            title=title,
            type=type,
            frequency=frequency,
            reminder_time=reminder_time,
            days_of_week = '',
            description=description,
            is_active=True
        )
        session.add(reminder)
        await session.commit()
        await session.refresh(reminder)
        return reminder

async def save_habit(reminder_id: int, target_days: int):
    async with async_session() as session:
        habit = Habit(
            reminder_id=reminder_id,
            target_days=target_days,
            streak=0  # Начинаем с 0 дней подряд
        )
        session.add(habit)
        await session.commit()

async def get_reminders(user_id: int):
    async with async_session() as session:
        result = await session.execute(
            select(Reminder)
            .where(Reminder.user_id == user_id, Reminder.is_active == True, Reminder.type == 'regular')
            .order_by(Reminder.reminder_time)
        )
        return result.scalars().all()
    
async def delete_reminder(reminder_id: int):
    async with async_session() as session:
        reminder = await session.get(Reminder, reminder_id)
        if reminder:
            await session.delete(reminder)
            await session.commit()


async def get_habits_with_titles(user_id: int):
    async with async_session() as session:
        result = await session.execute(
            select(Reminder, Habit)
            .join(Habit, Reminder.reminder_id == Habit.reminder_id)
            .where(
                Reminder.user_id == user_id,
                Reminder.is_active == True,
                Reminder.type == 'habit'
            )
            .order_by(Reminder.reminder_time)
        )
        return result.all()

