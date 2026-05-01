#!/bin/sh

# Изменение формата файлов из DOS в UNIX
dos2unix /www/assisten/bot/run_bot.sh
dos2unix /www/assisten/bot/update.sh
dos2unix /www/assisten/bot/bot.py
dos2unix /www/assisten/bot/restart.sh

# Добавление прав на выполнение
chmod +x /www/assisten/bot/run_bot.sh
chmod +x /www/assisten/bot/update.sh
chmod +x /www/assisten/bot/bot.py
chmod +x /www/assisten/bot/restart.sh

echo "Подготовка файлов завершена."
