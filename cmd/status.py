import os
import subprocess
import re
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes
import logging

# versi modul
VERSION = "3.5.0"

DEVICE_ID = os.environ.get('DEVICE_ID', 'rumah-menteng.net')

def format_memory(value_mb: str) -> str:
    """Конвертирует значение из МБ в ГБ, если оно больше 1024 МБ."""
    try:
        value_mb = int(value_mb)
        if value_mb > 1024:
            value_gb = value_mb / 1024
            return f"{value_gb:.2f} GB"
        return f"{value_mb} MB"
    except (ValueError, TypeError):
        return f"{value_mb} MB"

async def execute(update: Update, context: ContextTypes.DEFAULT_TYPE, command_data: str = None) -> None:
    """Выполняет команду 'status' и отправляет результат."""

    try:
        # Получение информации о CPU из /proc/cpuinfo
        cpuinfo_output = subprocess.run(['cat', '/proc/cpuinfo'], capture_output=True, text=True, check=True).stdout.strip()
        
        cpu_model_match = re.search(r'model name\s*:\s*(.*)', cpuinfo_output)
        cpu_model = cpu_model_match.group(1).strip() if cpu_model_match else "Недоступно"
        
        cores_count = len(re.findall(r'processor\s*:', cpuinfo_output))

        # Получение архитектуры CPU
        try:
            arch_output = subprocess.run(['opkg', 'print-architecture'], capture_output=True, text=True, check=True).stdout.strip()
            arch_matches = re.findall(r'arch\s+((?!all|noarch)\S+)\s+\d+', arch_output)
            cpu_arch = arch_matches[0] if arch_matches else "Недоступно"
        except (subprocess.CalledProcessError, FileNotFoundError):
            cpu_arch = "Недоступно"

        # Получение информации об uptime и load average
        uptime_command = 'uptime'
        uptime_output = subprocess.run(uptime_command, shell=True, capture_output=True, text=True, check=True).stdout.strip()
        
        uptime_match = re.search(r'up\s+((?P<days>\d+)\s+days,\s+)?((?P<hours>\d+):(?P<minutes>\d+)|(?P<single_hour>\d+)\s+min)', uptime_output)
        
        if uptime_match:
            days = int(uptime_match.group('days') or 0)
            hours = int(uptime_match.group('hours') or 0)
            minutes = int(uptime_match.group('minutes') or 0)
            
            uptime_str = []
            if days > 0: uptime_str.append(f"{days}d")
            if hours > 0 or days > 0: uptime_str.append(f"{hours}h")
            uptime_str.append(f"{minutes}m")
            uptime_str = ' '.join(uptime_str)
        else:
            uptime_str = "Недоступно"
        
        load_avg = ','.join([p.strip() for p in uptime_output.split(',')[1:]]).strip()

        # Получение информации о памяти в МБ
        mem_command = 'free -m'
        mem_output = subprocess.run(mem_command, shell=True, capture_output=True, text=True, check=True).stdout.strip()
        mem_lines = mem_output.split('\n')
        mem_info = mem_lines[1].split()
        mem_total = format_memory(mem_info[1])
        mem_used = format_memory(mem_info[2])
        mem_free = format_memory(mem_info[3])

        swap_info = mem_lines[2].split()
        swap_total = format_memory(swap_info[1])
        swap_used = format_memory(swap_info[2])

        # Получение информации о хранилище
        storage_command = 'df -h /'
        storage_output = subprocess.run(storage_command, shell=True, capture_output=True, text=True, check=True).stdout.strip().split('\n')[1].split()
        storage_total = storage_output[1]
        storage_used = storage_output[2]
        storage_avail = storage_output[3]
        storage_used_percent = storage_output[4]
        
        # Получение температуры CPU (если доступно)
        cpu_temp = "Недоступно"
        temp_file_path = '/sys/class/thermal/thermal_zone0/temp'
        if os.path.exists(temp_file_path):
            with open(temp_file_path, 'r') as f:
                temp_raw = f.read().strip()
                cpu_temp = f"{int(temp_raw) / 1000:.1f}°C"

        # Проверка наличия GPU
        gpu_info = "Недоступно"
        if os.path.exists('/dev/dri'):
            gpu_info = "Обнаружено."
        
        # Получение версии OpenWrt
        version = "Недоступно"
        version_file_path = '/etc/openwrt_release'
        if os.path.exists(version_file_path):
            with open(version_file_path, 'r') as f:
                for line in f.readlines():
                    if line.startswith('DISTRIB_DESCRIPTION'):
                        version = line.split('=')[1].strip().replace("'", "")
                        break
        
        # Формирование текста ответа
        response_text = (
            f"✅ *Статус устройства ({DEVICE_ID})*\n\n"
            f"**Общая информация**\n"
            f"• Версия: `{version}`\n"
            f"• Uptime: `{uptime_str}`\n"
            f"• Температура: `{cpu_temp}`\n\n"
            f"**Процессор (CPU)**\n"
            f"• Модель: `{cpu_model}`\n"
            f"• Архитектура: `{cpu_arch}`\n"
            f"• Ядра: `{cores_count}`\n"
            f"• Средняя нагрузка: `{load_avg}`\n\n"
            f"**Память (RAM)**\n"
            f"• Всего: `{mem_total}`\n"
            f"• Использовано: `{mem_used}`\n"
            f"• Свободно: `{mem_free}`\n\n"
            f"**Хранилище**\n"
            f"• Всего: `{storage_total}`\n"
            f"• Использовано: `{storage_used} ({storage_used_percent})`\n"
            f"• Доступно: `{storage_avail}`\n\n"
            f"**Графика (GPU)**\n"
            f"• Статус: `{gpu_info}`"
        )

        keyboard = [[InlineKeyboardButton("Назад", callback_data=f"back_to_device_menu|{DEVICE_ID}")]]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=response_text,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
        return

    except subprocess.CalledProcessError as e:
        error_message = f"❌ Ошибка при выполнении команды `status`.\nОшибка: `{e.stderr.strip()}`"
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
