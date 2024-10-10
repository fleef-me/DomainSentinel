# notifier.py

import json
from pyrogram import Client
from pyrogram.enums import ParseMode

from config import Config
import logging
import aiofiles

logger = logging.getLogger(__name__)


class Notifier:
    def __init__(self, app: Client):
        self.app = app

    async def send_message_to_users(self, message: str):
        users = await self.get_users()
        for user_id in users:
            print(user_id)
            try:
                await self.app.send_message(
                    chat_id=user_id,
                    text=message,
                    parse_mode=ParseMode("markdown")
                )
                logger.info(f"Уведомление отправлено пользователю {user_id}.")
            except Exception as e:
                logger.error(f"Не удалось отправить сообщение пользователю {user_id}: {e}")

    async def send_message_to_admin(self, message: str):
        admins = Config.ADMIN_USER_IDS
        # admins.extend([961097940, 1343588659,  865871473, 1109901724])
        for admin_id in admins:
            try:
                await self.app.send_message(
                    chat_id=admin_id,
                    text=message,
                    parse_mode=ParseMode("markdown")
                )
                logger.info(f"Уведомление отправлено администратору {admin_id}.")
            except Exception as e:
                logger.error(f"Не удалось отправить сообщение администратору {admin_id}: {e}")

    async def get_users(self) -> list:
        try:
            async with aiofiles.open(Config.USERS_FILE, 'r', encoding='utf-8') as f:
                content = await f.read()
                data = json.loads(content)
                return data.get("users", [])
        except json.JSONDecodeError as e:
            logger.error(f"Ошибка декодирования JSON в файле {Config.USERS_FILE}: {e}")
            return []
        except FileNotFoundError:
            logger.warning(f"Файл {Config.USERS_FILE} не найден. Создаётся новый файл.")
            return []
        except Exception as e:
            logger.error(f"Ошибка при загрузке пользователей: {e}")
            return []
