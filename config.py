import os
from pathlib import Path
from dotenv import load_dotenv

# Загрузить .env файл из директории проекта
env_path = Path(__file__).parent / '.env'
load_dotenv(dotenv_path=env_path)

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_IDS = list(map(int, os.getenv("ADMIN_IDS", "").split(","))) if os.getenv("ADMIN_IDS") else []

SESSION_TIMEOUT = 600  # 10 минут

ERROR_MESSAGES = {
    "invalid_binary": "❌ Ошибка: Введенная последовательность содержит недопустимые символы. Используйте только 0 и 1.",
    "invalid_number": "❌ Ошибка: Некорректное числовое значение.",
    "timeout": "⏰ Сессия истекла. Пожалуйста, начните заново с команды /start",
    "invalid_choice": "❌ Ошибка: Недопустимый выбор.",
    "invalid_input": "❌ Ошибка: Некорректный ввод данных."
}

