import os
import subprocess
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes
import logging

# versi modul
VERSION = "3.5.0"

DEVICE_ID = os.environ.get('DEVICE_ID', 'rumah-menteng.net')

async def execute(update: Update, context: ContextTypes.DEFAULT_TYPE, command_data: str = None) -> None:
    """Обрабатывает команды интерфейса для отображения списка или деталей."""
    
    # --- Код для удаления предыдущего сообщения ---
    try:
        await update.effective_message.delete()
    except Exception as e:
        logging.warning(f"Не удалось удалить сообщение меню: {e}")
    # --- Конец кода ---
    
    message_obj = update.effective_message
    chat_id = message_obj.chat_id

    # Разбор `callback_data` нажатой кнопки
    action = 'menu'
    interface_name = None
    if command_data:
        command_parts = command_data.split('|')
        if len(command_parts) > 1:
            action = command_parts[1]
        
        if action == 'detail' and len(command_parts) > 3:
            interface_name = command_parts[3]

    if action == 'detail':
        await get_interface_details_ifconfig(update, context, interface_name)
    else:
        await send_interface_menu(update, context, chat_id)

async def send_interface_menu(update: Update, context: ContextTypes.DEFAULT_TYPE, chat_id: int) -> None:
    """Отправляет меню со списком интерфейсов."""
    try:
        interfaces = os.listdir('/sys/class/net/')
        interfaces.sort()
        keyboard = []
        for interface in interfaces:
            keyboard.append([InlineKeyboardButton(interface, callback_data=f"interface|detail|{DEVICE_ID}|{interface}")])

        keyboard.append([InlineKeyboardButton("Назад", callback_data=f"back_to_device_menu|{DEVICE_ID}")])
        reply_markup = InlineKeyboardMarkup(keyboard)

        await context.bot.send_message(
            chat_id=chat_id,
            text=f"Выберите интерфейс для просмотра деталей:",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    except Exception as e:
        logging.error(f"Ошибка при загрузке списка интерфейсов: {e}")
        await context.bot.send_message(
            chat_id=chat_id,
            text="❌ Не удалось загрузить список интерфейсов. Попробуйте позже."
        )

async def get_interface_details_ifconfig(update: Update, context: ContextTypes.DEFAULT_TYPE, interface_name: str) -> None:
    """Извлекает и отображает детальную информацию с помощью ifconfig."""
    try:
        logging.info(f"Запрос деталей для интерфейса: {interface_name}")
        
        command = f"ifconfig {interface_name}"
        output = subprocess.run(command, shell=True, capture_output=True, text=True, check=True).stdout

        if not output.strip():
            status_message = f"ℹ️ Детали для интерфейса `{interface_name}` отсутствуют."
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=status_message,
                parse_mode='Markdown'
            )
            return
        
        mac_addr = 'N/A'
        inet_addr = 'N/A'
        rx_mi_bytes = 0
        tx_mi_bytes = 0
        rx_packets = 0
        tx_packets = 0

        lines = output.split('\n')
        for line in lines:
            if 'HWaddr' in line:
                mac_addr = line.split('HWaddr')[1].strip()
            if 'inet addr:' in line:
                inet_addr_raw = line.split('inet addr:')[1].split()[0]
                mask_raw = line.split('Mask:')[1].split()[0]
                cidr = sum([bin(int(x)).count('1') for x in mask_raw.split('.')])
                inet_addr = f"{inet_addr_raw}/{cidr}"
            if 'RX bytes' in line:
                try:
                    rx_bytes = int(line.split('RX bytes:')[1].split()[0])
                    rx_mi_bytes = rx_bytes / 1024 / 1024
                    rx_packets = line.split('packets:')[1].split()[0]
                except (ValueError, IndexError):
                    pass
            if 'TX bytes' in line:
                try:
                    tx_bytes = int(line.split('TX bytes:')[1].split()[0])
                    tx_mi_bytes = tx_bytes / 1024 / 1024
                    tx_packets = line.split('packets:')[1].split()[0]
                except (ValueError, IndexError):
                    pass

        dns_servers = 'N/A'
        try:
            dns_output = subprocess.run("cat /etc/resolv.conf", shell=True, capture_output=True, text=True).stdout.strip()
            dns_lines = [line for line in dns_output.split('\n') if line.startswith('nameserver')]
            if dns_lines:
                dns_servers = ', '.join([line.split()[1] for line in dns_lines])
            else:
                dns_servers = "DNS-серверы не обнаружены."
        except Exception:
            pass

        status_message = (
            f"**Interface: `{interface_name}`**\n"
            f"MAC: `{mac_addr}`\n"
            f"IPv4: `{inet_addr}`\n"
            f"DNS: `{dns_servers}`\n"
            f"RX: `{rx_mi_bytes:.2f} MiB ({rx_packets} Pkts.)`\n"
            f"TX: `{tx_mi_bytes:.2f} MiB ({tx_packets} Pkts.)`"
        )
        
        keyboard = [
            [InlineKeyboardButton("Назад", callback_data=f"interface|menu|{DEVICE_ID}")],
            [InlineKeyboardButton("В главное меню", callback_data=f"back_to_main_menu|{DEVICE_ID}")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=status_message,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    except subprocess.CalledProcessError as e:
        error_message = f"❌ Ошибка при получении деталей интерфейса `{interface_name}`.\nKesalahan: `{e.stderr.strip()}`"
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=error_message,
            parse_mode='Markdown'
        )
    except Exception as e:
        error_message = f"❌ Произошла непредвиденная ошибка: `{e}`"
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=error_message,
            parse_mode='Markdown'
        )
