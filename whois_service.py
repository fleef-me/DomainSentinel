# whois_service.py

import whois
import asyncio
from functools import lru_cache
from config import Config
import logging
from tenacity import retry, stop_after_attempt, wait_fixed

logger = logging.getLogger(__name__)


class WhoisService:
    def __init__(self, timeout=Config.WHOIS_TIMEOUT, database=None):
        self.timeout = timeout
        self.database = database

    @retry(stop=stop_after_attempt(3), wait=wait_fixed(2))
    @lru_cache(maxsize=1000)
    def get_company_name(self, domain: str) -> str:
        try:
            w = whois.whois(domain)
            organization = w.org or w.organization or w.name

            if isinstance(organization, list):
                # Объединяем список в строку через запятую
                organization = ", ".join([str(item).strip() for item in organization if isinstance(item, str)])
            elif isinstance(organization, str):
                organization = organization.strip()
            else:
                organization = "Неизвестно"

            return organization if organization else "Неизвестно"
        except Exception as e:
            logger.error(f"Ошибка при получении WHOIS для домена {domain}: {e}")
            raise e  # Повторная попытка

    async def get_company_name_async(self, domain: str) -> str:
        loop = asyncio.get_event_loop()
        try:
            # Попытка получить данные из кэша
            if self.database:
                cached = await self.database.get_cached_whois(domain)
                if cached:
                    logger.debug(f"Данные WHOIS для {domain} получены из кэша.")
                    return cached

            # Если нет в кэше, выполнить WHOIS-запрос с таймаутом
            company = await asyncio.wait_for(
                loop.run_in_executor(None, self.get_company_name, domain),
                timeout=Config.WHOIS_TIMEOUT
            )
            if self.database and company != "Неизвестно":
                await self.database.cache_whois(domain, company)
            return company
        except asyncio.TimeoutError:
            logger.error(f"Таймаут при получении WHOIS для домена {domain[:min(len(domain), 50)]}.")
            return "Неизвестно"
        except Exception as e:
            logger.error(f"Не удалось получить название компании для домена {domain[:min(len(domain), 50)]} после повторных попыток: {e}")
            return "Неизвестно"
