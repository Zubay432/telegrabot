import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN", "8625415740:AAEN7eUOstFqO8wjVctVNHxBMCbADVoE9p8")
ADMIN_IDS = [8350108810, 7574764214]  # Администраторлордун ID номерлери
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./university.db")
TIMEZONE = os.getenv("TIMEZONE", "Asia/Bishkek")
