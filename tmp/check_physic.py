import asyncio
from sqlalchemy import select
from university_bot.database import Group, Schedule, Subject, AsyncSessionLocal
from sqlalchemy.orm import joinedload

async def check_group_schedule():
    async with AsyncSessionLocal() as session:
        # Find group
        res = await session.execute(select(Group).where(Group.name.icontains("физик")))
        groups = res.scalars().all()
        print("Found Groups:")
        for g in groups:
            print(f"ID: {g.id}, Name: {g.name}")
        
        if not groups:
            print("No group found with 'физик'")
            return

        group_id = groups[0].id
        # Thursday is weekday 3
        stmt = select(Schedule).options(joinedload(Schedule.subject)).where(
            Schedule.group_id == group_id,
            Schedule.weekday == 3
        ).order_by(Schedule.start_time)
        
        res = await session.execute(stmt)
        schedules = res.unique().scalars().all()
        print(f"\nCurrent Schedule for {groups[0].name} on Thursday:")
        for s in schedules:
            print(f"{s.start_time}-{s.end_time} | {s.subject.name} | {s.room} | {s.subject.teacher_name}")

if __name__ == "__main__":
    asyncio.run(check_group_schedule())
