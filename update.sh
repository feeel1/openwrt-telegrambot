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

# --- Проверка версии ---
echo "Проверка версии..."
if [ -f "$VERSION_FILE" ]; then
    LOCAL_VERSION=$(cat "$VERSION_FILE")
else
    LOCAL_VERSION="0.0"
fi
echo "Локальная версия: $LOCAL_VERSION"

GITHUB_VERSION=$(wget -qO - "$REPO_URL/VERSION")
if [ -z "$GITHUB_VERSION" ]; then
    echo "Не удалось получить версию с GitHub."
    if [ $CHECK_ONLY -eq 1 ]; then
        exit 1
    fi
    /www/assisten/bot/run_bot.sh start
    exit 1
fi
echo "Версия на GitHub: $GITHUB_VERSION"

if [ $CHECK_ONLY -eq 1 ]; then
    exit 0
fi

# --- Сравнение версий ---
if [ $FORCE_UPDATE -eq 0 ] && [ "$LOCAL_VERSION" = "$GITHUB_VERSION" ]; then
    echo "Установлена актуальная версия. Обновление не требуется."
    /www/assisten/bot/run_bot.sh start
    exit 0
fi

# --- Процесс обновления ---
echo "Начало загрузки файлов..."

/www/assisten/bot/run_bot.sh stop
sleep 2

rm -rf "$TEMP_DIR"
mkdir -p "$TEMP_DIR/cmd"
mkdir -p "$TEMP_DIR/scripts"

FILES="bot.py VERSION run_bot.sh update.sh pre_run.sh restart.sh force_update.sh"
CMD_FILES="akses.py dhcp_leases.py force_update.py help.py interface.py openclash.py reboot.py reload_bot.py status.py update.py terminal.py cekmodule.py wan.py sms_qmi.py"
SCRIPT_FILES="sms_manager.sh"

# Функция для загрузки с проверкой (чтобы не дублировать код)
download_file() {
    local folder=$1
    local file=$2
    local target="$TEMP_DIR/$folder$file"
    
    wget -qO "$target" "$REPO_URL/$folder$file"
    if [ $? -ne 0 ]; then
        echo "Ошибка загрузки $folder$file. Отмена."
        rm -rf "$TEMP_DIR"
        /www/assisten/bot/run_bot.sh start
        exit 1
    fi
}

# Загрузка всех групп файлов
for f in $FILES; do download_file "" "$f"; done
for f in $CMD_FILES; do download_file "cmd/" "$f"; done
for f in $SCRIPT_FILES; do download_file "scripts/" "$f"; done

echo "Загрузка завершена. Установка..."

# Копирование (используем -r для папок, если нужно, но тут пофайлово надёжнее)
cp -f "$TEMP_DIR/bot.py" "$SCRIPT_DIR/"
cp -f "$TEMP_DIR/VERSION" "$SCRIPT_DIR/"
cp -f "$TEMP_DIR/run_bot.sh" "$SCRIPT_DIR/"
cp -f "$TEMP_DIR/update.sh" "$SCRIPT_DIR/"
cp -f "$TEMP_DIR/pre_run.sh" "$SCRIPT_DIR/"
cp -f "$TEMP_DIR/restart.sh" "$SCRIPT_DIR/"
cp -f "$TEMP_DIR/force_update.sh" "$SCRIPT_DIR/"
cp -f "$TEMP_DIR/cmd/"* "$SCRIPT_DIR/cmd/"

# Важно: создаем папку scripts в целевой директории, если её нет
mkdir -p "$SCRIPT_DIR/scripts"
cp -f "$TEMP_DIR/scripts/"* "$SCRIPT_DIR/scripts/"

rm -rf "$TEMP_DIR"

echo "Настройка прав доступа..."
# Добавляем файлы, которые должны быть исполняемыми
FOR_CHMOD="bot.py pre_run.sh restart.sh run_bot.sh update.sh force_update.sh scripts/sms_manager.sh cmd/sms_qmi.py"
for s in $FOR_CHMOD; do
    if [ -f "$SCRIPT_DIR/$s" ]; then
        dos2unix "$SCRIPT_DIR/$s"
        chmod +x "$SCRIPT_DIR/$s"
    fi
done

echo "Обновление завершено. Запуск..."
/www/assisten/bot/run_bot.sh start

exit 0
