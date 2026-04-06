from datetime import datetime, date
import pytz
from config import TIMEZONE

def get_current_week_type():
    # ISO week number: Odd/Even
    now = datetime.now(pytz.timezone(TIMEZONE))
    week_num = now.isocalendar()[1]
    return "odd" if week_num % 2 != 0 else "even"

def format_schedule(schedules, title):
    if not schedules:
        return f"<b>{title}</b>\n\nБош күн! 🎉"
    
    msg = f"<b>{title}</b>\n\n"
    for s in schedules:
        msg += f"📚 <b>{s.subject.name}</b>\n"
        msg += f"⏰ {s.start_time} - {s.end_time}\n"
        msg += f"📍 Кабинет: {s.room}\n"
        msg += f"👨‍🏫 Мугалим: {s.subject.teacher_name}\n"
        msg += f"────────────────\n\n"
    return msg

def format_exams(exams):
    if not exams:
        return "Жакында экзамендер жок. 👏"
    
    msg = "<b>🎓 Жакынкы экзамендер</b>\n\n"
    now = datetime.now(pytz.timezone(TIMEZONE))
    
    for e in exams:
        # Combine date and time
        try:
            exam_dt = datetime.combine(e.exam_date, datetime.strptime(e.exam_time, "%H:%M").time())
            exam_dt = pytz.timezone(TIMEZONE).localize(exam_dt)
        except:
            exam_dt = datetime.combine(e.exam_date, datetime.min.time())
            exam_dt = pytz.timezone(TIMEZONE).localize(exam_dt)

        diff = exam_dt - now
        days = diff.days
        hours = diff.seconds // 3600
        
        if diff.total_seconds() < 0:
            status = "Аяктады же учурда өтүп жатат"
        else:
            status = f"{days} күн, {hours} саат"
            
        msg += f"📚 <b>{e.subject.name}</b>\n"
        msg += f"📅 Күнү: {e.exam_date.strftime('%d.%m.%Y')} ({e.exam_time})\n"
        msg += f"📍 Кабинет: {e.room}\n"
        msg += f"📝 Түрү: {e.exam_type}\n"
        msg += f"⏳ Каалды: {status}\n"
        msg += f"────────────────\n\n"
    return msg
