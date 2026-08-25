import logging
import sys
from types import TracebackType
from typing import Type

from PySide6.QtWidgets import QApplication, QMessageBox

from infrastructure.system.paths import get_crash_log_path


def install_global_exception_handler() -> None:
    """التقاط الأخطاء غير المعالجة وتسجيلها داخل crashes.log."""

    crash_log_path = get_crash_log_path()

    crash_log_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    crash_logger = logging.getLogger(
        "pixel_guardian.crashes"
    )

    if not crash_logger.handlers:
        crash_logger.setLevel(logging.ERROR)
        crash_logger.propagate = False

        file_handler = logging.FileHandler(
            filename=str(crash_log_path),
            encoding="utf-8",
        )

        formatter = logging.Formatter(
            fmt=(
                "%(asctime)s | "
                "%(levelname)s | "
                "%(message)s"
            ),
            datefmt="%Y-%m-%d %H:%M:%S",
        )

        file_handler.setFormatter(formatter)
        crash_logger.addHandler(file_handler)

    def handle_exception(
        exception_type: Type[BaseException],
        exception_value: BaseException,
        exception_traceback: TracebackType | None,
    ) -> None:
        if issubclass(exception_type, KeyboardInterrupt):
            sys.__excepthook__(
                exception_type,
                exception_value,
                exception_traceback,
            )
            return

        crash_logger.critical(
            "Unhandled application exception",
            exc_info=(
                exception_type,
                exception_value,
                exception_traceback,
            ),
        )

        application = QApplication.instance()

        if application is not None:
            QMessageBox.critical(
                None,
                "Pixel Guardian Error",
                (
                    "An unexpected error occurred.\n\n"
                    "The error details were saved in:\n"
                    f"{crash_log_path}"
                ),
            )
        else:
            sys.__excepthook__(
                exception_type,
                exception_value,
                exception_traceback,
            )

    sys.excepthook = handle_exception