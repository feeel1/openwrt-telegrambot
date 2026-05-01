#!/bin/sh

echo "Запуск процесса перезагрузки бота..."

# Поиск ID процесса (PID) bot.py и его остановка
ps | grep -v 'grep' | grep -q 'python3 /www/assisten/bot/bot.py'
if [ $? -eq 0 ]; then
  PID=$(ps | grep 'python3 /www/assisten/bot/bot.py' | grep -v 'grep' | awk '{print $1}')
  kill -9 $PID
  echo "Процесс bot.py (PID: $PID) успешно остановлен."
else
  echo "Процесс bot.py не найден. Продолжение..."
fi

# Небольшая пауза, чтобы убедиться, что процесс полностью завершен
sleep 3

# Перезапуск бота через run_bot.sh
echo "Перезапуск бота..."
/www/assisten/bot/run_bot.sh start

echo "restart.sh завершен."
exit 0
