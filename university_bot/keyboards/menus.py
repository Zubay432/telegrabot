from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton

def main_menu_keyboard(is_admin=False, user_id=None):
    from config import ADMIN_IDS
    
    # If not admin in DB but in config, treat as admin
    if user_id and user_id in ADMIN_IDS:
        is_admin = True
        
    keyboard = [
        ["📅 Бүгүн", "📆 Эртең"],
        ["🗓 Жумалык", "🎓 Экзамендер"],
        ["🔍 Мугалимди издөө", "👥 Топту өзгөртүү"],
        ["🔔 Билдирүү (Күйгүзүү/Өчүрүү)"]
    ]
    if is_admin:
        keyboard.append(["🛠 Админ Меню"])
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def admin_menu_keyboard():
    keyboard = [
        [InlineKeyboardButton("➕ Топ кошуу", callback_data="admin_add_group")],
        [InlineKeyboardButton("🗑 Топту өчүрүү", callback_data="admin_delete_group")],
        [InlineKeyboardButton("📚 Сабак кошуу", callback_data="admin_add_subject")],
        [InlineKeyboardButton("🗓 Расписание кошуу", callback_data="admin_add_schedule")],
        [InlineKeyboardButton("⚡️ Ыкчам расписание", callback_data="admin_quick_schedule")],
        [InlineKeyboardButton("✏️ Расписаниени оңдоо", callback_data="admin_edit_schedule")],
        [InlineKeyboardButton("🎓 Экзамен кошуу", callback_data="admin_add_exam")],
        [InlineKeyboardButton("📢 Жалпы билдирүү", callback_data="admin_broadcast")],
        [InlineKeyboardButton("🧹 Тазалоо (Duplicates)", callback_data="admin_deduplicate")],
        [InlineKeyboardButton("📊 Статистика", callback_data="admin_stats")]
    ]
    return InlineKeyboardMarkup(keyboard)

def faculty_selection_keyboard(faculties):
    keyboard = []
    for faculty in faculties:
        keyboard.append([InlineKeyboardButton(faculty, callback_data=f"select_faculty_{faculty}")])
    return InlineKeyboardMarkup(keyboard)

def group_selection_keyboard(groups):
    keyboard = []
    for group in groups:
        keyboard.append([InlineKeyboardButton(group.name, callback_data=f"select_group_{group.id}")])
    return InlineKeyboardMarkup(keyboard)

def confirm_keyboard():
    keyboard = [
        [InlineKeyboardButton("Ооба", callback_data="confirm_yes"), 
         InlineKeyboardButton("Жок", callback_data="confirm_no")]
    ]
    return InlineKeyboardMarkup(keyboard)
