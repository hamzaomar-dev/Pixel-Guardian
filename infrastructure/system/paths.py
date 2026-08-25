import os
from pathlib import Path


APP_FOLDER_NAME = "PixelGuardian"


def get_local_app_data_directory() -> Path:
    """
    إرجاع مجلد بيانات Pixel Guardian وإنشاؤه تلقائيًا.

    المسار على Windows:
    C:\\Users\\User\\AppData\\Local\\PixelGuardian
    """

    local_app_data = os.getenv("LOCALAPPDATA")

    if local_app_data:
        app_directory = Path(local_app_data) / APP_FOLDER_NAME
    else:
        app_directory = Path.home() / "AppData" / "Local" / APP_FOLDER_NAME

    app_directory.mkdir(
        parents=True,
        exist_ok=True,
    )

    return app_directory


def get_logs_directory() -> Path:
    """إرجاع مجلد Logs وإنشاؤه تلقائيًا."""

    logs_directory = get_local_app_data_directory() / "logs"

    logs_directory.mkdir(
        parents=True,
        exist_ok=True,
    )

    return logs_directory


def get_application_log_path() -> Path:
    """إرجاع مسار سجل البرنامج الرئيسي."""

    log_path = get_logs_directory() / "application.log"

    # ضمان وجود المجلد حتى لو تغير المسار مستقبلًا
    log_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    return log_path


def get_crash_log_path() -> Path:
    """إرجاع مسار سجل الأخطاء غير المتوقعة."""

    crash_path = get_logs_directory() / "crashes.log"

    crash_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    return crash_path