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


async def save_reminder(user_id: int, title: str, reminder_time: time, description: str, frequency:str):
    async with async_session() as session:
        reminder = Reminder(
            user_id=user_id,
            title=title,
            type='regular',
            frequency=frequency,
            reminder_time=reminder_time,
            days_of_week='',
            description=description,
            is_active=True
        )
        session.add(reminder)
        await session.commit()