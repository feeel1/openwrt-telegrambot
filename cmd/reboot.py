import os
import subprocess
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes
import logging

# versi modul
VERSION = "3.5.0"

DEVICE_ID = os.environ.get('DEVICE_ID', 'rumah-menteng.net')

async def execute(update: Update, context: ContextTypes.DEFAULT_TYPE, command_data: str = None) -> None:
    """Обрабатывает команду перезагрузки с подтверждением."""

    message_obj = update.effective_message
    chat_id = message_obj.chat_id

    # Разбор `callback_data` нажатой кнопки
    if command_data:
        command_parts = command_data.split('|')
        action = command_parts[1] if len(command_parts) > 1 else 'menu'
    else:
        action = 'menu'

    if action == 'confirm':
        await context.bot.send_message(
            chat_id=chat_id,
            text="🔄 Устройство перезагружается...",
            parse_mode='Markdown'
        )
        try:
            logging.info(f"Выполнение команды reboot")
            subprocess.run(["/sbin/reboot"], check=True)
        except subprocess.CalledProcessError as e:
            error_message = f"❌ Не удалось выполнить команду `reboot`.\nОшибка: `{e.stderr.strip()}`"
            await context.bot.send_message(
                chat_id=chat_id,
                text=error_message,
                parse_mode='Markdown'
            )
        except Exception as e:
            error_message = f"❌ Произошла непредвиденная ошибка: `{e}`"
            await context.bot.send_message(
                chat_id=chat_id,
                text=error_message,
                parse_mode='Markdown'
            )
    else:
        keyboard = [
            [InlineKeyboardButton("✅ Да, перезагрузить сейчас", callback_data=f"reboot|confirm|{DEVICE_ID}")],
            [InlineKeyboardButton("❌ Отмена", callback_data=f"back_to_device_menu|{DEVICE_ID}")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await context.bot.send_message(
            chat_id=chat_id,
            text="❗ **Вы уверены, что хотите перезагрузить устройство?**",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
