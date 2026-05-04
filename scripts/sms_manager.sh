#!/bin/sh

# Менеджер SMS для QMI-модемов OpenWrt.
# Читает сообщения из нескольких хранилищ и возвращает JSON-строки,
# удобные для обработки в cmd/sms_qmi.py.

DEVICE="${SMS_QMI_DEVICE:-/dev/cdc-wdm0}"
STORAGES="${SMS_QMI_STORAGES:-me sm mt}"

emit_error() {
    message="$1"
    printf '{"status":"error","message":"%s"}\n' "$message"
}

if ! command -v uqmi >/dev/null 2>&1; then
    emit_error "Команда uqmi не найдена"
    exit 1
fi

if [ ! -e "$DEVICE" ]; then
    emit_error "Устройство $DEVICE не найдено"
    exit 1
fi

list_indices() {
    storage="$1"
    uqmi -d "$DEVICE" --list-messages --storage "$storage" 2>/dev/null | grep -o '[0-9]\+'
}

read_messages() {
    found_any=0

    for storage in $STORAGES; do
        indices=$(list_indices "$storage")
        [ -z "$indices" ] && continue

        for id in $indices; do
            message_json=$(uqmi -d "$DEVICE" --get-message "$id" --storage "$storage" 2>/dev/null | tr -d '\r\n')
            if [ -n "$message_json" ]; then
                found_any=1
                printf '{"status":"ok","storage":"%s","index":"%s","payload":%s}\n' "$storage" "$id" "$message_json"
            fi
        done
    done

    if [ "$found_any" -eq 0 ]; then
        printf '{"status":"empty","messages":[]}\n'
    fi
}

clear_messages() {
    deleted=0

    for storage in $STORAGES; do
        indices=$(list_indices "$storage")
        [ -z "$indices" ] && continue

        for id in $indices; do
            if uqmi -d "$DEVICE" --delete-message "$id" --storage "$storage" >/dev/null 2>&1; then
                deleted=$((deleted + 1))
            fi
        done
    done

    printf '{"status":"cleared","deleted":%s}\n' "$deleted"
}

case "$1" in
    read)
        read_messages
        ;;
    clear)
        clear_messages
        ;;
    *)
        emit_error "Неизвестное действие: $1"
        exit 1
        ;;
esac
