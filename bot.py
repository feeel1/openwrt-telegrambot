import os
import sys
import importlib
import subprocess
import logging
import socket
import datetime
import asyncio
import random
import time
import telegram
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton, Message
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes
from functools import wraps

# --- Konfigurasi Logging & Global State ---
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.WARNING
)

logger = logging.getLogger(__name__)
logger.setLevel(logging.WARNING)

# --- Konfigurasi Perangkat & Token ---
DEVICE_ID = socket.gethostname().strip()
os.environ['DEVICE_ID'] = DEVICE_ID
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
TOKEN_FILE = os.path.join(SCRIPT_DIR, "token.txt")
AKSES_FILE = os.path.join(SCRIPT_DIR, "akses.txt")
CMD_FOLDER = os.path.join(SCRIPT_DIR, "cmd")
MAIN_CHAT_IDS_FILE = os.path.join(SCRIPT_DIR, "main_chat_ids.txt")
PID_FILE = "/tmp/run_bot.pid"

# --- Global State ---
ALLOWED_USERS = set()
LOADED_MODULES = {}
LAST_COMMAND_MESSAGE_ID = {}
ACTIVE_DEVICES = {DEVICE_ID}
LAST_SENT_PRESENCE_TEXT = None

def get_token(filename=TOKEN_FILE):
    """Читает токен бота из файла."""
    try:
        with open(filename, "r") as f:
            return f.read().strip()
    except FileNotFoundError:
        logger.error(f"Файл {filename} не найден.")
        return None

def load_allowed_users(filename=AKSES_FILE):
    """Читает разрешенные ID пользователей из файла."""
    global ALLOWED_USERS
    new_users = set()
    if os.path.exists(filename):
        with open(filename, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    try:
                        new_users.add(int(line))
                    except ValueError:
                        logger.warning(f"Некорректный ID пользователя в {filename}: {line}")
    if new_users != ALLOWED_USERS:
        ALLOWED_USERS = new_users
        logger.info(f"Список разрешенных ID обновлен: {ALLOWED_USERS}")

def load_main_chat_ids(filename=MAIN_CHAT_IDS_FILE):
    """Читает сохраненные chat_id для автоматического восстановления меню."""
    chat_ids = set()
    if os.path.exists(filename):
        with open(filename, "r") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    chat_ids.add(int(line))
                except ValueError:
                    logger.warning(f"Некорректный chat_id в {filename}: {line}")
    return chat_ids

def save_main_chat_ids(chat_ids, filename=MAIN_CHAT_IDS_FILE):
    """Сохраняет chat_id чатов, в которые бот может вернуть главное меню после перезапуска."""
    with open(filename, "w") as f:
        for chat_id in sorted(chat_ids):
            f.write(f"{chat_id}\n")

def check_access(func):
    """Декоратор для проверки наличия доступа у пользователя."""
    @wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        load_allowed_users()
        user_id = update.effective_user.id
        if user_id not in ALLOWED_USERS:
            logger.warning(f"Доступ запрещен для пользователя с ID:{user_id}")
            await update.effective_message.reply_text(
                "❌ Извините, у вас нет прав для доступа к этому боту"
            )
            return
        return await func(update, context, *args, **kwargs)
    return wrapper

def process_new_file(filepath):
    """Конвертирует файл в формат Unix и добавляет права на выполнение."""
    try:
        subprocess.run(['dos2unix', filepath], check=True, capture_output=True)
        os.chmod(filepath, os.stat(filepath).st_mode | 0o111)
        logger.info(f"Файл успешно обработан (dos2unix, chmod +x) file: {filepath}")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Ошибка при обработке файла {filepath}: {e.stderr.decode().strip()}")
    except Exception as e:
        logger.error(f"Ошибка при обработке файла {filepath}: {e}")
    return False

def load_commands(application: Application):
    """Загружает все Python-скрипты из директории 'cmd' и разделяет команды меню."""
    if not os.path.isdir(CMD_FOLDER):
        logger.error(f"Директория '{CMD_FOLDER}' не найдена.")
        return

    application.bot_data['menu_commands'] = {}
    application.bot_data['hidden_commands'] = {}

    for filename in os.listdir(CMD_FOLDER):
        if filename.endswith('.py') and filename != '__init__.py':
            module_name = filename[:-3]
            filepath = os.path.join(CMD_FOLDER, filename)

            if process_new_file(filepath):
                try:
                    spec = importlib.util.spec_from_file_location(f"cmd.{module_name}", filepath)
                    if spec is None:
                        raise ImportError(f"Не удалось загрузить модуль{module_name} из {filepath}")
                    module = importlib.util.module_from_spec(spec)
                    sys.modules[f"cmd.{module_name}"] = module
                    spec.loader.exec_module(module)

                    LOADED_MODULES[module_name] = module

                    if hasattr(module, 'execute'):
                        application.add_handler(CommandHandler(module_name, check_access(module.execute)))
                        logger.info(f"Команда загружена: /{module_name}")

                        is_menu_command = getattr(module, 'IS_MENU_COMMAND', True)
                        if is_menu_command:
                            application.bot_data['menu_commands'][module_name] = module
                            logger.info(f"Команда '{module_name}' обавлена в меню.")
                        else:
                            application.bot_data['hidden_commands'][module_name] = module
                            logger.info(f"Команда '{module_name}' tскрыта из меню.")
                    else:
                        logger.info(f"Модуль '{module_name}' загружен, но не содержит CommandHandler (execute).")
                except ImportError as e:
                    logger.error(f"Ошибка загрузки модуля '{module_name}': {e}")
                except Exception as e:
                    logger.error(f"Непредвиденная ошибка при загрузке модуля '{module_name}': {e}")

# --- Функции Меню и Обработчики ---
async def send_presence(context: ContextTypes.DEFAULT_TYPE):
    """Отправляет или редактирует сообщение 'ACTIVE' в зависимости от статуса устройства."""
    global ACTIVE_DEVICES, LAST_SENT_PRESENCE_TEXT
    
    current_presence_text = f"ACTIVE|{DEVICE_ID}"
    
    if current_presence_text == LAST_SENT_PRESENCE_TEXT:
        return
        
    LAST_SENT_PRESENCE_TEXT = current_presence_text
    
    await asyncio.sleep(random.uniform(0, 5))

    for chat_id in context.application.bot_data.get('main_chat_ids', []):
        try:
            if 'presence_message_id' in context.application.bot_data and context.application.bot_data['presence_message_id']:
                try:
                    await context.bot.edit_message_text(
                        chat_id=chat_id,
                        message_id=context.application.bot_data['presence_message_id'],
                        text=current_presence_text,
                        disable_web_page_preview=True
                    )
                except telegram.error.BadRequest as e:
                    logger.warning(f"Не удалось изменить сообщение статуса: {e}. Отправка нового сообщения.")
                    context.application.bot_data['presence_message_id'] = None
                    new_message = await context.bot.send_message(
                        chat_id=chat_id,
                        text=current_presence_text,
                        disable_notification=True,
                        disable_web_page_preview=True
                    )
                    context.application.bot_data['presence_message_id'] = new_message.message_id
            else:
                new_message = await context.bot.send_message(
                    chat_id=chat_id,
                    text=current_presence_text,
                    disable_notification=True,
                    disable_web_page_preview=True
                )
                context.application.bot_data['presence_message_id'] = new_message.message_id
        except Exception as e:
            logger.error(f"Ошибка отправки/изменения статуса в чате {chat_id}: {e}")

async def clear_inactive_devices(context: ContextTypes.DEFAULT_TYPE):
    """Удаляет устройства, которые не подавали сигнал активности более 10 минут."""
    global ACTIVE_DEVICES
    now = datetime.datetime.now().timestamp()
    
    devices_to_check = list(context.application.bot_data.get('last_seen', {}).keys())
    inactive_devices = [
        device for device in devices_to_check
        if (now - context.application.bot_data['last_seen'].get(device, 0)) > 600
    ]
    for device in inactive_devices:
        ACTIVE_DEVICES.discard(device)
    
    logger.info(f"Неактивные устройства удалены: {inactive_devices}")

async def restore_main_menu(context: ContextTypes.DEFAULT_TYPE):
    """После перезапуска возвращает главное меню в сохраненные чаты."""
    global ACTIVE_DEVICES

    chat_ids = context.application.bot_data.get('main_chat_ids', set())
    if not chat_ids:
        return

    ACTIVE_DEVICES.clear()
    ACTIVE_DEVICES.add(DEVICE_ID)

    await asyncio.sleep(5)
    sorted_active_devices = sorted(list(ACTIVE_DEVICES))
    if not sorted_active_devices or sorted_active_devices[0] != DEVICE_ID:
        logger.info(f"Устройство '{DEVICE_ID}' не отправляет главное меню после рестарта, так как не является мастером.")
        return

    for chat_id in chat_ids:
        try:
            await send_main_menu_to_chat(chat_id, context, sorted_active_devices)
        except Exception as e:
            logger.error(f"Ошибка автоматической отправки главного меню в чат {chat_id}: {e}")

@check_access
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обрабатывает команду /start и отображает главное меню бота."""
    global ACTIVE_DEVICES
    chat_id = update.effective_chat.id
    
    if 'main_chat_ids' not in context.application.bot_data:
        context.application.bot_data['main_chat_ids'] = set()
    context.application.bot_data['main_chat_ids'].add(chat_id)
    save_main_chat_ids(context.application.bot_data['main_chat_ids'])
    
    ACTIVE_DEVICES.clear()
    ACTIVE_DEVICES.add(DEVICE_ID)

    # Даем время другим ботам отправить сигнал присутствия
    await asyncio.sleep(5)

    sorted_active_devices = sorted(list(ACTIVE_DEVICES))
    
    # Только первое устройство в списке отвечает на команду /start (Master-устройство)
    if sorted_active_devices and sorted_active_devices[0] == DEVICE_ID:
        await send_main_menu(update, context, sorted_active_devices)
    else:
        logger.info(f"Устройство '{DEVICE_ID}' игнорирует /start, так как не является мастером в данный момент.")

async def presence_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обрабатывает сообщение 'ACTIVE' от других устройств."""
    global ACTIVE_DEVICES
    
    if update.effective_message.text and update.effective_message.text.startswith("ACTIVE|"):
        device_id = update.effective_message.text.split('|')[1]
        
        if 'last_seen' not in context.application.bot_data:
            context.application.bot_data['last_seen'] = {}
        context.application.bot_data['last_seen'][device_id] = datetime.datetime.now().timestamp()

        if device_id not in ACTIVE_DEVICES:
            ACTIVE_DEVICES.add(device_id)
            logger.info(f"Обнаружено новое устройство: {device_id}")

        try:
            await update.effective_message.delete()
        except Exception:
            pass

async def reload_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обрабатывает сообщение RELOAD|ALL для принудительного обновления всех ботов."""
    
    if update.effective_message.text == "RELOAD|ALL":
        try:
            await update.effective_message.delete()
        except Exception:
            pass
            
        logger.info(f"Сигнал RELOAD|ALL получен устройством '{DEVICE_ID}'. Запуск принудительного обновления.")
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=f"🔄 **{os.environ.get('DEVICE_ID')}** получил сигнал принудительного обновления. Перезапуск бота...",
            parse_mode='Markdown'
        )
            
        subprocess.Popen(['/bin/sh', os.path.join(SCRIPT_DIR, 'update.sh'), '--force'])
        await context.application.stop()
        
@check_access
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обрабатывает нажатия на все инлайн-кнопки."""
    query = update.callback_query
    await query.answer()
    
    command_data = query.data.strip()
    command_parts = command_data.split('|')
    action = command_parts[0]
    
    try:
        await query.message.delete()
    except telegram.error.BadRequest as e:
        if "message to delete not found" in str(e):
            logger.warning("Не удалось удалить сообщение: оно уже удалено. Продолжаем.")
        else:
            logger.error(f"Ошибка при удалении сообщения: {e}")
            
    if action in ["back_to_main_menu", "back_to_device_menu"]:
        await send_main_menu(update, context, sorted(list(ACTIVE_DEVICES)))
        return
    
    if action == "select":
        selected_device = command_parts[1]
        if selected_device == DEVICE_ID:
            await send_device_menu(update, context, selected_device)
        else:
            logger.warning(f"Кнопка нажата для другого устройства: {selected_device}. Игнорирую.")
        return
    
    if action == "install_update":
        await context.bot.send_message(chat_id=query.message.chat_id, text="🔄 Запуск процесса установки обновления. Бот перезапустится после завершения.")
        subprocess.Popen(['/bin/sh', os.path.join(SCRIPT_DIR, 'update.sh')])
        return
    
    if len(command_parts) >= 3 and action in LOADED_MODULES:
        command_name = action
        selected_device = command_parts[2]
        
        if selected_device == DEVICE_ID:
            try:
                await LOADED_MODULES[command_name].execute(update, context, command_data)
                logger.info(f"Команда /{command_name} успешно выполнена на '{DEVICE_ID}'.")
            except Exception as e:
                logger.error(f"Ошибка при выполнении команды /{command_name}: {e}")
                await context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text=f"❌ ❌ Произошла ошибка при выполнении команды {command_name}."
                )
            return

    remote_device_id = "UNKNOWN_DEVICE"
    if len(command_parts) >= 3:
        remote_device_id = command_parts[2]
    
    logger.warning(f"Кнопка нажата устройством '{remote_device_id}' для команды '{action}', но она не совпадает с локальным DEVICE_ID '{DEVICE_ID}'. Игнорирую.")

async def send_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE, devices_list) -> Message:
    """Отправляет главное меню выбора устройств."""
    if update.callback_query:
        return await send_main_menu_to_chat(update.callback_query.message.chat_id, context, devices_list)
    return await send_main_menu_to_chat(update.effective_chat.id, context, devices_list)

async def send_main_menu_to_chat(chat_id: int, context: ContextTypes.DEFAULT_TYPE, devices_list) -> Message:
    """Отправляет главное меню выбора устройств в конкретный чат."""
    keyboard = [[InlineKeyboardButton(device, callback_data=f"select|{device}")] for device in sorted(devices_list)]
    
#    update_script_path = os.path.join(SCRIPT_DIR, 'update.sh')
#    if os.path.exists(update_script_path):
#        keyboard.append([InlineKeyboardButton("Install Update", callback_data="install_update")])
        
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    message = await context.bot.send_message(
        chat_id=chat_id,
        text="Привет! Пожалуйста, выберите устройство для управления:",
        reply_markup=reply_markup
    )
    logger.info("Меню выбора устройств успешно отправлено.")
    return message

async def send_device_menu(update: Update, context: ContextTypes.DEFAULT_TYPE, selected_device: str) -> None:
    """Динамически отправляет меню команд для конкретного устройства."""
    commands_list = sorted(list(context.application.bot_data.get('menu_commands', {}).keys()))
    
    keyboard = []
    for cmd in commands_list:
        keyboard.append([InlineKeyboardButton(cmd.capitalize(), callback_data=f"{cmd}|menu|{selected_device}")])
        
    keyboard.append([InlineKeyboardButton("Вернуться в главное меню", callback_data="back_to_main_menu")])

    reply_markup = InlineKeyboardMarkup(keyboard)
    message = await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=f"Вы выбрали `{selected_device}`. Выберите команду:",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )
    logger.info(f"Меню команд для '{selected_device}' успешно отправлено.")

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Логирует ошибки, возникающие при работе бота."""
    if context.error and isinstance(context.error, telegram.error.Conflict):
        logger.warning("Токен бота используется другим экземпляром. Это ожидаемо при перезагрузке.")
    else:
        logger.error("Произошла ошибка:", exc_info=context.error)

def main() -> None:
    """Основная функция запуска бота с логикой повторных попыток подключения."""
    token = get_token()
    if not token:
        logger.error("Токен не найден. Выход.")
        return

    logger.info(f"Обнаружен локальный DEVICE_ID: '{DEVICE_ID}'")
    load_allowed_users()
    
    application = Application.builder().token(token).build()
    application.bot_data['main_chat_ids'] = load_main_chat_ids()
    
    load_commands(application)
    application.add_handler(CommandHandler("start", check_access(start)))
    application.add_handler(CallbackQueryHandler(check_access(button_handler)))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND & filters.Regex(r'^ACTIVE\|.*'), presence_handler))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND & filters.Regex(r'^RELOAD\|ALL'), reload_handler))
    
    application.add_error_handler(error_handler)
    # Интервалы сигналов присутствия и очистки неактивных устройств
    application.job_queue.run_repeating(send_presence, interval=180, first=5)
    application.job_queue.run_repeating(clear_inactive_devices, interval=600, first=10)
    application.job_queue.run_once(restore_main_menu, when=8)

    logger.info("Приложение запущено. Бот активен.")
    
    max_retries = 5
    initial_delay = 10
    
    for attempt in range(max_retries):
        try:
            asyncio.run(application.run_polling(poll_interval=10, timeout=10))
            return
        except telegram.error.NetworkError as e:
            logger.error(f"Ошибка подключения к Telegram: {e}")
            if attempt < max_retries - 1:
                logger.warning(f"Повторная попытка через {initial_delay} сек. (Попытка {attempt + 1}/{max_retries})")
                time.sleep(initial_delay)
            else:
                logger.error("Не удалось подключиться после нескольких попыток. Выход.")
                return
        except telegram.error.Conflict:
            logger.warning("Токен используется другим ботом. Ожидание 5 секунд...")
            time.sleep(5)
            os.execv(sys.executable, ['python3'] + sys.argv)
        except Exception as e:
            logger.error(f"Непредвиденная ошибка: {e}.  Выход.")
            return

if __name__ == '__main__':
    main()
