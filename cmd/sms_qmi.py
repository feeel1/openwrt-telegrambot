import asyncio
import json
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes
from telegram.helpers import escape_markdown

VERSION = "1.6.0"
IS_MENU_COMMAND = True
SH_SCRIPT = "/www/assisten/bot/scripts/sms_manager.sh"
MAX_MESSAGES = 8


def _format_message(item: dict) -> str:
    payload = item.get("payload", {})
    sender = escape_markdown(str(payload.get("sender", "Unknown")), version=2)
    timestamp = escape_markdown(str(payload.get("timestamp", "")), version=2)
    text = escape_markdown(str(payload.get("text", "")), version=2)
    storage = escape_markdown(str(item.get("storage", "?")).upper(), version=2)
    index = escape_markdown(str(item.get("index", "?")), version=2)
    return (
        f"👤 *{sender}*\n"
        f"📦 `{storage}`  •  ID `{index}`\n"
        f"📅 _{timestamp}_\n"
        f"{text}"
    )


async def execute(update: Update, context: ContextTypes.DEFAULT_TYPE, command_data: str = None) -> None:
    chat_id = update.effective_chat.id
    action = "read"
    selected_device = "local"

    if command_data and "|" in command_data:
        parts = command_data.split("|")
        if len(parts) > 1:
            action = parts[1]
        if len(parts) > 2:
            selected_device = parts[2]

    back_callback = f"back_to_device_menu|{selected_device}"

    if action == "clear":
        proc = await asyncio.create_subprocess_exec(
            "/bin/sh",
            SH_SCRIPT,
            "clear",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await proc.communicate()
        output = stdout.decode("utf-8").strip()
        error_output = stderr.decode("utf-8").strip()

        text = "✅ Все SMS в памяти модема удалены."
        if proc.returncode != 0:
            text = "❌ Не удалось очистить SMS в памяти модема."
            if error_output:
                text += f"\n\n`{escape_markdown(error_output, version=2)}`"
        elif output:
            try:
                result = json.loads(output.splitlines()[-1])
                deleted = result.get("deleted")
                if deleted is not None:
                    text = f"✅ Удалено сообщений: *{deleted}*"
            except json.JSONDecodeError:
                pass

        keyboard = [
            [InlineKeyboardButton("🔄 Обновить", callback_data=f"sms_qmi|read|{selected_device}")],
            [InlineKeyboardButton("⬅️ Назад", callback_data=back_callback)],
        ]
    else:
        proc = await asyncio.create_subprocess_exec(
            "/bin/sh",
            SH_SCRIPT,
            "read",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await proc.communicate()
        output = stdout.decode("utf-8").strip()
        error_output = stderr.decode("utf-8").strip()

        messages = []
        script_error = None

        if output:
            for line in output.splitlines():
                line = line.strip()
                if not line:
                    continue
                try:
                    item = json.loads(line)
                except json.JSONDecodeError:
                    continue

                status = item.get("status")
                if status == "error":
                    script_error = item.get("message", "Неизвестная ошибка")
                elif status == "ok":
                    messages.append(item)

        if proc.returncode != 0 and not script_error:
            script_error = error_output or "Скрипт чтения SMS завершился с ошибкой"

        if script_error:
            text = "❌ *SMS \(QMI\)*\n\n"
            text += escape_markdown(script_error, version=2)
        elif not messages:
            text = "📬 *SMS \(QMI\)*\n\nСообщений не найдено\."
        else:
            rendered = [_format_message(item) for item in messages[-MAX_MESSAGES:]]
            text = "📬 *Последние входящие SMS*\n\n" + "\n\n".join(rendered)

        keyboard = [
            [InlineKeyboardButton("🔄 Обновить", callback_data=f"sms_qmi|read|{selected_device}")],
            [InlineKeyboardButton("🗑 Очистить память", callback_data=f"sms_qmi|clear|{selected_device}")],
            [InlineKeyboardButton("⬅️ Назад", callback_data=back_callback)],
        ]

    reply_markup = InlineKeyboardMarkup(keyboard)

    if update.callback_query:
        await update.callback_query.edit_message_text(
            text,
            parse_mode="MarkdownV2",
            reply_markup=reply_markup,
        )
    else:
        await context.bot.send_message(
            chat_id=chat_id,
            text=text,
            parse_mode="MarkdownV2",
            reply_markup=reply_markup,
        )
