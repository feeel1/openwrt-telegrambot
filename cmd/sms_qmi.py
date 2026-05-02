import asyncio
import json
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes
from telegram.helpers import escape_markdown

# Метаданные для help.py
VERSION = "1.5.0"
IS_MENU_COMMAND = True
SH_SCRIPT = "/www/assisten/bot/scripts/sms_manager.sh"

async def execute(update: Update, context: ContextTypes.DEFAULT_TYPE, command_data: str = None) -> None:
    chat_id = update.effective_chat.id
    
    # Определяем действие: чтение (по умолчанию) или очистка
    action = "read"
    if command_data and "|" in command_data:
        action = command_data.split("|")[1]

    if action == "clear":
        # Вызов удаления
        await asyncio.create_subprocess_exec('/bin/sh', SH_SCRIPT, 'clear')
        text = "✅ Все SMS в памяти модема удалены."
        keyboard = [[InlineKeyboardButton("⬅️ Назад к списку", callback_data="sms_qmi|read")]]
    else:
        # Чтение сообщений
        proc = await asyncio.create_subprocess_exec(
            '/bin/sh', SH_SCRIPT, 'read',
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, _ = await proc.communicate()
        output = stdout.decode('utf-8').strip()

        if not output or "empty" in output:
            text = "📬 **SMS (QMI)**\n\nСообщений не найдено."
        else:
            messages = []
            # Обработка вывода (может быть несколько JSON объектов)
            raw_blocks = output.replace('}{', '}\n{').split('\n')
            for block in raw_blocks[-5:]: # Последние 5 сообщений
                try:
                    data = json.loads(block)
                    msg = (f"👤 *{data.get('sender', 'Unknown')}*\n"
                           f"📅 _{data.get('timestamp', '')}_\n"
                           f"`{escape_markdown(data.get('text', ''), version=2)}`")
                    messages.append(msg)
                except:
                    continue
            text = "📬 **Последние входящие:**\n\n" + "\n\n---\n".join(messages)

        keyboard = [
            [InlineKeyboardButton("🔄 Обновить", callback_data="sms_qmi|read")],
            [InlineKeyboardButton("🗑 Очистить память", callback_data="sms_qmi|clear")]
        ]

    reply_markup = InlineKeyboardMarkup(keyboard)

    # Если это нажатие кнопки — редактируем старое сообщение, если команда /sms_qmi — шлем новое
    if update.callback_query:
        await update.callback_query.edit_message_text(text, parse_mode='MarkdownV2', reply_markup=reply_markup)
    else:
        await context.bot.send_message(chat_id=chat_id, text=text, parse_mode='MarkdownV2', reply_markup=reply_markup)
