import asyncio
from sqlalchemy import select
from university_bot.database import User, AsyncSessionLocal
from university_bot.config import ADMIN_IDS

async def check():
    async with AsyncSessionLocal() as session:
        res = await session.execute(select(User))
        users = res.scalars().all()
        print("Database Users:")
        for u in users:
            print(f"ID: {u.telegram_id}, Name: {u.full_name}, Admin: {u.is_admin}")
        print(f"Config ADMIN_IDS: {ADMIN_IDS}")

if __name__ == "__main__":
    asyncio.run(check())
