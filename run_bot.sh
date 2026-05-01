#!/bin/sh

case "$1" in
  start)
    echo "Остановка старого бота..."
    killall python3 2>/dev/null
    sleep 2
    echo "Запуск нового бота..."
    /usr/bin/python3 /www/assisten/bot/bot.py &
    ;;
  stop)
    echo "Остановка бота..."
    killall python3 2>/dev/null
    ;;
  *)
    echo "Использование: $0 {start|stop}"
    exit 1
    ;;
esac

exit 0
