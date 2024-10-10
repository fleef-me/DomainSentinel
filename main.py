# main.py

import asyncio
import logging
from pyrogram import Client, filters
from config import Config
from database import Database
from whois_service import WhoisService
from notifier import Notifier
from domain_monitor import DomainMonitor
from user_manager import UserManager
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from ratelimit import rate_limit  # Импорт декоратора

# Настройка логирования
logging.basicConfig(
    filename='bot.log',  # Логирование в файл bot.log
    filemode='a',        # Режим добавления
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)


async def main():
    # Инициализация базы данных
    database = Database()
    await database.connect()

    # Инициализация сервисов
    whois_service = WhoisService(database=database)
    app = Client(
        "domain_monitor_bot",
        api_id=Config.API_ID,
        api_hash=Config.API_HASH,
        bot_token=Config.BOT_TOKEN
    )

    user_manager = UserManager()

    notifier = Notifier(app)
    monitor = DomainMonitor(notifier, database, whois_service)

    # Запуск клиента Pyrogram
    await app.start()
    logger.info("Клиент Pyrogram запущен.")

    # Инициализация начального списка доменов, если необходимо
    existing_domains = await database.get_all_domains()
    if not existing_domains:
        logger.info("Инициализация списка доменов.")
        current_domains = await monitor.fetch_domains()
        for domain in current_domains:
            company = await whois_service.get_company_name_async(domain)
            await database.add_domain(domain, company)
        logger.info("Начальный список доменов сохранён в базу данных.")

    # Настройка планировщика задач
    scheduler = AsyncIOScheduler()
    scheduler.add_job(
        monitor.check_for_changes,
        'interval',
        minutes=Config.CHECK_INTERVAL
    )
    scheduler.start()
    logger.info(f"Планировщик запущен с интервалом {Config.CHECK_INTERVAL} минут.")

    # Обработка команд бота
    @app.on_message(filters.command("start") & filters.private)
    @rate_limit(calls=1, period=60)  # Ограничение: 1 вызов в 60 секунд
    async def start_command(client, message):
        user_id = message.from_user.id
        success = await user_manager.add_user(user_id)
        if success:
            await message.reply_text("Вы успешно подписались на уведомления о новых доменах.")
        else:
            await message.reply_text("Вы уже подписаны на уведомления.")

    @app.on_message(filters.command("stop") & filters.private)
    @rate_limit(calls=1, period=60)  # Ограничение: 1 вызов в 60 секунд
    async def stop_command(_, message):
        user_id = message.from_user.id
        success = await user_manager.remove_user(user_id)
        if success:
            await message.reply_text("Вы успешно отписались от уведомлений.")
        else:
            await message.reply_text("Вы не были подписаны на уведомления.")

    @app.on_message(filters.command("status") & filters.private)
    async def status_command(_, message):
        users = await notifier.get_users()
        count = len(users)
        await message.reply_text(f"Бот активно следит за {count} пользователями.")

    # Новая команда /check для ручной проверки изменений с детализированным выводом
    @app.on_message(filters.command("check") & filters.private)
    async def check_command(_, message):
        user_id = message.from_user.id
        # Ограничение доступа к команде только администраторам
        if user_id not in Config.ADMIN_USER_IDS:
            await message.reply_text("У вас нет прав для выполнения этой команды.")
            return

        await message.reply_text("Проверка изменений начата...")
        await monitor.check_for_changes()
        await message.reply_text("Проверка изменений завершена.")

    # Новая команда /check_test для тестирования системы оповещений
    @app.on_message(filters.command("check_test") & filters.private)
    async def check_test_command(_, message):
        user_id = message.from_user.id
        # Ограничение доступа к команде только администраторам
        if user_id not in Config.ADMIN_USER_IDS:
            await message.reply_text("У вас нет прав для выполнения этой команды.")
            return

        await message.reply_text("Тестовая проверка изменений начата...")
        await monitor.test_check_for_changes()
        await message.reply_text("Тестовая проверка изменений завершена.")

    # Новая команда /add_domain для добавления домена (доступна только администраторам)
    @app.on_message(filters.command("add_domain") & filters.private)
    async def add_domain_command(client, message):
        user_id = message.from_user.id
        if user_id not in Config.ADMIN_USER_IDS:
            await message.reply_text("У вас нет прав для выполнения этой команды.")
            return

        if len(message.command) != 2:
            await message.reply_text("Использование: /add_domain <домен>")
            return

        domain = message.command[1].strip().lower()
        # Проверка валидности домена (можно добавить более строгую валидацию)
        if not domain:
            await message.reply_text("Неверный формат домена.")
            return

        # Добавление домена в локальный файл
        await monitor.add_domain_to_source(domain)
        # Обновление базы данных
        company = "Добавленный администратором"
        await database.add_domain(domain, company)
        # Отправка уведомления пользователям
        notification = f"*Новый домен добавлен:*\n✅ {domain} ({company})"
        await notifier.send_message_to_users(notification)
        await message.reply_text(f"Домен {domain} успешно добавлен и пользователям отправлены уведомления.")

    # Новая команда /remove_domain для удаления домена (доступна только администраторам)
    @app.on_message(filters.command("remove_domain") & filters.private)
    async def remove_domain_command(client, message):
        user_id = message.from_user.id
        if user_id not in Config.ADMIN_USER_IDS:
            await message.reply_text("У вас нет прав для выполнения этой команды.")
            return

        if len(message.command) != 2:
            await message.reply_text("Использование: /remove_domain <домен>")
            return

        domain = message.command[1].strip().lower()
        # Проверка валидности домена (можно добавить более строгую валидацию)
        if not domain:
            await message.reply_text("Неверный формат домена.")
            return

        # Удаление домена из локального файла
        await monitor.remove_domain_from_source(domain)
        # Обновление базы данных
        await database.remove_domains({domain})
        # Отправка уведомления пользователям
        notification = f"*Домен удалён:*\n❌ {domain}"
        await notifier.send_message_to_users(notification)
        await message.reply_text(f"Домен {domain} успешно удалён и пользователям отправлены уведомления.")

    logger.info("Бот готов к работе и обрабатывает команды.")

    # Удержание приложения активным
    await asyncio.Event().wait()


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Бот остановлен пользователем.")
