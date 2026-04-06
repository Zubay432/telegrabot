from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import (
    ContextTypes, 
    ConversationHandler, 
    CommandHandler, 
    MessageHandler, 
    CallbackQueryHandler, 
    filters
)
from sqlalchemy import select, func, delete
from database import Group, Subject, Schedule, Exam, User, AsyncSessionLocal
from keyboards import admin_menu_keyboard, main_menu_keyboard
from config import ADMIN_IDS

# States for ConversationHandlers
ADD_GROUP, ADD_SUBJECT, ADD_SCHEDULE, ADD_EXAM, BROADCAST, SET_SCHEDULE_GROUP, SET_SCHEDULE_DAY, SET_EXAM_GROUP, ADD_EXAM_DATA, SET_ADD_SCHED_GROUP, SET_ADD_SCHED_DAY, ADD_SINGLE_SCHED_DATA = range(12)

WEEKDAYS_KYR = ["Дүйшөмбү", "Шейшемби", "Шаршемби", "Бейшемби", "Жума", "Ишемби"]

async def admin_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in ADMIN_IDS:
        await update.message.reply_text("Сиздин администратордук укугуңуз жок.")
        return
    
    await update.message.reply_text(
        "🛠 Администратор башкы менюсу:",
        reply_markup=admin_menu_keyboard()
    )

async def admin_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if query.data == "admin_edit_schedule":
        from .admin_edit import edit_schedule_start
        return await edit_schedule_start(update, context)
    
    elif query.data == "admin_delete_group":
        from .admin_edit import admin_delete_group_start
        return await admin_delete_group_start(update, context)
    
    elif query.data == "admin_add_exam":
        async with AsyncSessionLocal() as session:
            groups = await session.execute(select(Group))
            groups = groups.scalars().all()
            from keyboards import group_selection_keyboard
            await query.message.edit_text(
                "Экзамен кошуу үчүн топту тандаңыз:",
                reply_markup=group_selection_keyboard(groups)
            )
            return SET_EXAM_GROUP
    
    elif query.data == "admin_stats":
        async with AsyncSessionLocal() as session:
            user_count = await session.execute(select(func.count(User.id)))
            group_count = await session.execute(select(func.count(Group.id)))
            
            msg = f"📊 <b>Статистика</b>\n\n"
            msg += f"👤 Колдонуучулар: {user_count.scalar()}\n"
            msg += f"👥 Топтор: {group_count.scalar()}\n"
            await query.message.edit_text(msg, parse_mode="HTML", reply_markup=admin_menu_keyboard())
            return ConversationHandler.END
    
    elif query.data == "admin_deduplicate":
        return await admin_deduplicate(update, context)
    
    elif query.data == "admin_back":
        from .admin_edit import admin_back
        return await admin_back(update, context)
        
    elif query.data == "admin_quick_schedule":
        async with AsyncSessionLocal() as session:
            groups = await session.execute(select(Group))
            groups = groups.scalars().all()
            if not groups:
                await query.message.edit_text("Топтор табылган жок!")
                return ConversationHandler.END
            
            from keyboards import group_selection_keyboard
            await query.message.edit_text(
                "Ыкчам расписание үчүн группаны тандаңыз:",
                reply_markup=group_selection_keyboard(groups)
            )
            return SET_SCHEDULE_GROUP

    elif query.data == "admin_broadcast":
        await query.message.edit_text("Жалпы билдирүүнү жазыңыз (же /cancel):")
        return BROADCAST

    elif query.data == "admin_add_group":
        await query.message.edit_text("Топтун маалыматын жазыңыз (Мисалы: <code>ПИ-1-24, 1</code>):", parse_mode="HTML")
        return ADD_GROUP

    elif query.data == "admin_add_subject":
        await query.message.edit_text("Сабактын маалыматын жазыңыз (Мисалы: <i>Математика, Иванов И.И., лекция</i>):", parse_mode="HTML")
        return ADD_SUBJECT
    
    elif query.data == "admin_add_schedule":
        async with AsyncSessionLocal() as session:
            groups = await session.execute(select(Group))
            groups = groups.scalars().all()
            if not groups:
                await query.message.edit_text("Топтор табылган жок!")
                return ConversationHandler.END
            
            from keyboards import group_selection_keyboard
            await query.message.edit_text(
                "Сабак кошуу үчүн группаны тандаңыз:",
                reply_markup=group_selection_keyboard(groups)
            )
            return SET_ADD_SCHED_GROUP

async def process_broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    async with AsyncSessionLocal() as session:
        users = await session.execute(select(User))
        users = users.scalars().all()
        
        count = 0
        for u in users:
            try:
                await context.bot.send_message(chat_id=u.telegram_id, text=f"📢 <b>Жалпы билдирүү:</b>\n\n{text}", parse_mode="HTML")
                count += 1
            except: pass
        
    await update.message.reply_text(f"Билдирүү {count} колдонуучуга жиберилди.")
    return ConversationHandler.END

async def process_add_group(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    try:
        data = [i.strip() for i in text.split(",")]
        if not data:
            return ADD_GROUP
            
        name = data[0]
        course = 1 # Default
        
        # Look for a number in the rest of the parts
        found_course = False
        for item in data[1:]:
            if item.isdigit():
                course = int(item)
                found_course = True
                break
        
        if len(data) < 2 or (not found_course and not data[1].isdigit()):
            if not found_course:
                # If they just wrote "Group Name", ask again
                await update.message.reply_text("Топтун атын жана курсун жазыңыз (Мисалы: <code>ПИ-1-24, 1</code>).", parse_mode="HTML")
                return ADD_GROUP

        faculty = "ИИТПФ"
        async with AsyncSessionLocal() as session:
            new_group = Group(name=name, faculty=faculty, course=course)
            session.add(new_group)
            await session.commit()
        await update.message.reply_text(f"✅ Топ ийгиликтүү кошулду: {name}\nКурсу: {course}", reply_markup=main_menu_keyboard(True, user_id=update.effective_user.id))
    except Exception as e:
        await update.message.reply_text(f"Базага кошуу катасы: {e}")
    return ConversationHandler.END

async def process_add_subject(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        data = [i.strip() for i in update.message.text.split(",")]
        name, teacher, s_type = data[0], data[1], data[2]
        async with AsyncSessionLocal() as session:
            new_s = Subject(name=name, teacher_name=teacher, subject_type=s_type)
            session.add(new_s)
            await session.commit()
        await update.message.reply_text(f"Сабак кошулду: {name}")
    except Exception as e:
        await update.message.reply_text(f"Ката: {e}")
    return ConversationHandler.END

async def process_add_schedule(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        data = [i.strip() for i in update.message.text.split(",")]
        g_id, s_id, w_day, start, end, room, w_type = int(data[0]), int(data[1]), int(data[2]), data[3], data[4], data[5], data[6]
        async with AsyncSessionLocal() as session:
            new_sch = Schedule(group_id=g_id, subject_id=s_id, weekday=w_day, start_time=start, end_time=end, room=room, week_type=w_type)
            session.add(new_sch)
            await session.commit()
        await update.message.reply_text(f"Расписание кошулду!")
    except Exception as e:
        await update.message.reply_text(f"Ката: {e}")
    return ConversationHandler.END

async def process_set_schedule_group(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    group_id = int(query.data.split("_")[-1])
    context.user_data["admin_sched_group"] = group_id
    context.user_data["admin_sched_day"] = 0 # Start with Monday
    
    await query.message.edit_text(
        f"Группа тандалды. Эми <b>{WEEKDAYS_KYR[0]}</b> үчүн сабактарды жазыңыз.\n"
        f"Формат: <code>СабакАты, Убакыт, Кабинет, МугалимдинАты</code> (ар бир сабак жаңы сапта болсун).\n"
        f"Мугалимдин аты милдеттүү эмес.\n"
        f"Өткөрүп жиберүү үчүн <code>/skip</code> жазыңыз.",
        parse_mode="HTML"
    )
    return SET_SCHEDULE_DAY

async def process_set_schedule_day(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    group_id = context.user_data.get("admin_sched_group")
    day_idx = context.user_data.get("admin_sched_day", 0)

    if text.lower() != "/skip":
        try:
            async with AsyncSessionLocal() as session:
                lines = [line.strip() for line in text.strip().split("\n") if line.strip()]
                for line in lines:
                    parts = [p.strip() for p in line.split(",")]
                    if len(parts) >= 2:
                        sub_name = parts[0]
                        time_range = parts[1] # e.g. 09:00-10:20
                        room = parts[2] if len(parts) > 2 else "---"
                        teacher_name = parts[3] if len(parts) > 3 else "Көрсөтүлгөн эмес"
                        
                        # Find or create subject by name AND teacher
                        res = await session.execute(
                            select(Subject).where(Subject.name == sub_name, Subject.teacher_name == teacher_name)
                        )
                        subject = res.scalar_one_or_none()
                        
                        if not subject:
                            subject = Subject(name=sub_name, teacher_name=teacher_name, subject_type="лекция")
                            session.add(subject)
                            await session.commit()
                            await session.refresh(subject)
                        
                        start, end = "", "00:00"
                        if "-" in time_range:
                            time_parts = [t.strip() for t in time_range.split("-")]
                            if len(time_parts) >= 2:
                                start, end = time_parts[0], time_parts[1]
                            else:
                                start = time_parts[0]
                        else:
                            start = time_range
                        
                        # Normalize HH:MM
                        if start and len(start) == 4: start = "0" + start
                        if end and len(end) == 4: end = "0" + end
                        
                        # Check if this exact schedule already exists to prevent duplicates
                        dup_stmt = select(Schedule).where(
                            Schedule.group_id == group_id,
                            Schedule.weekday == day_idx,
                            Schedule.start_time == start
                        )
                        existing_sch = await session.execute(dup_stmt)
                        if not existing_sch.scalar_one_or_none():
                            new_sch = Schedule(
                                group_id=group_id,
                                subject_id=subject.id,
                                weekday=day_idx,
                                start_time=start,
                                end_time=end,
                                room=room,
                                week_type="all"
                            )
                            session.add(new_sch)
                await session.commit()
        except Exception as e:
            await update.message.reply_text(f"❌ Расписаниени иштеп чыгууда ката кетти: {e}. Сураныч, форматты текшериңиз.")
            return SET_SCHEDULE_DAY

    # Move to next day
    day_idx += 1
    if day_idx < 6: # Mon-Sat
        context.user_data["admin_sched_day"] = day_idx
        await update.message.reply_text(
            f"<b>{WEEKDAYS_KYR[day_idx]}</b> үчүн сабактарды жазыңыз (же /skip):",
            parse_mode="HTML"
        )
        return SET_SCHEDULE_DAY
    else:
        await update.message.reply_text("✅ Расписание толук кошулду!", reply_markup=main_menu_keyboard(True, user_id=update.effective_user.id))
        return ConversationHandler.END

async def process_set_exam_group(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    group_id = int(query.data.split("_")[-1])
    context.user_data["admin_exam_group"] = group_id
    
    await query.message.edit_text(
        "Экзамендин маалыматын жазыңыз:\n"
        "Формат: <code>СабакАты, Күнү(кк.аа.жжжж), Убактысы, Кабинет, Түрү</code>\n"
        "Мисалы: <code>Математика, 25.05.2024, 09:00, 301, Экзамен</code>",
        parse_mode="HTML"
    )
    return ADD_EXAM_DATA

async def process_add_exam(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    group_id = context.user_data.get("admin_exam_group")
    
    try:
        data = [p.strip() for p in text.split(",")]
        if len(data) < 5:
            await update.message.reply_text("❌ Формат туура эмес. 5 маалыматты тең жазыңыз.")
            return ADD_EXAM_DATA
            
        sub_name, date_str, exam_time, room, exam_type = data[0], data[1], data[2], data[3], data[4]
        
        from datetime import datetime
        try:
            exam_date = datetime.strptime(date_str, "%d.%m.%Y").date()
        except:
            await update.message.reply_text("❌ Күндүн форматы туура эмес (кк.аа.жжжж болушу керек).")
            return ADD_EXAM_DATA
        
        async with AsyncSessionLocal() as session:
            # Find subject or create one
            res = await session.execute(select(Subject).where(Subject.name == sub_name))
            subject = res.scalar_one_or_none()
            
            if not subject:
                subject = Subject(name=sub_name, teacher_name="Көрсөтүлгөн эмес", subject_type="лекция")
                session.add(subject)
                await session.commit()
                await session.refresh(subject)
            
            new_exam = Exam(
                group_id=group_id,
                subject_id=subject.id,
                exam_date=exam_date,
                exam_time=exam_time,
                room=room,
                exam_type=exam_type
            )
            session.add(new_exam)
            await session.commit()
            
        await update.message.reply_text("✅ Экзамен ийгиликтүү кошулду!", reply_markup=main_menu_keyboard(True, user_id=update.effective_user.id))
    except Exception as e:
        await update.message.reply_text(f"❌ Ката: {e}\nСураныч, форматты текшерип, кайра жазыңыз.")
        return ADD_EXAM_DATA
        
    return ConversationHandler.END

async def process_set_add_sched_group(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    group_id = int(query.data.split("_")[-1])
    context.user_data["add_sched_group"] = group_id
    
    keyboard = []
    for i, day in enumerate(WEEKDAYS_KYR):
        keyboard.append([InlineKeyboardButton(day, callback_data=f"add_sch_day_{i}")])
    
    await query.message.edit_text(
        "Күндү тандаңыз:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return SET_ADD_SCHED_DAY

async def process_set_add_sched_day(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    day_idx = int(query.data.split("_")[-1])
    context.user_data["add_sched_day"] = day_idx
    
    await query.message.edit_text(
        f"<b>{WEEKDAYS_KYR[day_idx]}</b> үчүн сабактын маалыматын жазыңыз:\n"
        "Формат: <code>СабакАты, Убакыт, Кабинет, МугалимдинАты</code>\n"
        "Мисалы: <code>Математика, 09:00-10:20, 301, Иванов И.И.</code>",
        parse_mode="HTML"
    )
    return ADD_SINGLE_SCHED_DATA

async def process_add_single_schedule(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    group_id = context.user_data.get("add_sched_group")
    day_idx = context.user_data.get("add_sched_day")
    
    try:
        parts = [p.strip() for p in text.split(",")]
        if len(parts) < 3:
            await update.message.reply_text("❌ Формат туура эмес. Кеминде Сабак, Убакыт жана Кабинетти жазыңыз.")
            return ADD_SINGLE_SCHED_DATA
            
        sub_name = parts[0]
        time_range = parts[1]
        room = parts[2]
        teacher_name = parts[3] if len(parts) > 3 else "Көрсөтүлгөн эмес"
        
        start, end = "", "00:00"
        if "-" in time_range:
            time_parts = [t.strip() for t in time_range.split("-")]
            if len(time_parts) >= 2:
                start, end = time_parts[0], time_parts[1]
            else:
                start = time_parts[0]
        else:
            start = time_range
            
        # Normalize HH:MM
        if start and len(start) == 4: start = "0" + start
        if end and len(end) == 4: end = "0" + end
            
        async with AsyncSessionLocal() as session:
            # Find or create subject
            res = await session.execute(
                select(Subject).where(Subject.name == sub_name, Subject.teacher_name == teacher_name)
            )
            subject = res.scalar_one_or_none()
            
            if not subject:
                subject = Subject(name=sub_name, teacher_name=teacher_name, subject_type="лекция")
                session.add(subject)
                await session.commit()
                await session.refresh(subject)
            
            # Check for duplicates
            dup_stmt = select(Schedule).where(
                Schedule.group_id == group_id,
                Schedule.weekday == day_idx,
                Schedule.start_time == start
            )
            existing_sch = await session.execute(dup_stmt)
            if existing_sch.scalar_one_or_none():
                await update.message.reply_text("⚠️ Бул сабак мурда эле кошулган!")
                return ConversationHandler.END

            new_sch = Schedule(
                group_id=group_id,
                subject_id=subject.id,
                weekday=day_idx,
                start_time=start,
                end_time=end,
                room=room,
                week_type="all"
            )
            session.add(new_sch)
            await session.commit()
            
        await update.message.reply_text("✅ Сабак ийгиликтүү кошулду!", reply_markup=main_menu_keyboard(True, user_id=update.effective_user.id))
    except Exception as e:
        await update.message.reply_text(f"❌ Ката: {e}")
        return ADD_SINGLE_SCHED_DATA
        
    return ConversationHandler.END

async def admin_deduplicate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer("Тазалоо башталды...")
    
    async with AsyncSessionLocal() as session:
        res = await session.execute(select(Schedule))
        all_schedules = res.scalars().all()
        
        seen = set()
        to_delete = []
        
        for s in all_schedules:
            key = (s.group_id, s.weekday, s.start_time)
            if key in seen:
                to_delete.append(s.id)
            else:
                seen.add(key)
        
        count = len(to_delete)
        if to_delete:
            stmt = delete(Schedule).where(Schedule.id.in_(to_delete))
            await session.execute(stmt)
            await session.commit()
            await query.message.edit_text(f"✅ Тазалоо бүттү! {count} кайталанган сабактар өчүрүлдү.", reply_markup=admin_menu_keyboard())
        else:
            await query.message.edit_text("✅ Кайталанган сабактар табылган жок.", reply_markup=admin_menu_keyboard())
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Жоюлду.", reply_markup=main_menu_keyboard(True, user_id=update.effective_user.id))
    return ConversationHandler.END
