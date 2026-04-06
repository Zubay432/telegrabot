import os
import sys

if __name__ == "__main__":
    # Папканы университет_ботуна алмаштыруу (импорттор туура иштеши үчүн)
    bot_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "university_bot"))
    os.chdir(bot_path)
    sys.path.append(bot_path)
    
    # Ботту иштетүү
    import bot
    bot.main()
