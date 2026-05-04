import os
import logging
import subprocess
import asyncio
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes

# Версия модуля
VERSION = "3.5.3"

# Флаг для отображения в главном меню
IS_MENU_COMMAND = True

logger = logging.getLogger(__name__)

async def execute(update: Update, context: ContextTypes.DEFAULT_TYPE, command_data: str = None) -> None:
    """
    Обрабатывает команду /update и нажатия кнопок.
    Проверяет версии через update.sh и запускает процесс обновления.
    """
    
    chat_id = update.effective_chat.id
    # Определяем путь к скрипту обновления (на уровень выше от папки cmd)
    SCRIPT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    UPDATE_SCRIPT = os.path.join(SCRIPT_DIR, 'update.sh')
    
    if update.callback_query:
        await update.callback_query.answer()

    # --- БЛОК 1: ЗАПУСК УСТАНОВКИ ---
    if command_data == "install":
        msg_install = "🚀 *Запуск обновления...*\nБот будет перезапущен. Пожалуйста, подождите."
        try:
            if update.callback_query:
                await update.callback_query.edit_message_text(text=msg_install, parse_mode='Markdown')
            else:
                await context.bot.send_message(chat_id=chat_id, text=msg_install, parse_mode='Markdown')
            
            # Запуск процесса обновления
            await asyncio.create_subprocess_exec('/bin/sh', UPDATE_SCRIPT, '--force')
            return
        except Exception as e:
            logger.error(f"Ошибка при запуске обновления: {e}")
            await context.bot.send_message(chat_id=chat_id, text="❌ Ошибка при выполнении скрипта обновления.")
            return

    # --- БЛОК 2: ПРОВЕРКА СТАТУСА ---
    try:
        # Вызов скрипта в режиме проверки
        process = await asyncio.create_subprocess_exec(
            '/bin/sh', UPDATE_SCRIPT, '--check',
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        stdout, stderr = await process.communicate()
        output = stdout.decode('utf-8').strip()
        
        local_version = "Не определено"
        github_version = "Не определено"

        if output:
            lines = output.split('\n')
            for line in lines:
                # Ищем русские ключи, которые мы прописали в update.sh
                if "Локальная версия:" in line:
                    local_version = line.split(':')[1].strip()
                elif "Версия на GitHub:" in line or "Versi GitHub:" in line:
                    github_version = line.split(':')[1].strip()
        
        message_text = f"⚙️ **Статус обновления**\n\n"
        message_text += f"Локальная версия: `{local_version}`\n"
        message_text += f"Версия GitHub: `{github_version}`\n\n"
        
        keyboard = []
        if local_version != "Не определено" and github_version != "Не определено" and local_version != github_version:
            message_text += "✨ Доступна новая версия! Желаете обновить?"
            keyboard.append([
                InlineKeyboardButton("✅ Обновить", callback_data="update|install"),
                InlineKeyboardButton("⬅️ Назад", callback_data="help")
            ])
        else:
            message_text += "✅ У вас установлена последняя версия."
            keyboard.append([InlineKeyboardButton("⬅️ Назад", callback_data="help")])
            
        reply_markup = InlineKeyboardMarkup(keyboard)

        # Пытаемся отправить сообщение
        try:
            if update.callback_query:
                await update.callback_query.edit_message_text(
                    text=message_text, 
                    reply_markup=reply_markup, 
                    parse_mode='Markdown'
                )
            else:
                await context.bot.send_message(
                    chat_id=chat_id, 
                    text=message_text, 
                    reply_markup=reply_markup, 
                    parse_mode='Markdown'
                )
        except Exception as msg_err:
            # Если не удалось отредактировать (например, сообщение удалено), шлем новое
            logger.warning(f"Редактирование не удалось, шлю новое: {msg_err}")
            await context.bot.send_message(
                chat_id=chat_id, 
                text=message_text, 
                reply_markup=reply_markup, 
                parse_mode='Markdown'
            )
        
    except Exception as e:
        logger.error(f"Критическая ошибка модуля обновления: {e}")
        error_kb = [[InlineKeyboardButton("⬅️ Назад", callback_data="help")]]
        await context.bot.send_message(
            chat_id=chat_id, 
            text="❌ Не удалось получить данные от системы обновления.",
            reply_markup=InlineKeyboardMarkup(error_kb)
        )
