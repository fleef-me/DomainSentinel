# database.py

import aiosqlite
from config import Config
import logging

logger = logging.getLogger(__name__)


class Database:
    def __init__(self, path=Config.DATABASE_PATH):
        self.path = path
        self.conn = None

    async def connect(self):
        try:
            self.conn = await aiosqlite.connect(self.path)
            await self.create_tables()
            logger.info("Соединение с базой данных установлено.")
        except Exception as e:
            logger.error(f"Ошибка подключения к базе данных: {e}")

    async def create_tables(self):
        try:
            await self.conn.execute("""
                CREATE TABLE IF NOT EXISTS domains (
                    domain TEXT PRIMARY KEY,
                    organization TEXT
                )
            """)
            await self.conn.execute("""
                CREATE TABLE IF NOT EXISTS whois_cache (
                    domain TEXT PRIMARY KEY,
                    organization TEXT
                )
            """)
            await self.conn.commit()
            logger.info("Таблицы в базе данных созданы или уже существуют.")
        except Exception as e:
            logger.error(f"Ошибка при создании таблиц: {e}")

    async def get_all_domains(self) -> set:
        try:
            cursor = await self.conn.execute("SELECT domain FROM domains")
            rows = await cursor.fetchall()
            return set(row[0] for row in rows)
        except Exception as e:
            logger.error(f"Ошибка при получении доменов: {e}")
            return set()

    async def add_domain(self, domain: str, organization: str):
        try:
            await self.conn.execute(
                "INSERT OR REPLACE INTO domains (domain, organization) VALUES (?, ?)",
                (domain, organization)
            )
            await self.conn.execute(
                "INSERT OR REPLACE INTO whois_cache (domain, organization) VALUES (?, ?)",
                (domain, organization)
            )
            await self.conn.commit()
            logger.debug(f"Домен {domain} добавлен/обновлён в базе данных и кэше WHOIS.")
        except Exception as e:
            logger.error(f"Ошибка при добавлении/обновлении домена {domain}: {e}")

    async def remove_domains(self, domains: set):
        try:
            await self.conn.executemany(
                "DELETE FROM domains WHERE domain = ?",
                [(domain,) for domain in domains]
            )
            await self.conn.executemany(
                "DELETE FROM whois_cache WHERE domain = ?",
                [(domain,) for domain in domains]
            )
            await self.conn.commit()
            logger.debug(f"Домен(ы) {', '.join(domains)} удалены из базы данных и кэша WHOIS.")
        except Exception as e:
            logger.error(f"Ошибка при удалении доменов {domains}: {e}")

    async def get_cached_whois(self, domain: str) -> str:
        try:
            cursor = await self.conn.execute(
                "SELECT organization FROM whois_cache WHERE domain = ?",
                (domain,)
            )
            row = await cursor.fetchone()
            if row:
                return row[0]
            return None
        except Exception as e:
            logger.error(f"Ошибка при получении кэша WHOIS для {domain}: {e}")
            return None

    async def cache_whois(self, domain: str, organization: str):
        try:
            await self.conn.execute(
                "INSERT OR REPLACE INTO whois_cache (domain, organization) VALUES (?, ?)",
                (domain, organization)
            )
            await self.conn.commit()
            logger.debug(f"Кэш WHOIS для {domain} обновлён.")
        except Exception as e:
            logger.error(f"Ошибка при кэшировании WHOIS для {domain}: {e}")

    async def close(self):
        if self.conn:
            await self.conn.close()
            logger.info("Соединение с базой данных закрыто.")
