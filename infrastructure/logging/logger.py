import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

from infrastructure.system.paths import (
    get_application_log_path,
)


LOGGER_NAME = "pixel_guardian"


def configure_logging() -> logging.Logger:
    """تجهيز نظام تسجيل أحداث Pixel Guardian."""

    logger = logging.getLogger(LOGGER_NAME)

    # منع إضافة Handlers مكررة عند استدعاء الدالة أكثر من مرة
    if logger.handlers:
        return logger

    logger.setLevel(logging.DEBUG)
    logger.propagate = False

    log_path: Path = get_application_log_path()

    # حماية إضافية لضمان وجود المجلد
    log_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    formatter = logging.Formatter(
        fmt=(
            "%(asctime)s | "
            "%(levelname)s | "
            "%(name)s | "
            "%(module)s.%(funcName)s:%(lineno)d | "
            "%(message)s"
        ),
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    file_handler = RotatingFileHandler(
        filename=str(log_path),
        maxBytes=2 * 1024 * 1024,
        backupCount=5,
        encoding="utf-8",
        delay=False,
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)

    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    logger.info(
        "Logging system initialized. Log path: %s",
        log_path,
    )

    return logger


def get_logger() -> logging.Logger:
    """إرجاع Logger البرنامج الرئيسي."""

    return configure_logging()