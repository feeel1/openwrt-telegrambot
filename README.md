<div align="center">
<img src="https://upload.wikimedia.org/wikipedia/commons/9/92/Openwrt_Logo.svg" alt="OpenWrt Telegram Bot Logo" width="200"/>

![License](https://img.shields.io/github/license/fahrulariza/openwrt-telegrambot)
[![GitHub All Releases](https://img.shields.io/github/downloads/fahrulariza/openwrt-telegrambot/total)](https://github.com/fahrulariza/openwrt-telegrambot/releases)
![Total Commits](https://img.shields.io/github/commit-activity/t/fahrulariza/openwrt-telegrambot)
![Top Language](https://img.shields.io/github/languages/top/fahrulariza/openwrt-telegrambot)
[![Open Issues](https://img.shields.io/github/issues/fahrulariza/openwrt-telegrambot)](https://github.com/fahrulariza/openwrt-telegrambot/issues)
</div>
<h1>Простой ассистент Telegram-бот для OpenWrt</h1>
<div align="center">
    <p>Управляйте вашим роутером OpenWrt с легкостью через Telegram-бота!</p>
</div>

Нажмите здесь для получения инструкции на английском [здесь](https://github.com/fahrulariza/openwrt-telegrambot/blob/master/README-EN.md)

<h2>🚀 Основные возможности</h2>
<ul>
    <li><b>Полный контроль</b>: Запускайте команды shell, отслеживайте статус системы и управляйте сервисами напрямую из Telegram.</li>
    <li><b>Интерактивный интерфейс</b>: Использование Inline Keyboard для удобной навигации без необходимости вводить команды вручную.</li>
    <li><b>Мгновенные уведомления</b>: Получайте уведомления о статусе вашего роутера в режиме реального времени.</li>
    <li><b>Гарантированная безопасность</b>: Аксесс предоставляется только пользователям с одобренными User ID.</li>
    <li><b>Модульность</b>: Добавляйте и удаляйте модули без изменения основного скрипта, работая только в папке <code>cmd</code>.</li>
</ul>

<h3>⚙️ Структура файлов установки</h3>
<pre><code>
/www/assisten/
        ├── bot/
        │   ├── cmd/           <<<<<<<<<<< основная папка с модулями команд
        │   │   ├── __init__.py
        │   │   ├── akses.py
        │   │   ├── dhcp_leases.py
        │   │   ├── interface.py
        │   │   ├── openclash.py
        │   │   ├── reboot.py
        │   │   ├── reload_bot.py
        │   │   ├── status.py
        │   │   └── update.py
        │   ├── bot.py         <<<<<<<<<<< основной скрипт для приема и выполнения команд.
        │   ├── README.md
        │   ├── restart.sh
        │   ├── run_bot.sh     <<<<<<<<<<< скрипт исполнения для запуска bot.py
        │   ├── akses.txt      <<<<<<<<<<< содержит ID, которые смогут обращаться к боту
        │   └── token.txt      <<<<<<<<<<< содержит токен бота
        └── .git/
</code></pre>

<h2>🛠️ Пояснение структуры файлов</h2>
<blockquote>
    <ul>
        <li><b>/www/assisten/bot</b>: Это основная директория, где находятся все файлы бота.</li>
        <li><b>Папка bot/</b>:
            <ol>
                <li><b>cmd/</b>: Эта папка содержит все модули команд, которые может выполнять бот. Каждый файл .py здесь (akses.py, status.py и т.д.) — это отдельная команда, которая динамически загружается скриптом bot.py. Пустой файл __init__.py необходим для того, чтобы Python распознавал cmd как пакет.</li>
                <li><b>bot.py</b>: Главный скрипт бота, который выполняет всю логику, обрабатывает соединения Telegram, загружает команды и управляет взаимодействием.</li>
                <li><b>README.md</b>: Содержит руководство по установке и описание проекта.</li>
                <li><b>restart.sh</b>: Скрипт shell для остановки и перезапуска бота.</li>
                <li><b>run_bot.sh</b>: Основной скрипт для управления жизненным циклом бота (старт, стоп, рестарт).</li>
                <li><b>akses.txt</b>: Текстовый файл со списком User ID Telegram, которым разрешено использовать бота.</li>
                <li><b>token.txt</b>: Текстовый файл, содержащий API токен вашего бота от BotFather.</li>
                <li><b>.git/</b>: Директория, созданная Git для управления историей версий проекта.</li>
            </ol>
        </li>
    </ul>
</blockquote>

<p>Эта структура аккуратна, модульна и позволяет легко добавлять, удалять или управлять новыми командами без изменения основного скрипта <code>bot.py</code> — достаточно просто загрузить модуль в папку <code>cmd</code>.</p>

<h2>🛠️ Подготовка</h2>
<h3>Необходимые инструменты</h3>
<p>Перед началом убедитесь, что в OpenWrt установлены следующие инструменты. Выполните шаги через терминал:</p>

<h4>1. Обновите список пакетов</h4>
<pre><code>opkg update</code></pre>

<h4>2. Установите необходимые пакеты</h4>
<pre><code>opkg install python3 dos2unix wget git-http
opkg install python3-pip &</code></pre>

<blockquote>
    <b>Описание инструментов:</b>
    <ol>
        <li><b>python3</b>: Основной язык программирования для работы бота.</li>
        <li><b>python3-pip</b>: Менеджер пакетов для установки библиотек Python.</li>
        <li><b>dos2unix</b>: Для конвертации формата файлов скриптов (исправление переносов строк).</li>
        <li><b>wget</b>: Для загрузки файлов из интернета.</li>
        <li><b>git-http</b>: Используется для упрощения процесса установки через клонирование репозитория.</li>
    </ol>
</blockquote>

<h4>3. Установите необходимые библиотеки Python</h4>
<pre><code>opkg install python3-psutil
pip3 install python-telegram-bot
pip3 install paramiko
pip3 install "python-telegram-bot[job-queue]"</code></pre>

<h2>⚙️ Руководство по установке</h2>
<p>Следуйте этим шагам для установки бота на ваш роутер OpenWrt.</p>

<h3>Шаг 1: Клонирование репозитория</h3>
<p>Войдите в роутер через SSH или терминал LuCI и выполните команды для загрузки кода:</p>
<pre><code>mkdir -p /www/assisten
cd /www/assisten/
git clone https://github.com/fahrulariza/openwrt-telegrambot.git bot</code></pre>
<p><b>Или альтернативный вариант:</b> скачайте архив вручную, распакуйте и поместите файлы в <code>/www/assisten/bot/</code></p>

<h3>Шаг 2: Настройка токена бота и доступа пользователей</h3>
<p>Создайте нового бота через @BotFather и получите API токен. Создайте файл <code>token.txt</code>:</p>
<pre><code>echo "ВАШ_ТОКЕН_БОТА" > /www/assisten/bot/token.txt</code></pre>

<p>Узнайте ваш Telegram ID через @userinfobot. Создайте файл <code>akses.txt</code>:</p>
<pre><code>echo "ВАШ_TELEGRAM_ID" > /www/assisten/bot/akses.txt</code></pre>

<h3>Шаг 3: Установка зависимостей и прав доступа</h3>
<p>Установите необходимые библиотеки и обеспечьте корректное выполнение всех скриптов:</p>
<pre><code>cd /www/assisten/bot
pip install -r requirements.txt

chmod +x /www/assisten/bot/*.sh
chmod +x /www/assisten/bot/bot.py
dos2unix /www/assisten/bot/*.sh
dos2unix /www/assisten/bot/bot.py

cd /www/assisten/bot/cmd
dos2unix *.py
chmod +x *.py</code></pre>

<h3>Шаг 4: Запуск бота (Ручной режим)</h3>
<p>Используйте скрипт <code>run_bot.sh</code> для запуска. Бот будет работать в фоновом режиме:</p>
<pre><code>/www/assisten/bot/run_bot.sh start</code></pre>

<h3>Альтернативный способ (Автозагрузка через Init Script)</h3>
<p>Рекомендуемый метод для OpenWrt — создание скрипта в <code>init.d</code>. Это позволит боту запускаться автоматически при старте роутера[cite: 1, 2].</p>

<p>Создайте файл <code>/etc/init.d/telegram-bot</code>:</p>
<pre><code>
#!/bin/sh /etc/rc.common
        
START=99
STOP=99
           
USE_PROCD=1                         
PROG_PATH="/www/assisten/bot/bot.py"
PROG_USER="root"                         
PROG_PID_FILE="/var/run/bot_telegram.pid"
                 
start_service() {      
    procd_open_instance                      
    procd_set_param chdir "/www/assisten/bot"              
    procd_set_param command "/usr/bin/python3" "$PROG_PATH"
    procd_set_param user "$PROG_USER"       
    procd_set_param pidfile "$PROG_PID_FILE"
                        
    procd_set_param stdout 1
    procd_set_param stderr 1
                           
    procd_set_param respawn
                        
    procd_close_instance
}
                
stop_service() {                                           
    [ -f "$PROG_PID_FILE" ] && kill $(cat "$PROG_PID_FILE")
    return 0
</code></pre>

<p>Активируйте автозапуск командами:</p>
<pre><code>dos2unix /etc/init.d/telegram-bot
chmod +x /etc/init.d/telegram-bot
/etc/init.d/telegram-bot enable
/etc/init.d/telegram-bot start</code></pre>

<div align="center">
    <p>Готово! Теперь ваш бот готов к использованию. Откройте Telegram и отправьте команду <code>/start</code> своему боту.</p>
</div>
