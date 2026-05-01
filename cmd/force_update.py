# File: cmd/force_update.py

import os
import logging
import subprocess
import asyncio
from telegram import Update
from telegram.ext import ContextTypes

IS_MENU_COMMAND = False

# версия модуля
VERSION = "3.5.0"

logger = logging.getLogger(__name__)

# Расположение скрипта force_update.sh
SCRIPT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FORCE_UPDATE_SCRIPT = os.path.join(SCRIPT_DIR, "force_update.sh")

async def execute(update: Update, context: ContextTypes.DEFAULT_TYPE, command_data: str = None) -> None:
    """Обрабатывает команду /force_update для принудительного обновления."""
    
    chat_id = update.effective_chat.id
    
    # Отправка уведомления
    message = "🚨 **Принудительное обновление устройства...**"
    await context.bot.send_message(
        chat_id=chat_id,
        text=message,
        parse_mode='Markdown'
    )
    logger.info("Получена команда /force_update. Запуск скрипта принудительного обновления.")

    # Запуск скрипта force_update.sh асинхронно
    subprocess.Popen(['/bin/sh', FORCE_UPDATE_SCRIPT])
    
    # Строка остановки приложения удалена по инструкции:
    # await context.application.stop()
