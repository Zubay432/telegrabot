from telegram import Update, ReplyKeyboardRemove
from telegram.ext import ContextTypes, ConversationHandler
from sqlalchemy import select
from sqlalchemy.orm import joinedload
from database import Schedule, Subject, AsyncSessionLocal
from keyboards import main_menu_keyboard
from datetime import datetime
import pytz
from config import TIMEZONE

SEARCH_TEACHER_NAME = 0

async def teacher_search_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🔍 Мугалимдин атын же фамилиясын жазыңыз (Мисалы: <code>Иванов</code>):",
        parse_mode="HTML",
        reply_markup=ReplyKeyboardRemove()
    )
    return SEARCH_TEACHER_NAME

async def process_teacher_search(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.message.text.strip()
    if len(query) < 3:
        await update.message.reply_text("Сураныч, изилдөө үчүн кеминде 3 тамга жазыңыз.")
        return SEARCH_TEACHER_NAME

    async with AsyncSessionLocal() as session:
        # Search for subjects by teacher name
        stmt = select(Schedule).join(Subject).options(joinedload(Schedule.subject), joinedload(Schedule.group)).where(
            Subject.teacher_name.icontains(query)
        ).order_by(Schedule.weekday, Schedule.start_time)
        
        results = await session.execute(stmt)
        schedules = results.unique().scalars().all()
        
        if not schedules:
            await update.message.reply_text(
                f"❌ '{query}' боюнча мугалим табылган жок.",
                reply_markup=main_menu_keyboard(user_id=update.effective_user.id)
            )
            return ConversationHandler.END

        msg = f"🔍 <b>'{query}' боюнча табылган сабактар:</b>\n\n"
        weekdays = ["Дүйшөмбү", "Шейшемби", "Шаршемби", "Бейшемби", "Жума", "Ишемби"]
        
        current_day = -1
        for s in schedules:
            if s.weekday != current_day:
                current_day = s.weekday
                msg += f"\n<b>🗓 {weekdays[current_day]}</b>\n"
            
            msg += f"▫️ {s.start_time}-{s.end_time} | {s.subject.name}\n"
            msg += f"   👥 Топ: {s.group.name} | 📍 Каб: {s.room}\n"
            msg += f"   👨‍🏫 Мугалим: {s.subject.teacher_name}\n"

        await update.message.reply_text(msg, parse_mode="HTML", reply_markup=main_menu_keyboard(user_id=update.effective_user.id))
        return ConversationHandler.END

async def cancel_search(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Издөө токтотулду.", reply_markup=main_menu_keyboard(user_id=update.effective_user.id))
    return ConversationHandler.END
