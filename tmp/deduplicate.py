import asyncio
from sqlalchemy import select, delete
from university_bot.database import Schedule, AsyncSessionLocal

async def deduplicate():
    async with AsyncSessionLocal() as session:
        # Get all schedules
        res = await session.execute(select(Schedule))
        all_schedules = res.scalars().all()
        
        seen = set()
        to_delete = []
        
        for s in all_schedules:
            # Key: group_id, weekday, start_time
            key = (s.group_id, s.weekday, s.start_time)
            if key in seen:
                to_delete.append(s.id)
            else:
                seen.add(key)
        
        if to_delete:
            print(f"Found {len(to_delete)} duplicate schedules. Deleting...")
            stmt = delete(Schedule).where(Schedule.id.in_(to_delete))
            await session.execute(stmt)
            await session.commit()
            print("Successfully deduplicated!")
        else:
            print("No duplicates found.")

if __name__ == "__main__":
    asyncio.run(deduplicate())
