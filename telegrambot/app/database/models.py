from sqlalchemy import BigInteger, String, Text, Date, DateTime, Time, Boolean, ForeignKey, Integer
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.ext.asyncio import AsyncAttrs, async_sessionmaker, create_async_engine

engine = create_async_engine(url='sqlite+aiosqlite:///database.sqlite3')

async_session = async_sessionmaker(engine)

class Base(AsyncAttrs, DeclarativeBase):
    pass

class User(Base):
    __tablename__ = 'users'

    user_id: Mapped[int] = mapped_column(primary_key = True)
    #tg_id = mapped_column(BigInteger)
    username: Mapped[str] = mapped_column(String)
    created_at: Mapped[DateTime] = mapped_column(DateTime)
    timezone: Mapped[Text] = mapped_column(Text)

class Habit(Base):
    __tablename__ = 'habits'

    habit_id: Mapped[int] = mapped_column(primary_key=True)
    reminder_id: Mapped[int] = mapped_column(ForeignKey('reminders.reminder_id')) #связанное напоминание;
    target_days: Mapped[int] = mapped_column(Integer)
    streak: Mapped[int] = mapped_column(Integer)


class HabitLog(Base):
    __tablename__ = 'habit_logs'  # Название таблицы в БД

    log_id: Mapped[int] = mapped_column(primary_key=True)  # ID записи
    reminder_id: Mapped[int] = mapped_column(ForeignKey('reminders.reminder_id'))
    completion_time: Mapped[DateTime] = mapped_column(DateTime)  # Дата выполнения
    status: Mapped[bool] = mapped_column(Boolean)  # Статус выполнения

class Reminder(Base):
    __tablename__ = 'reminders'  # Название таблицы в БД

    reminder_id: Mapped[int] = mapped_column(primary_key=True)  # ID напоминания
    user_id: Mapped[int] = mapped_column(ForeignKey('users.user_id'))  # ID пользователя
    title: Mapped[Text] = mapped_column(Text) #название/описание напоминания
    type: Mapped[Text] = mapped_column(Text) #тип: 'habit' (для привычек) или 'regular' (обычное);
    frequency: Mapped[Text] = mapped_column(Text) #периодичность ('once', 'daily', 'weekly', 'custom');
    reminder_time: Mapped[Time] = mapped_column(Time)  # Время срабатывания
    days_of_week: Mapped[Text] = mapped_column(Text) #дни недели (для weekly/custom, например "mon,wed,fri");
    description: Mapped[Text] = mapped_column(Text) #текст уведомления;
    is_active: Mapped[Boolean] = mapped_column(Boolean) #активно ли напоминание

async def async_main():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)