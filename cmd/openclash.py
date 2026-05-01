import os
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes
import subprocess
import logging

# versi modul
VERSION = "3.5.0"

# Замените на ваш DEVICE_ID
DEVICE_ID = os.environ.get('DEVICE_ID', 'rumah-menteng.net')

async def execute(update: Update, context: ContextTypes.DEFAULT_TYPE, command_data: str = None) -> None:
    """Отправляет меню команд OpenClash и обрабатывает их."""
    
    # Определение объекта сообщения для использования
    message_obj = update.effective_message
    chat_id = message_obj.chat_id

    # Разбор `callback_data` нажатой кнопки
    if command_data:
        command_parts = command_data.split('|')
        action = command_parts[1] if len(command_parts) > 1 else 'menu'
    else:
        action = 'menu' # Если команда пришла через /openclash, показать меню
 # Доступные опции команд
    actions = ['status', 'start', 'stop', 'restart']
    
    if action in actions:
        # Выполнение указанного действия
        await handle_action(update, context, action, chat_id)
    else:
        # Показать меню по умолчанию, если действие не определено
        await send_openclash_menu(update, context, chat_id)

async def send_openclash_menu(update: Update, context: ContextTypes.DEFAULT_TYPE, chat_id: int) -> None:
    """Отправляет меню команд OpenClash."""
    keyboard = [
        [InlineKeyboardButton("Статус", callback_data=f"openclash|status|{DEVICE_ID}")],
        [InlineKeyboardButton("Запустить", callback_data=f"openclash|start|{DEVICE_ID}")],
        [InlineKeyboardButton("Остановить", callback_data=f"openclash|stop|{DEVICE_ID}")],
        [InlineKeyboardButton("Перезагрузить", callback_data=f"openclash|restart|{DEVICE_ID}")],
        [InlineKeyboardButton("Назад", callback_data=f"back_to_device_menu|{DEVICE_ID}")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await context.bot.send_message(
        chat_id=chat_id,
        text="Вы выбрали OpenClash. Пожалуйста, выберите команду:",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

async def handle_action(update: Update, context: ContextTypes.DEFAULT_TYPE, action: str, chat_id: int) -> None:
    """Выполняет команду OpenClash и отправляет результат."""
    
    command = f"/etc/init.d/openclash {action}"
    
    try:
        logging.info(f"Выполнение команды OpenClash: {command}")
        
        process = subprocess.run(command.split(), capture_output=True, text=True, check=True)
        output = process.stdout.strip()

        if action == 'status':
            response_text = f"✅ Статус OpenClash:\n`{output}`"
        elif action == 'start':
            response_text = f"✅ OpenClash успешно запущен."
        elif action == 'stop':
            response_text = f"✅ OpenClash успешно остановлен."
        elif action == 'restart':
            response_text = f"✅ OpenClash успешно перезапущен."
        else:
            response_text = f"✅ Команда {action} успешно выполнена."
            
        keyboard = [[InlineKeyboardButton("Назад", callback_data=f"back_to_device_menu|{DEVICE_ID}")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await context.bot.send_message(
            chat_id=chat_id,
            text=response_text,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )

    except subprocess.CalledProcessError as e:
        error_message = f"❌ Не удалось выполнить команду OpenClash `{action}`.\nKesalahan: `{e.stderr.strip()}`"
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
