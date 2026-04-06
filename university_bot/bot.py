import logging
import asyncio
import os
import sys

# Ensure project root is in sys.path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.append(BASE_DIR)
from telegram.ext import (
    ApplicationBuilder, 
    CommandHandler, 
    MessageHandler, 
    CallbackQueryHandler, 
    ConversationHandler,
    filters     
)
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from pytz import timezone

from config import BOT_TOKEN, TIMEZONE
from database import init_db
from handlers import (
    start, select_group_callback, change_group,
    today_schedule, tomorrow_schedule, week_schedule, exams_list,
    toggle_notifications, send_reminders,
    admin_start, admin_callback_handler, process_broadcast, process_add_group, 
    cancel, ADD_GROUP, BROADCAST,
    edit_schedule_start, edit_schedule_group_selected, edit_schedule_day_selected, edit_schedule_delete,
    admin_delete_group_confirm,
    process_set_exam_group, process_add_exam,
    process_set_add_sched_group, process_set_add_sched_day, process_add_single_schedule,
    teacher_search_start, process_teacher_search, cancel_search
)
import handlers.admin as admin_h
import handlers.search as search_h

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

async def post_init(application):
    """Инициализация БД и планировщика после запуска бота"""
    await init_db()
    
    scheduler = AsyncIOScheduler(timezone=timezone(TIMEZONE))
    # Проверка напоминаний каждую минуту
    scheduler.add_job(send_reminders, 'cron', minute='*', args=[application.bot]) 
    scheduler.start()
    logging.info("База данных и планировщик запущены.")

def main():
    # Build Application with post_init hook
    app = ApplicationBuilder().token(BOT_TOKEN).post_init(post_init).build()

    # Teacher Search Conversation Handler
    search_conv = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex("^🔍 Мугалимди издөө$"), teacher_search_start)],
        states={
            search_h.SEARCH_TEACHER_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, process_teacher_search)],
        },
        fallbacks=[CommandHandler("cancel", cancel_search)],
    )

    # Admin Conversation Handler
    admin_conv = ConversationHandler(
        entry_points=[
            CommandHandler("admin", admin_start),
            CallbackQueryHandler(admin_callback_handler, pattern="^admin_")
        ],
        states={
            admin_h.ADD_GROUP: [MessageHandler(filters.TEXT & ~filters.COMMAND, process_add_group)],
            admin_h.ADD_SUBJECT: [MessageHandler(filters.TEXT & ~filters.COMMAND, admin_h.process_add_subject)],
            admin_h.ADD_SCHEDULE: [MessageHandler(filters.TEXT & ~filters.COMMAND, admin_h.process_add_schedule)],
            admin_h.BROADCAST: [MessageHandler(filters.TEXT & ~filters.COMMAND, process_broadcast)],
            admin_h.SET_SCHEDULE_GROUP: [CallbackQueryHandler(admin_h.process_set_schedule_group, pattern="^select_group_")],
            admin_h.SET_SCHEDULE_DAY: [MessageHandler(filters.TEXT & ~filters.COMMAND, admin_h.process_set_schedule_day), CommandHandler("skip", admin_h.process_set_schedule_day)],
            admin_h.SET_EXAM_GROUP: [CallbackQueryHandler(process_set_exam_group, pattern="^select_group_")],
            admin_h.ADD_EXAM_DATA: [MessageHandler(filters.TEXT & ~filters.COMMAND, process_add_exam)],
            admin_h.SET_ADD_SCHED_GROUP: [CallbackQueryHandler(process_set_add_sched_group, pattern="^select_group_")],
            admin_h.SET_ADD_SCHED_DAY: [CallbackQueryHandler(process_set_add_sched_day, pattern="^add_sch_day_")],
            admin_h.ADD_SINGLE_SCHED_DATA: [MessageHandler(filters.TEXT & ~filters.COMMAND, process_add_single_schedule)],
        },
        fallbacks=[
            CommandHandler("cancel", cancel),
            CallbackQueryHandler(admin_callback_handler, pattern="^admin_")
        ],
    )

    # Handlers registration
    app.add_handler(CommandHandler("start", start))
    app.add_handler(search_conv)
    app.add_handler(admin_conv)
    app.add_handler(CallbackQueryHandler(edit_schedule_group_selected, pattern="^edit_sch_group_"))
    app.add_handler(CallbackQueryHandler(edit_schedule_day_selected, pattern="^edit_sch_day_"))
    app.add_handler(CallbackQueryHandler(edit_schedule_delete, pattern="^edit_sch_del_"))
    app.add_handler(CallbackQueryHandler(admin_delete_group_confirm, pattern="^del_group_conf_"))
    app.add_handler(CallbackQueryHandler(select_group_callback, pattern="^select_group_"))
    
    app.add_handler(MessageHandler(filters.Regex("^📅 Бүгүн$") | filters.Command("today"), today_schedule))
    app.add_handler(MessageHandler(filters.Regex("^📆 Эртең$") | filters.Command("tomorrow"), tomorrow_schedule))
    app.add_handler(MessageHandler(filters.Regex("^🗓 Жумалык$") | filters.Command("week"), week_schedule))
    app.add_handler(MessageHandler(filters.Regex("^🎓 Экзамендер$") | filters.Command("exams"), exams_list))
    app.add_handler(MessageHandler(filters.Regex(r"^🔔 Билдирүү \(Күйгүзүү/Өчүрүү\)$") | filters.Command("notify"), toggle_notifications))
    app.add_handler(MessageHandler(filters.Regex("^👥 Топту өзгөртүү$") | filters.Command("group"), change_group))
    app.add_handler(MessageHandler(filters.Regex("^🛠 Админ Меню$"), admin_start))

    print("Бот иштеп жатат...")
    app.run_polling()

if __name__ == '__main__':
    main()
