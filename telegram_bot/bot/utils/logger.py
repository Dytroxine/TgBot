import logging


# Настройка логирования
logging.basicConfig(
    level=logging.WARNING,  # Уровень логирования: DEBUG, INFO, WARNING, ERROR, CRITICAL
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("bot.log"),  # Логи будут записываться в файл bot.log
        logging.StreamHandler()  # Логи будут отображаться в консоли (опционально)
    ]
)

logger = logging.getLogger(__name__)