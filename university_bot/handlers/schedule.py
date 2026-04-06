from telegram import Update
from telegram.ext import ContextTypes
from sqlalchemy import select
from datetime import datetime, timedelta
import pytz
from database import User, Schedule, Group, Exam, AsyncSessionLocal
from utils import format_schedule, format_exams, get_current_week_type
from config import TIMEZONE

from sqlalchemy.orm import joinedload

async def get_user_group(user_id):
    async with AsyncSessionLocal() as session:
        user = await session.execute(select(User).where(User.telegram_id == user_id))
        user = user.scalar_one_or_none()
        if user and user.group_id:
            return user.group_id
        return None

async def today_schedule(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    group_id = await get_user_group(user_id)
    if not group_id:
        await update.message.reply_text("Топ тандала элек! /start басыңыз.")
        return
    
    now = datetime.now(pytz.timezone(TIMEZONE))
    weekday = now.weekday()
    week_type = get_current_week_type()
    
    async with AsyncSessionLocal() as session:
        stmt = select(Schedule).options(joinedload(Schedule.subject)).where(
            Schedule.group_id == group_id,
            Schedule.weekday == weekday,
            Schedule.week_type.in_(['all', week_type])
        ).order_by(Schedule.start_time)
        
        results = await session.execute(stmt)
        schedules = results.unique().scalars().all()
        
        # Sort in Python to handle any unnormalized DB entries
        sorted_schedules = sorted(schedules, key=lambda x: x.start_time if x.start_time and len(x.start_time)==5 else ("0"+x.start_time if x.start_time else "00:00"))
        
        text = format_schedule(sorted_schedules, "📅 Бүгүнкү расписание")
        await update.message.reply_text(text, parse_mode="HTML")

async def tomorrow_schedule(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    group_id = await get_user_group(user_id)
    if not group_id:
        await update.message.reply_text("Топ тандала элек! /start басыңыз.")
        return
    
    now = datetime.now(pytz.timezone(TIMEZONE)) + timedelta(days=1)
    weekday = now.weekday()
    week_type = "odd" if now.isocalendar()[1] % 2 != 0 else "even"
    
    async with AsyncSessionLocal() as session:
        stmt = select(Schedule).options(joinedload(Schedule.subject)).where(
            Schedule.group_id == group_id,
            Schedule.weekday == weekday,
            Schedule.week_type.in_(['all', week_type])
        ).order_by(Schedule.start_time)
        
        results = await session.execute(stmt)
        schedules = results.unique().scalars().all()
        
        # Sort in Python to handle any unnormalized DB entries
        sorted_schedules = sorted(schedules, key=lambda x: x.start_time if x.start_time and len(x.start_time)==5 else ("0"+x.start_time if x.start_time else "00:00"))
        
        text = format_schedule(sorted_schedules, "📆 Эртеңки расписание")
        await update.message.reply_text(text, parse_mode="HTML")

async def week_schedule(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    group_id = await get_user_group(user_id)
    if not group_id:
        await update.message.reply_text("Топ тандала элек! /start басыңыз.")
        return
    
    week_type = get_current_week_type()
    weekdays_kyr = ["Дүйшөмбү", "Шейшемби", "Шаршемби", "Бейшемби", "Жума", "Ишемби"]
    full_msg = f"<b>🗓 Жумалык расписание ({'Так' if week_type=='odd' else 'Жуп'} жума)</b>\n\n"
    
    async with AsyncSessionLocal() as session:
        for i in range(6):
            stmt = select(Schedule).options(joinedload(Schedule.subject)).where(
                Schedule.group_id == group_id,
                Schedule.weekday == i,
                Schedule.week_type.in_(['all', week_type])
            ).order_by(Schedule.start_time)
            
            results = await session.execute(stmt)
            schedules = results.unique().scalars().all()
            
            if schedules:
                # Sort in Python to handle any unnormalized DB entries
                sorted_schedules = sorted(schedules, key=lambda x: x.start_time if x.start_time and len(x.start_time)==5 else ("0"+x.start_time if x.start_time else "00:00"))
                
                full_msg += f"<b>{weekdays_kyr[i]}</b>\n"
                for s in sorted_schedules:
                    # Strict formatting: TIME | SUBJECT
                    full_msg += f"▫️ {s.start_time}-{s.end_time} | {s.subject.name}\n"
                full_msg += "\n\n"
        
        await update.message.reply_text(full_msg, parse_mode="HTML")

async def exams_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    group_id = await get_user_group(user_id)
    if not group_id:
        await update.message.reply_text("Топ тандала элек! /start басыңыз.")
        return
    
    async with AsyncSessionLocal() as session:
        stmt = select(Exam).options(joinedload(Exam.subject)).where(
            Exam.group_id == group_id,
            Exam.exam_date >= datetime.now().date()
        ).order_by(Exam.exam_date)
        
        results = await session.execute(stmt)
        exams = results.unique().scalars().all()
        
        text = format_exams(exams)
        await update.message.reply_text(text, parse_mode="HTML")
