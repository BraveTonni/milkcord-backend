import logging
import logging.config

from src.core.config import settings


def setup_logging() -> None:
    """Настраивает консольный логгер приложения.

    Уровень задаётся переменной окружения LOG_LEVEL (по умолчанию INFO),
    формат одинаковый в dev и prod — различие только в уровне детализации.
    """
    level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)

    logging.config.dictConfig(
        {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "default": {
                    "format": "%(asctime)s %(levelname)-8s %(name)s: %(message)s",
                    "datefmt": "%Y-%m-%d %H:%M:%S",
                },
            },
            "handlers": {
                "console": {
                    "class": "logging.StreamHandler",
                    "formatter": "default",
                },
            },
            "root": {"level": level, "handlers": ["console"]},
        }
    )
