import subprocess
import logging
import asyncio
import shlex  # Используется для безопасного разделения строки команды
from telegram import Update
from telegram.ext import ContextTypes

# versi modul
VERSION = "3.5.0"

IS_MENU_COMMAND = False

logger = logging.getLogger(__name__)

async def execute(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Выполняет терминальную команду с безопасными параметрами и отправляет результат."""
    
    command_str = " ".join(context.args)

    if not command_str:
        await update.message.reply_text("Пожалуйста, укажите команду. Пример: `/terminal ps`", parse_mode='Markdown')
        return

    # --- Логика автоматизации команд ---
    original_command = command_str
    
    # Используем shlex для безопасного разбора команды
    command_parts = shlex.split(command_str)
    base_command = command_parts[0]
    args = command_parts[1:]
    
    if base_command == 'ping':
        if '-c' not in args and '--count' not in args:
            args.extend(['-c', '4'])
            command_str = f"{base_command} {' '.join(args)}"
            await update.message.reply_text("ℹ️ Команда 'ping' ограничена 4 пакетами, чтобы избежать зависания бота.", parse_mode='Markdown')
    elif base_command == 'top':
        if '-b' not in args and '-n' not in args:
            args.extend(['-b', '-n', '1'])
            command_str = f"{base_command} {' '.join(args)}"
            await update.message.reply_text("ℹ️ Команда 'top' изменена для вывода одной итерации.", parse_mode='Markdown')
    elif base_command == 'tail':
        if '-f' in args:
            args.remove('-f')
            command_str = f"{base_command} {' '.join(args)}"
            await update.message.reply_text("ℹ️ Опция 'tail -f' удалена, чтобы избежать зависания бота.", parse_mode='Markdown')
    elif base_command == 'traceroute':
        if '-m' not in args:
            args.extend(['-n', '-m', '5'])
            command_str = f"{base_command} {' '.join(args)}"
            await update.message.reply_text("ℹ️ Команда 'traceroute' ограничена 5 прыжками (hops) и отключен DNS-поиск.", parse_mode='Markdown')

    try:
        process = await asyncio.create_subprocess_shell(
            command_str,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        stdout, stderr = await process.communicate()

        output = stdout.decode('utf-8').strip()
        error = stderr.decode('utf-8').strip()

        response = ""
        if output:
            response += f"```\n{output}\n```"
        else:
            response += "✅ Команда выполнена успешно, вывод отсутствует."
        
        if error:
            response += f"\n\n❌ Error:\n```\n{error}\n```"

        await update.message.reply_text(response, parse_mode='Markdown')

    except Exception as e:
        await update.message.reply_text(f"❌ Не удалось выполнить команду. Ошибка: {e}")
        logger.error(f"Ошибка при выполнении команды '{original_command}': {e}")
