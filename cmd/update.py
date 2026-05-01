# File: cmd/update.py

import os
import logging
import subprocess
import asyncio
from telegram import Update
from telegram.ext import ContextTypes
from telegram import InlineKeyboardMarkup, InlineKeyboardButton, Message

# versi modul
VERSION = "3.5.0"

IS_MENU_COMMAND = True

logger = logging.getLogger(__name__)

async def execute(update: Update, context: ContextTypes.DEFAULT_TYPE, command_data: str = None) -> None:
    """
    Обрабатывает команду /update и callback от кнопок.
    Функция отображает локальную версию и версию на GitHub,
    предлагая кнопку обновления, если доступна новая версия.
    """
    
    chat_id = update.effective_chat.id
    SCRIPT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    try:
        # Вызов скрипта update.sh для проверки статуса версий
        process = await asyncio.create_subprocess_exec(
            '/bin/sh', os.path.join(SCRIPT_DIR, 'update.sh'), '--check',
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        stdout, stderr = await process.communicate()
        
        output = stdout.decode('utf-8').strip()
        
        # Разделение вывода на строки и поиск версий
        lines = output.split('\n')
        local_version = "Не определено"
        github_version = "Не определено"
        
        for line in lines:
            # Примечание: метки "Versi lokal" и "Versi GitHub" должны соответствовать выводу вашего update.sh
            if "Versi lokal:" in line:
                local_version = line.split(':')[1].strip()
            elif "Versi GitHub:" in line:
                github_version = line.split(':')[1].strip()
        
        message_text = f"⚙️ **Статус обновления**\n"
        message_text += f"Локальная версия: `{local_version}`\n"
        message_text += f"Версия GitHub: `{github_version}`\n"
        
        keyboard = []
        if local_version != "Не определено" and github_version != "Не определено" and local_version != github_version:
            message_text += "Доступно обновление! Нажмите кнопку ниже для установки."
            keyboard.append([InlineKeyboardButton("Install Update", callback_data="install_update")])
        else:
            message_text += "Вы используете актуальную версию."
            
        reply_markup = InlineKeyboardMarkup(keyboard)

        await context.bot.send_message(
            chat_id=chat_id,
            text=message_text,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
        logger.info(f"Статус обновления отправлен в чат {chat_id}.")
        
    except Exception as e:
        logger.error(f"Ошибка при проверке обновлений: {e}")
        await context.bot.send_message(
            chat_id=chat_id,
            text="❌ Произошла ошибка при проверке обновлений."
        )
