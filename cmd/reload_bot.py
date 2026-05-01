import os
import subprocess
import logging
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes

# versi modul
VERSION = "3.5.0"

logger = logging.getLogger(__name__)

async def execute(update: Update, context: ContextTypes.DEFAULT_TYPE, command_data: str) -> None:
    chat_id = update.effective_chat.id
    
    command_parts = command_data.split('|')
    selected_device = command_parts[2]

    # Кнопка "В главное меню"
    keyboard = [
        [InlineKeyboardButton("В главное меню", callback_data="back_to_main_menu")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    if selected_device == os.getenv('DEVICE_ID'):
        try:
            # Удалить сообщение с командой
            await update.callback_query.message.delete()
        except Exception:
            pass
            
        # Отправить сообщение об успешном запуске ДО остановки бота
        await context.bot.send_message(
            chat_id=chat_id, 
            text="✅ Перезапуск бота запущен. Бот снова будет активен через несколько мгновений.",
            reply_markup=reply_markup
        )
        
        try:
            # Вызов скрипта restart.sh в фоновом режиме
            # Это обеспечит корректную остановку и повторный запуск бота
            subprocess.Popen(['/bin/sh', '/www/assisten/bot/restart.sh'])
            
        except FileNotFoundError:
            await context.bot.send_message(
                chat_id=chat_id, 
                text="❌ Ошибка: Файл restart.sh не найден.",
                reply_markup=reply_markup
            )
        except Exception as e:
            await context.bot.send_message(
                chat_id=chat_id, 
                text=f"❌ Ошибка: Произошла ошибка при выполнении restart.sh: {e}",
                reply_markup=reply_markup
            )
    else:
        # Сообщение, если команда запущена не на том устройстве
        await context.bot.send_message(
            chat_id=chat_id, 
            text="Эта команда может быть выполнена только на активном устройстве.",
            reply_markup=reply_markup
        )
