import logging
import sys

from app.core.config import settings


def configure_logging() -> logging.Logger:
    logger = logging.getLogger("sentinel")
    logger.setLevel(logging.DEBUG if settings.is_development else logging.INFO)

    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter(
            "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    return logger


logger = configure_logging()