from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler
from sqlalchemy import select
from database import User, Group, AsyncSessionLocal
from keyboards import main_menu_keyboard, group_selection_keyboard
from config import ADMIN_IDS

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    username = update.effective_user.username
    full_name = update.effective_user.full_name
    
    async with AsyncSessionLocal() as session:
        user = await session.execute(select(User).where(User.telegram_id == user_id))
        user = user.scalar_one_or_none()
        
        if not user:
            is_admin = user_id in ADMIN_IDS
            user = User(
                telegram_id=user_id,
                username=username,
                full_name=full_name,
                is_admin=is_admin
            )
            session.add(user)
            await session.commit()
            await session.refresh(user)
        else:
            # Refresh admin status if changed in config
            is_admin = user_id in ADMIN_IDS
            if user.is_admin != is_admin:
                user.is_admin = is_admin
                await session.commit()
        
        if not user.group_id:
            # Show all groups directly (for IITPF faculty)
            groups = await session.execute(select(Group))
            groups = groups.scalars().all()
            
            if not groups:
                await update.message.reply_text("Топтор табылган жок. Админ менен байланышыңыз.")
                return
            
            await update.message.reply_text(
                "Салам! Кош келиңиз. Өзүңүздүн тобуңузду тандаңыз:",
                reply_markup=group_selection_keyboard(groups)
            )
            return

        await update.message.reply_text(
            f"Салам, {full_name}! Кандай жардам керек?",
            reply_markup=main_menu_keyboard(user.is_admin, user_id=user_id)
        )

async def select_group_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    group_id = int(query.data.split("_")[-1])
    user_id = query.from_user.id
    
    async with AsyncSessionLocal() as session:
        user = await session.execute(select(User).where(User.telegram_id == user_id))
        user = user.scalar_one_or_none()
        
        if user:
            user.group_id = group_id
            
            # Refresh admin status if changed in config
            is_admin = user_id in ADMIN_IDS
            if user.is_admin != is_admin:
                user.is_admin = is_admin
                
            await session.commit()
            
            group = await session.get(Group, group_id)
            await query.message.edit_text(f"Топ ийгиликтүү тандалды: {group.name} ✅")
            await query.message.reply_text(
                "Башкы меню:",
                reply_markup=main_menu_keyboard(user.is_admin, user_id=user_id)
            )

async def change_group(update: Update, context: ContextTypes.DEFAULT_TYPE):
    async with AsyncSessionLocal() as session:
        groups = await session.execute(select(Group))
        groups = groups.scalars().all()
        
        if not groups:
            await update.message.reply_text("Топтор табылган жок.")
            return

        await update.message.reply_text(
            "Жаңы топту тандаңыз:",
            reply_markup=group_selection_keyboard(groups)
        )
