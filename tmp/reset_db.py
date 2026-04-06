import asyncio
import os
import sys

# Добавляем путь к боту
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from sqlalchemy import delete
from university_bot.database import (
    AsyncSessionLocal, 
    Schedule, 
    Exam, 
    Subject, 
    Group, 
    User
)

async def reset_database():
    print("⚠️  Базаны толук тазалоо башталды...")
    async with AsyncSessionLocal() as session:
        try:
            # Өчүрүү кезеги (ForeignKey эске алуу менен)
            await session.execute(delete(Schedule))
            await session.execute(delete(Exam))
            await session.execute(delete(Subject))
            
            # Эгер топторду да өчүргүңүз келсе:
            await session.execute(delete(Group))
            
            # User'дорду өчүрбөй эле койгонуңуз жакшы, болбосо админдик укук кетип калат
            # Бирок алардын тандаган тобун нөлгө түшүрүүгө болот:
            # await session.execute(update(User).values(group_id=None))

            await session.commit()
            print("✅ База ийгиликтүү тазаланды! (Студенттер калды, бирок расписание жана топтор өчүрүлдү)")
        except Exception as e:
            await session.rollback()
            print(f"❌ Ката кетти: {e}")

if __name__ == "__main__":
    asyncio.run(reset_database())
