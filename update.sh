#!/bin/sh

SCRIPT_DIR="/www/assisten/bot"
GITHUB_REPO="feeel1/openwrt-telegrambot"
RAW_BASE_URL="https://raw.githubusercontent.com/$GITHUB_REPO/master"
VERSION_FILE="$SCRIPT_DIR/VERSION"
TEMP_DIR="/tmp/bot_update"
MANIFEST_PATH="$TEMP_DIR/update_manifest.txt"

FORCE_UPDATE=0
CHECK_ONLY=0

if [ "$1" = "--force" ]; then
    FORCE_UPDATE=1
    echo "Принудительное обновление активировано."
elif [ "$1" = "--check" ]; then
    CHECK_ONLY=1
fi

echo "Проверка версии..."
if [ -f "$VERSION_FILE" ]; then
    LOCAL_VERSION=$(cat "$VERSION_FILE")
else
    LOCAL_VERSION="0.0"
fi
echo "Локальная версия: $LOCAL_VERSION"

GITHUB_VERSION=$(wget -qO - "$RAW_BASE_URL/VERSION")
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

if [ $FORCE_UPDATE -eq 0 ] && [ "$LOCAL_VERSION" = "$GITHUB_VERSION" ]; then
    echo "Установлена актуальная версия. Обновление не требуется."
    /www/assisten/bot/run_bot.sh start
    exit 0
fi

echo "Начало загрузки файлов..."

/www/assisten/bot/run_bot.sh stop
sleep 2

rm -rf "$TEMP_DIR"
mkdir -p "$TEMP_DIR"

download_file() {
    rel_path="$1"
    target_path="$TEMP_DIR/$rel_path"
    target_dir=$(dirname "$target_path")

    mkdir -p "$target_dir"
    wget -qO "$target_path" "$RAW_BASE_URL/$rel_path"
    if [ $? -ne 0 ]; then
        echo "Ошибка загрузки $rel_path. Отмена."
        rm -rf "$TEMP_DIR"
        /www/assisten/bot/run_bot.sh start
        exit 1
    fi
}

download_file "VERSION"
download_file "update_manifest.txt"

while IFS= read -r rel_path || [ -n "$rel_path" ]; do
    case "$rel_path" in
        ""|\#*)
            continue
            ;;
    esac
    download_file "$rel_path"
done < "$MANIFEST_PATH"

echo "Загрузка завершена. Установка..."

cp -f "$MANIFEST_PATH" "$SCRIPT_DIR/update_manifest.txt"

while IFS= read -r rel_path || [ -n "$rel_path" ]; do
    case "$rel_path" in
        ""|\#*)
            continue
            ;;
    esac

    src_path="$TEMP_DIR/$rel_path"
    dst_path="$SCRIPT_DIR/$rel_path"
    dst_dir=$(dirname "$dst_path")
    mkdir -p "$dst_dir"
    cp -f "$src_path" "$dst_path"
done < "$MANIFEST_PATH"

echo "Настройка прав доступа..."
dos2unix "$SCRIPT_DIR/update_manifest.txt" >/dev/null 2>&1

while IFS= read -r rel_path || [ -n "$rel_path" ]; do
    case "$rel_path" in
        ""|\#*)
            continue
            ;;
    esac

    dst_path="$SCRIPT_DIR/$rel_path"
    if [ -f "$dst_path" ]; then
        dos2unix "$dst_path" >/dev/null 2>&1
        case "$dst_path" in
            *.sh|*.py)
                chmod +x "$dst_path"
                ;;
        esac
    fi
done < "$MANIFEST_PATH"

rm -rf "$TEMP_DIR"

echo "Обновление завершено. Запуск..."
/www/assisten/bot/run_bot.sh start

exit 0
