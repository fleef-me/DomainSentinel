# user_manager.py

import json
from config import Config
import logging
import aiofiles

logger = logging.getLogger(__name__)


class UserManager:
    def __init__(self, users_file: str = Config.USERS_FILE):
        self.users_file = users_file

    async def add_user(self, user_id: int) -> bool:
        try:
            data = await self.load_users()
            if user_id not in data["users"]:
                data["users"].append(user_id)
                await self.save_users(data)
                logger.info(f"Пользователь {user_id} добавлен.")
                return True
            logger.debug(f"Пользователь {user_id} уже существует.")
            return False
        except Exception as e:
            logger.error(f"Ошибка при добавлении пользователя {user_id}: {e}")
            return False

    async def remove_user(self, user_id: int) -> bool:
        try:
            data = await self.load_users()
            if user_id in data["users"]:
                data["users"].remove(user_id)
                await self.save_users(data)
                logger.info(f"Пользователь {user_id} удалён.")
                return True
            logger.debug(f"Пользователь {user_id} не найден.")
            return False
        except Exception as e:
            logger.error(f"Ошибка при удалении пользователя {user_id}: {e}")
            return False

    async def load_users(self) -> dict:
        try:
            async with aiofiles.open(self.users_file, 'r', encoding='utf-8') as f:
                content = await f.read()
                return json.loads(content)
        except FileNotFoundError:
            logger.warning(f"Файл {self.users_file} не найден. Создаётся новый файл.")
            return {"users": []}
        except json.JSONDecodeError as e:
            logger.error(f"Ошибка декодирования JSON в файле {self.users_file}: {e}")
            return {"users": []}
        except Exception as e:
            logger.error(f"Ошибка при загрузке пользователей из {self.users_file}: {e}")
            return {"users": []}

    async def save_users(self, data: dict):
        try:
            async with aiofiles.open(self.users_file, 'w', encoding='utf-8') as f:
                await f.write(json.dumps(data, ensure_ascii=False, indent=4))
            logger.debug(f"Список пользователей сохранён в {self.users_file}.")
        except Exception as e:
            logger.error(f"Ошибка при сохранении пользователей в {self.users_file}: {e}")
