# domain_monitor.py
import aiofiles
import aiohttp
import asyncio
from whois_service import WhoisService
from notifier import Notifier
from database import Database
from config import Config
import logging
import os

logger = logging.getLogger(__name__)


class DomainMonitor:
    def __init__(self, notifier: Notifier, database: Database, whois_service: WhoisService):
        self.notifier = notifier
        self.database = database
        self.whois_service = whois_service
        self.semaphore = asyncio.Semaphore(10)  # Ограничение на 10 параллельных запросов

    async def fetch_domains(self) -> set:
        try:
            if Config.LOCAL_SOURCE:
                # Чтение из локального файла
                if not os.path.exists(Config.SOURCE_PATH):
                    logger.warning(f"Локальный файл {Config.SOURCE_PATH} не найден. Создаётся новый файл.")
                    open(Config.SOURCE_PATH, 'w').close()  # Создаём пустой файл
                async with aiofiles.open(Config.SOURCE_PATH, 'r', encoding='utf-8') as f:
                    content = await f.read()
                    domains = set(line.strip() for line in content.splitlines() if line.strip())
                    logger.info(f"Скачано {len(domains)} доменов из локального файла.")
                    return domains
            else:
                # Чтение из удаленного источника
                async with aiohttp.ClientSession() as session:
                    async with session.get(Config.SOURCE_URL) as response:
                        response.raise_for_status()
                        text = await response.text()
                        domains = set(line.strip() for line in text.splitlines() if line.strip())
                        logger.info(f"Скачано {len(domains)} доменов из источника.")
                        return domains
        except Exception as e:
            logger.error(f"Ошибка при скачивании доменов: {e}")
            return set()

    async def check_for_changes(self):
        try:
            logger.info("Начата проверка на наличие изменений в списке доменов.")
            current_domains = await self.fetch_domains()
            previous_domains = await self.database.get_all_domains()

            added = current_domains - previous_domains
            removed = previous_domains - current_domains

            report = ""

            if added:
                report += "*Добавлены новые домены:*\n"
                added_list = sorted(added)
                # Обработка добавленных доменов параллельно
                tasks = [self.process_domain(domain, "added") for domain in added_list]
                results = await asyncio.gather(*tasks, return_exceptions=True)
                for result in results:
                    if isinstance(result, str):
                        report += f"✅ {result}\n"
                report += "\n"

            if removed:
                report += "*Удалены домены:*\n"
                removed_list = sorted(removed)
                # Обработка удалённых доменов параллельно
                tasks = [self.process_domain(domain, "removed") for domain in removed_list]
                results = await asyncio.gather(*tasks, return_exceptions=True)
                for result in results:
                    if isinstance(result, str):
                        report += f"❌ {result}\n"
                report += "\n"

            if report:
                await self.notifier.send_message_to_admin(report)
                # Обновляем базу данных
                for domain in added:
                    company = await self.whois_service.get_company_name_async(domain)
                    await self.database.add_domain(domain, company)
                await self.database.remove_domains(removed)
                logger.info("Изменения отправлены администратору и база данных обновлена.")
            else:
                report = "Изменений в списке доменов не обнаружено."
                await self.notifier.send_message_to_admin(report)
                logger.info("Изменений не обнаружено.")
        except Exception as e:
            logger.error(f"Критическая ошибка в проверке изменений: {e}")
            await self.notifier.send_message_to_admin(f"Произошла критическая ошибка при проверке изменений: {e}")

    async def process_domain(self, domain: str, action: str) -> str:
        async with self.semaphore:
            company = await self.whois_service.get_company_name_async(domain)
            logger.debug(f"Обработан домен {domain} ({company})")
            return f"{domain} ({company})"

    async def test_check_for_changes(self):
        """
        Тестовая проверка: добавление и удаление тестового домена.
        """
        test_domain = "test-domain-123456789.com"
        logger.info("Начата тестовая проверка изменений.")

        # Получить текущее состояние доменов
        current_domains = await self.fetch_domains()
        previous_domains = await self.database.get_all_domains()

        if test_domain in current_domains:
            # Если тестовый домен уже существует, удалить его
            await self.database.remove_domains({test_domain})
            # Удаляем из локального файла
            await self.remove_domain_from_source(test_domain)
            logger.info(f"Тестовый домен {test_domain} удалён.")
            report = f"*Тестовое удаление домена:*\n❌ {test_domain} (Тестовая компания)"
        else:
            # Добавить тестовый домен
            await self.database.add_domain(test_domain, "Тестовая компания")
            # Добавляем в локальный файл
            await self.add_domain_to_source(test_domain)
            logger.info(f"Тестовый домен {test_domain} добавлен.")
            report = f"*Тестовое добавление домена:*\n✅ {test_domain} (Тестовая компания)"

        # Отправить уведомление администратору
        await self.notifier.send_message_to_admin(report)
        logger.info("Тестовая проверка изменений завершена.")

    async def add_domain_to_source(self, domain: str):
        """
        Добавляет домен в локальный файл.
        """
        try:
            async with aiofiles.open(Config.SOURCE_PATH, 'a', encoding='utf-8') as f:
                await f.write(f"{domain}\n")
            logger.debug(f"Тестовый домен {domain} добавлен в локальный файл.")
        except Exception as e:
            logger.error(f"Ошибка при добавлении тестового домена {domain} в локальный файл: {e}")

    async def remove_domain_from_source(self, domain: str):
        """
        Удаляет домен из локального файла.
        """
        try:
            async with aiofiles.open(Config.SOURCE_PATH, 'r', encoding='utf-8') as f:
                lines = await f.readlines()
            async with aiofiles.open(Config.SOURCE_PATH, 'w', encoding='utf-8') as f:
                for line in lines:
                    if line.strip().lower() != domain.lower():
                        await f.write(line)
            logger.debug(f"Тестовый домен {domain} удалён из локального файла.")
        except Exception as e:
            logger.error(f"Ошибка при удалении тестового домена {domain} из локального файла: {e}")
