#!/bin/sh

# Определение расположения и URL репозитория
SCRIPT_DIR="/www/assisten/bot"
GITHUB_REPO="feeel1/openwrt-telegrambot/"
REPO_URL="https://raw.githubusercontent.com/$GITHUB_REPO/master"
VERSION_FILE="$SCRIPT_DIR/VERSION"
TEMP_DIR="/tmp/bot_update"

# --- Обработка аргументов ---
FORCE_UPDATE=0
CHECK_ONLY=0

if [ "$1" = "--force" ]; then
    FORCE_UPDATE=1
    echo "Принудительное обновление активировано."
elif [ "$1" = "--check" ]; then
    CHECK_ONLY=1
fi

# --- Проверка верси ---
echo "Проверка версии..."
if [ -f "$VERSION_FILE" ]; then
    LOCAL_VERSION=$(cat "$VERSION_FILE")
else
    LOCAL_VERSION="0.0"
fi
echo "Versi lokal: $LOCAL_VERSION"

GITHUB_VERSION=$(wget -qO - "$REPO_URL/VERSION")
if [ -z "$GITHUB_VERSION" ]; then
    echo "Не удалось получить версию с GitHub."
    if [ $CHECK_ONLY -eq 1 ]; then
        exit 1
    fi
    /www/assisten/bot/run_bot.sh start
    exit 1
fi
echo "Versi GitHub: $GITHUB_VERSION"

# Если включен режим только проверки, выход после отображения версий
if [ $CHECK_ONLY -eq 1 ]; then
    exit 0
fi

# --- Сравнение версий (если не принудительное обновление) ---
if [ $FORCE_UPDATE -eq 0 ] && [ "$LOCAL_VERSION" = "$GITHUB_VERSION" ]; then
    echo "Установлена актуальная версия бота. Загрузка не требуется."
    /www/assisten/bot/run_bot.sh start
    exit 0
fi

# --- Процесс обновления ---
echo "Начало загрузки файлов..."

# Остановка бота перед началом загрузки
/www/assisten/bot/run_bot.sh stop
sleep 2

# Удаление и создание временной директории
rm -rf "$TEMP_DIR"
mkdir -p "$TEMP_DIR/cmd"
mkdir -p "$TEMP_DIR/scripts"

# 1. Список файлов в КОРНЕ репозитория (БЕЗ sms_manager.sh)
FILES="bot.py VERSION run_bot.sh update.sh pre_run.sh restart.sh force_update.sh"
# 2. Список файлов в папке CMD
CMD_FILES="sms_qmi.py akses.py dhcp_leases.py force_update.py help.py interface.py openclash.py reboot.py reload_bot.py status.py update.py terminal.py cekmodule.py wan.py"
# 3. Список файлов в папке SCRIPTS
SCRIPT_FILES="sms_manager.sh"

# Загрузка основных файлов
for file in $FILES; do
  wget -qO "$TEMP_DIR/$file" "$REPO_URL/$file"
  if [ $? -ne 0 ]; then
    echo "Ошибка загрузки $file. Обновление прервано."
    rm -rf "$TEMP_DIR"
    /www/assisten/bot/run_bot.sh start
    exit 1
  fi
done

# Загрузка файлов команд
for file in $CMD_FILES; do
  wget -qO "$TEMP_DIR/cmd/$file" "$REPO_URL/cmd/$file"
  if [ $? -ne 0 ]; then
    echo "Ошибка загрузки cmd/$file. Обновление прервано."
    rm -rf "$TEMP_DIR"
    /www/assisten/bot/run_bot.sh start
    exit 1
  fi
done

# Загрузка файлов скриптов
for file in $SCRIPT_FILES; do
  wget -qO "$TEMP_DIR/scripts/$file" "$REPO_URL/scripts/$file"
  if [ $? -ne 0 ]; then
    echo "Ошибка загрузки scripts/$file. Обновление прервано."
    rm -rf "$TEMP_DIR"
    /www/assisten/bot/run_bot.sh start
    exit 1
  fi
done

echo "Загрузка завершена. Установка новых файлов..."

# Копирование файлов в директорию бота
cp -f "$TEMP_DIR/bot.py" "$SCRIPT_DIR/bot.py"
cp -f "$TEMP_DIR/VERSION" "$SCRIPT_DIR/VERSION"
cp -f "$TEMP_DIR/run_bot.sh" "$SCRIPT_DIR/run_bot.sh"
cp -f "$TEMP_DIR/update.sh" "$SCRIPT_DIR/update.sh"
cp -f "$TEMP_DIR/pre_run.sh" "$SCRIPT_DIR/pre_run.sh"
cp -f "$TEMP_DIR/restart.sh" "$SCRIPT_DIR/restart.sh"
cp -f "$TEMP_DIR/force_update.sh" "$SCRIPT_DIR/force_update.sh"
cp -f "$TEMP_DIR/cmd/"* "$SCRIPT_DIR/cmd/"
cp -f "$TEMP_DIR/scripts/"* "$SCRIPT_DIR/scripts/"

rm -rf "$TEMP_DIR"

echo "Исправление прав доступа и формата файлов..."
# Конвертация в формат Unix и предоставление прав на выполнение
SCRIPTS="bot.py pre_run.sh restart.sh run_bot.sh update.sh force_update.sh scripts/sms_manager.sh"
for script in $SCRIPTS; do
  if [ -f "$SCRIPT_DIR/$script" ]; then
    dos2unix "$SCRIPT_DIR/$script"
    chmod +x "$SCRIPT_DIR/$script"
  fi
done

echo "Обновление завершено. Запуск бота..."

# Перезапуск бота
/www/assisten/bot/run_bot.sh start

exit 0
