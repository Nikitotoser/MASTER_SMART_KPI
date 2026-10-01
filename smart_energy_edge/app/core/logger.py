import logging
import sys
from logging.handlers import RotatingFileHandler
from app.core.config import LOGS_DIR


def setup_logger(name: str = "smart_edge") -> logging.Logger:
    """
    Ініціалізує та налаштовує глобальний логер для мікросервісу.
    Реалізує ротацію файлів та розділення за рівнями важливості.
    """
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)  # Збираємо абсолютно всі події

    # Запобігаємо дублюванню логів при гарячому перезавантаженні
    if logger.handlers:
        return logger

    # Формат повідомлення: Час | Рівень | Модуль:Функція | Повідомлення
    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(module)s:%(funcName)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    # 1. Вивід у консоль (тільки INFO і вище)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)

    # 2. Загальний файл логів (DEBUG і вище, з ротацією по 5 МБ)
    file_handler = RotatingFileHandler(
        filename=f"{LOGS_DIR}/app.log",
        maxBytes=5 * 1024 * 1024,
        backupCount=3,
        encoding='utf-8'
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)

    # 3. Файл тільки для критичних помилок (ERROR і вище)
    error_handler = RotatingFileHandler(
        filename=f"{LOGS_DIR}/errors.log",
        maxBytes=5 * 1024 * 1024,
        backupCount=3,
        encoding='utf-8'
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(formatter)

    # Підключаємо обробники до нашого логера
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
    logger.addHandler(error_handler)

    return logger

logger = setup_logger()