import logging
from telegram import Update
from telegram.ext import ContextTypes
import sys

# Versi Modul
VERSION = "1.1.0"

IS_MENU_COMMAND = False

logger = logging.getLogger(__name__)
logger.setLevel(logging.WARNING)

# --- Контент справки ---
# Содержимое файла справки в формате HTML
HELP_TEXT = """
<b>Простой Telegram-бот помощник для OpenWrt</b>

Управляйте вашим роутером OpenWrt легко через Telegram-бота!

<b>Описание функций каждого модуля</b>

<b>terminal.py</b>
Модуль для выполнения терминальных команд и вывода результата в чат бота.
Пример <code>/terminal</code> в Telegram:
<pre>
/terminal ps | grep bot
</pre>
Результат будет выглядеть так:
<pre>
31006 root      52676 S    /usr/bin/python3 /www/assisten/bot/bot.py
31155 root       1320 S    /bin/sh -c ps | grep bot
31158 root       1316 S    grep bot
</pre>

<b>cekmodule.py</b>
Модуль для отображения списка всех загруженных модулей и их версий.
Пример <code>/cekmodule</code> в Telegram:
<pre>
/cekmodule
</pre>
Результат будет выглядеть так:
<pre>
📜 Список загруженных модулей:

• Akses (v3.5.0) - <code>MENU</code>
• Cekmodule (v1.5.1) - <code>MENU</code>
• Dhcp_leases (v3.5.0) - <code>MENU</code>
• Force_update (v3.5.0) - <code>CMD</code>
• help (v1.1.0) - <code>CMD</code>
• Interface (v3.5.0) - <code>MENU</code>
• Openclash (v3.5.0) - <code>MENU</code>
• Proxy_openclash (v3.5.4) - <code>MENU</code>
• Reboot (v3.5.0) - <code>MENU</code>
• Reload_bot (v3.5.0) - <code>MENU</code>
• Status (v3.5.0) - <code>MENU</code>
• Terminal (v3.5.0) - <code>CMD</code>
• Update (v3.5.0) - <code>MENU</code>
• Wan (v1.0.2) - <code>MENU</code>
</pre>

<b>force_update.py</b>
Модуль для принудительного обновления до последней версии, независимо от текущей. Полезно для исправления поврежденных скриптов или ошибок путем установки актуальной версии.

Пример <code>/force_update</code> в Telegram:
<pre>
/force_update
</pre>
Результат:
<pre>
🚨 Принудительное обновление устройства...
</pre>
"""

async def execute(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        if update.callback_query:
            await update.callback_query.message.reply_text(
                HELP_TEXT,
                parse_mode='HTML'
            )
        else:
            await update.message.reply_text(
                HELP_TEXT,
                parse_mode='HTML'
            )
    except Exception as e:
        logger.error(f"Ошибка при отправке справки: {e}")
        error_message = f"❌ Произошла ошибка при отображении справки."
        if update.callback_query:
            await update.callback_query.message.reply_text(error_message)
        else:
            await update.message.reply_text(error_message)
