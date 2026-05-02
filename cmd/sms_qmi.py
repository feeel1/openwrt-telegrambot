import asyncio
import json
import logging
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes
from telegram.helpers import escape_markdown

VERSION = "1.0.0"
IS_MENU_COMMAND = True
# Пути к ресурсам
SH_SCRIPT = "/www/assisten/bot/scripts/sms_manager.sh"

async def execute(update: Update, context: ContextTypes.DEFAULT_TYPE, command_data: str = None) -> None:
    chat_id = update.effective_chat.id
    query = update.callback_query

    # Определяем действие: чтение или очистка
    action = "read"
    if command_data and "|" in command_data:
        action = command_data.split("|")[1]

    if action == "clear":
        await delete_sms(update, context)
    else:
        await list_sms(update, context)

async def list_sms(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    # Вызываем shell-скрипт для чтения
    process = await asyncio.create_subprocess_exec(
        '/bin/sh', SH_SCRIPT, 'read',
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )
    stdout, _ = await process.communicate()
    output = stdout.decode('utf-8').strip()

    if not output or "empty" in output:
        text = "📬 **SMS**\n\nСообщений не найдено."
    else:
        # Парсим вывод (может быть несколько JSON объектов подряд)
        messages = []
        # Разделяем по закрывающей скобке и добавляем её обратно для корректного JSON
        raw_blocks = output.replace('}{', '}\n{').split('\n')
        
        for block in raw_blocks[-5:]: # Последние 5
            try:
                data = json.loads(block)
                msg = (f"👤 *{data.get('sender')}*\n"
                       f"📅 _{data.get('timestamp')}_\n"
                       f"`{escape_markdown(data.get('text', ''), version=2)}`")
                messages.append(msg)
            except: continue
        
        text = "📬 **Последние сообщения:**\n\n" + "\n\n---\n".join(messages)

    keyboard = [
        [InlineKeyboardButton("🔄 Обновить", callback_data="sms_qmi|read")],
        [InlineKeyboardButton("🗑 Очистить память", callback_data="sms_qmi|clear")]
    ]
    
    if update.callback_query:
        await update.callback_query.edit_message_text(text, parse_mode='MarkdownV2', reply_markup=InlineKeyboardMarkup(keyboard))
    else:
        await context.bot.send_message(chat_id=update.effective_chat.id, text=text, parse_mode='MarkdownV2', reply_markup=InlineKeyboardMarkup(keyboard))

async def delete_sms(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await asyncio.create_subprocess_exec('/bin/sh', SH_SCRIPT, 'clear')
    text = "✅ Память модема (ME) очищена."
    keyboard = [[InlineKeyboardButton("⬅️ Назад", callback_data="sms_qmi|read")]]
    
    if update.callback_query:
        await update.callback_query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
