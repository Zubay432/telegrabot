from telegram import Update
from telegram.ext import ContextTypes
from sqlalchemy import select
from sqlalchemy.orm import joinedload
from database import User, Schedule, AsyncSessionLocal
from datetime import datetime, timedelta
import pytz
from config import TIMEZONE

async def toggle_notifications(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    async with AsyncSessionLocal() as session:
        user = await session.execute(select(User).where(User.telegram_id == user_id))
        user = user.scalar_one_or_none()
        
        if user:
            user.notify_enabled = not user.notify_enabled
            await session.commit()
            status = "күйгүзүлдү" if user.notify_enabled else "өчүрүлдү"
            await update.message.reply_text(f"Эскермелер {status}!")

async def send_reminders(bot):
    # Check for lessons starting in 15 minutes
    now = datetime.now(pytz.timezone(TIMEZONE))
    target_time = (now + timedelta(minutes=15)).strftime("%H:%M")
    weekday = now.weekday()
    # Weak type needs to be determined here as well
    week_type = "odd" if now.isocalendar()[1] % 2 != 0 else "even"
    
    async with AsyncSessionLocal() as session:
        # Get schedules starting at target_time
        stmt = select(Schedule).options(joinedload(Schedule.subject)).where(
            Schedule.weekday == weekday,
            Schedule.start_time == target_time,
            Schedule.week_type.in_(['all', week_type])
        )
        results = await session.execute(stmt)
        schedules = results.unique().scalars().all()
        
        for s in schedules:
            # Find users in this group with notifications enabled
            user_stmt = select(User).where(
                User.group_id == s.group_id,
                User.notify_enabled == True
            )
            users = await session.execute(user_stmt)
            users = users.scalars().all()
            
            msg = f"🔔 <b>Эскертүү! Сабак 15 мүнөттөн кийин башталат!</b>\n\n"
            msg += f"📚 <b>{s.subject.name}</b>\n"
            msg += f"⏰ Убактысы: {s.start_time}\n"
            msg += f"📍 Кабинет: {s.room}\n"
            msg += f"👨‍🏫 Мугалим: {s.subject.teacher_name}"
            
            for u in users:
                try:
                    await bot.send_message(
                        chat_id=u.telegram_id,
                        text=msg,
                        parse_mode="HTML"
                    )
                except Exception as e:
                    print(f"Error sending reminder to {u.telegram_id}: {e}")
