import os
import datetime
import logging
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes

# versi modul
VERSION = "3.5.0"

logger = logging.getLogger(__name__)

async def execute(update: Update, context: ContextTypes.DEFAULT_TYPE, command_data: str) -> None:
    """Извлекает и отображает список DHCP арен из файла /tmp/dhcp.leases."""
    
    selected_device = 'local'
    command_parts = command_data.split('|')
    if len(command_parts) > 2:
        selected_device = command_parts[2]

    leases_file = '/tmp/dhcp.leases'

    # Добавляем кнопку возврата
    keyboard = [[InlineKeyboardButton("Назад в меню команд", callback_data=f"back_to_device_menu|{selected_device}")]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    if not os.path.exists(leases_file):
        await update.effective_message.reply_text(
            "❌ Файл dhcp.leases не найден. Вероятно, подключенных устройств нет.",
            reply_markup=reply_markup
        )
        return

    try:
        with open(leases_file, 'r') as f:
            lines = f.readlines()

        if not lines:
            await update.effective_message.reply_text(
                "Активные DHCP аренды не найдены.",
                reply_markup=reply_markup
            )
            return

        response_text = "✨ **Список подключенных устройств (DHCP Leases)** ✨\n\n"
        
        for line in lines:
            parts = line.strip().split()
            if len(parts) >= 4:
                try:
                    expiry_timestamp = int(parts[0])
                    mac_address = parts[1]
                    ip_address = parts[2]
                    hostname = parts[3]

                    now_timestamp = int(datetime.datetime.now().timestamp())
                    leasetime_remaining = expiry_timestamp - now_timestamp
                    
                    if leasetime_remaining > 0:
                        lease_timedelta = datetime.timedelta(seconds=leasetime_remaining)
                        days, remainder = divmod(lease_timedelta.total_seconds(), 86400)
                        hours, remainder = divmod(remainder, 3600)
                        minutes, seconds = divmod(remainder, 60)
                        lease_str = f"{int(days)}h {int(hours)}j {int(minutes)}m {int(seconds)}d"
                    else:
                        lease_str = "Истекло"

                    response_text += f"**Hostname:** `{hostname}`\n"
                    response_text += f"**IP Address:** `{ip_address}`\n"
                    response_text += f"**MAC Address:** `{mac_address}`\n"
                    response_text += f"**Остаток времени аренды:** `{lease_str}`\n"
                    response_text += "––––––––––––––––––––\n"

                except (ValueError, IndexError) as e:
                    logger.warning(f"Пропуск некорректной строки в dhcp.leases: {line.strip()}. Error: {e}")
                    continue

        await update.effective_message.reply_text(
            response_text,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )

    except Exception as e:
        logger.error(f"Ошибка при чтении файла dhcp.leases: {e}")
        await update.effective_message.reply_text(
            f"❌ Произошла непредвиденная ошибка: `{e}`", 
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
