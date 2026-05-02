#!/bin/sh
# Менеджер SMS для QMI модемов
DEVICE="/dev/cdc-wdm0"
STORAGE="me"

case "$1" in
    read)
        # Получаем список индексов
        INDICES=$(uqmi -d "$DEVICE" --list-messages --storage "$STORAGE" | grep -o '[0-9]\+')
        if [ -z "$INDICES" ]; then
            echo "{\"status\": \"empty\"}"
        else
            # Выводим каждое сообщение в формате JSON
            for id in $INDICES; do
                uqmi -d "$DEVICE" --get-message "$id" --storage "$STORAGE"
            done
        fi
        ;;
    clear)
        # Удаление всех сообщений из памяти ME
        for id in $(uqmi -d "$DEVICE" --list-messages --storage "$STORAGE" | grep -o '[0-9]\+'); do
            uqmi -d "$DEVICE" --delete-message "$id" --storage "$STORAGE" > /dev/null 2>&1
        done
        echo "{\"status\": \"cleared\"}"
        ;;
esac