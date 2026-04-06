from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes
from sqlalchemy import select, delete
from sqlalchemy.orm import joinedload
from database import Group, Subject, Schedule, Exam, AsyncSessionLocal
from keyboards import group_selection_keyboard, admin_menu_keyboard
from config import ADMIN_IDS

WEEKDAYS_KYR = ["Дүйшөмбү", "Шейшемби", "Шаршемби", "Бейшемби", "Жума", "Ишемби"]

async def edit_schedule_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    async with AsyncSessionLocal() as session:
        groups = await session.execute(select(Group))
        groups = groups.scalars().all()
        
        if not groups:
            await query.message.edit_text("Топтор табылган жок!", reply_markup=admin_menu_keyboard())
            return
            
        # Custom keyboard for editing (different prefix to avoid conflicts)
        keyboard = []
        for g in groups:
            keyboard.append([InlineKeyboardButton(g.name, callback_data=f"edit_sch_group_{g.id}")])
        keyboard.append([InlineKeyboardButton("⬅️ Артка", callback_data="admin_back")])
        
        await query.message.edit_text(
            "Оңдоо үчүн группаны тандаңыз:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

async def edit_schedule_group_selected(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    group_id = int(query.data.split("_")[-1])
    
    keyboard = []
    for i, day in enumerate(WEEKDAYS_KYR):
        keyboard.append([InlineKeyboardButton(day, callback_data=f"edit_sch_day_{group_id}_{i}")])
    keyboard.append([InlineKeyboardButton("⬅️ Группаларга кайтуу", callback_data="admin_edit_schedule")])
    
    await query.message.edit_text(
        "Күндү тандаңыз:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def edit_schedule_day_selected(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    parts = query.data.split("_")
    group_id = int(parts[3])
    day_idx = int(parts[4])
    
    async with AsyncSessionLocal() as session:
        stmt = select(Schedule).options(joinedload(Schedule.subject)).where(
            Schedule.group_id == group_id,
            Schedule.weekday == day_idx
        ).order_by(Schedule.start_time)
        
        results = await session.execute(stmt)
        schedules = results.unique().scalars().all()
        
        if not schedules:
            keyboard = [[InlineKeyboardButton("⬅️ Күндөргө кайтуу", callback_data=f"edit_sch_group_{group_id}")]]
            await query.message.edit_text(
                f"<b>{WEEKDAYS_KYR[day_idx]}</b> күнү үчүн сабактар жок.",
                parse_mode="HTML",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
            return

        msg = f"<b>{WEEKDAYS_KYR[day_idx]}</b> күндөгү сабактар:\n\n"
        keyboard = []
        for s in schedules:
            msg += f"🔸 {s.start_time}-{s.end_time} | {s.subject.name}\n"
            keyboard.append([InlineKeyboardButton(f"❌ Өчүрүү: {s.start_time}", callback_data=f"edit_sch_del_{s.id}_{group_id}_{day_idx}")])
        
        keyboard.append([InlineKeyboardButton("⬅️ Күндөргө кайтуу", callback_data=f"edit_sch_group_{group_id}")])
        
        await query.message.edit_text(
            msg,
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

async def edit_schedule_delete(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer("Сабак өчүрүлдү")
    
    parts = query.data.split("_")
    sch_id = int(parts[3])
    group_id = int(parts[4])
    day_idx = int(parts[5])
    
    async with AsyncSessionLocal() as session:
        await session.execute(delete(Schedule).where(Schedule.id == sch_id))
        await session.commit()
        
    # Refresh the view
    query.data = f"edit_sch_day_{group_id}_{day_idx}"
    await edit_schedule_day_selected(update, context)

async def admin_back(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.message.edit_text(
        "🛠 Администратор башкы менюсу:",
        reply_markup=admin_menu_keyboard()
    )

async def admin_delete_group_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    async with AsyncSessionLocal() as session:
        groups = await session.execute(select(Group))
        groups = groups.scalars().all()
        
        if not groups:
            await query.message.edit_text("Топтор табылган жок!", reply_markup=admin_menu_keyboard())
            return
            
        keyboard = []
        for g in groups:
            keyboard.append([InlineKeyboardButton(f"🗑 {g.name}", callback_data=f"del_group_conf_{g.id}")])
        keyboard.append([InlineKeyboardButton("⬅️ Артка", callback_data="admin_back")])
        
        await query.message.edit_text(
            "Өчүрүү үчүн топту тандаңыз (Эскертүү: Бул топтун бардык расписаниеси кошо өчөт!):",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

async def admin_delete_group_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    group_id = int(query.data.split("_")[-1])
    
    async with AsyncSessionLocal() as session:
        # Delete related schedules and exams first (manual cascade)
        await session.execute(delete(Schedule).where(Schedule.group_id == group_id))
        await session.execute(delete(Exam).where(Exam.group_id == group_id))
        
        # Reset group_id for users
        from sqlalchemy import update as sqlalchemy_update
        from database import User
        await session.execute(sqlalchemy_update(User).where(User.group_id == group_id).values(group_id=None))
        
        # Finally delete group
        await session.execute(delete(Group).where(Group.id == group_id))
        await session.commit()
        
        await query.answer("Топ жана анын маалыматтары өчүрүлдү")
        return await admin_delete_group_start(update, context)
