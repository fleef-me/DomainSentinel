# ratelimit.py

import asyncio
import time
from functools import wraps
from typing import Callable, Dict
from config import Config

RATE_LIMIT_CALLS = 1  # Максимальное количество вызовов
RATE_LIMIT_PERIOD = 60  # Период в секундах

# Словарь для хранения времени последнего вызова команды для каждого пользователя
user_call_times: Dict[int, float] = {}


def rate_limit(calls: int = RATE_LIMIT_CALLS, period: int = RATE_LIMIT_PERIOD):
    """
    Декоратор для ограничения количества вызовов команды пользователем.

    :param calls: Максимальное количество вызовов
    :param period: Период в секундах
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(client, message, *args, **kwargs):
            user_id = message.from_user.id

            # Проверка, является ли пользователь администратором
            if user_id in Config.ADMIN_USER_IDS:
                return await func(client, message, *args, **kwargs)

            current_time = time.time()
            last_call = user_call_times.get(user_id, 0)

            if current_time - last_call < period:
                wait_time = int(period - (current_time - last_call))
                await message.reply_text(
                    f"Пожалуйста, подождите {wait_time} секунд перед повторным использованием этой команды."
                )
                return
            else:
                user_call_times[user_id] = current_time
                return await func(client, message, *args, **kwargs)

        return wrapper

    return decorator
