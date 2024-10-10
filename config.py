# config.py

import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    API_ID: int = int(os.getenv('API_ID', '0'))
    API_HASH: str = os.getenv('API_HASH', '')
    BOT_TOKEN: str = os.getenv('BOT_TOKEN', '')
    CHECK_INTERVAL: int = int(os.getenv('CHECK_INTERVAL', '60'))  # в минутах
    LOCAL_SOURCE: bool = os.getenv('LOCAL_SOURCE', 'true').lower() in ('false', '1', 't')
    SOURCE_URL: str = os.getenv('SOURCE_URL', 'https://community.antifilter.download/list/domains.lst')
    SOURCE_PATH: str = os.getenv('SOURCE_PATH', 'domains.lst')  # Путь к локальному файлу
    WHOIS_TIMEOUT: int = int(os.getenv('WHOIS_TIMEOUT', '10'))  # в секундах
    DATABASE_PATH: str = os.getenv('DATABASE_PATH', 'domains.db')
    USERS_FILE: str = 'users.json'
    ADMIN_USER_IDS: list = [6153626642]  # Замените на ваши user_id или добавьте других администраторов
