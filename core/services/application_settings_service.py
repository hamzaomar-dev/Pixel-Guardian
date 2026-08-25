from __future__ import annotations

import os
from pathlib import Path

from PySide6.QtCore import QSettings


class ApplicationSettingsService:
    """قراءة وحفظ إعدادات Pixel Guardian العامة."""

    DEFAULTS = {
        # Language
        "general/language": "en",

        # General
        "general/restore_last_page": True,

        # Notifications
        "notifications/enabled": True,
        "notifications/sound_enabled": True,
        "notifications/minimize_to_tray": False,
        "notifications/start_minimized": False,

        # Automatic scanning
        "scanning/auto_scan_hardware": True,
        "scanning/auto_scan_game_library": True,
        "scanning/auto_scan_game_readiness": True,

        # Monitoring
        "monitoring/refresh_interval_ms": 1000,

        # Cleaner
        "maintenance/confirm_before_cleanup": True,

        # Gaming performance
        "gaming/allow_online_performance": False,
        "gaming/cache_days": 30,
    }

    SUPPORTED_LANGUAGES = (
        "en",
        "ar",
    )

    def __init__(
        self,
        settings_path: Path | None = None,
    ) -> None:
        self._settings_path = (
            settings_path
            or self.default_settings_path()
        )

        self._settings_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        self._settings = QSettings(
            str(self._settings_path),
            QSettings.Format.IniFormat,
        )

    @property
    def settings_path(self) -> Path:
        """مسار ملف الإعدادات."""

        return self._settings_path

    @property
    def language(self) -> str:
        """لغة واجهة البرنامج."""

        value = self.get_string(
            "general/language"
        ).casefold()

        if value not in self.SUPPORTED_LANGUAGES:
            return "en"

        return value

    @language.setter
    def language(
        self,
        value: str,
    ) -> None:
        normalized_value = str(
            value or ""
        ).strip().casefold()

        if normalized_value not in self.SUPPORTED_LANGUAGES:
            raise ValueError(
                f"Unsupported language: {value}"
            )

        self.set_value(
            "general/language",
            normalized_value,
        )

    @property
    def notifications_enabled(self) -> bool:
        return self.get_bool(
            "notifications/enabled"
        )

    @notifications_enabled.setter
    def notifications_enabled(
        self,
        value: bool,
    ) -> None:
        self.set_value(
            "notifications/enabled",
            bool(value),
        )

    @property
    def notification_sound_enabled(self) -> bool:
        return self.get_bool(
            "notifications/sound_enabled"
        )

    @notification_sound_enabled.setter
    def notification_sound_enabled(
        self,
        value: bool,
    ) -> None:
        self.set_value(
            "notifications/sound_enabled",
            bool(value),
        )

    @property
    def minimize_to_tray(self) -> bool:
        return self.get_bool(
            "notifications/minimize_to_tray"
        )

    @minimize_to_tray.setter
    def minimize_to_tray(
        self,
        value: bool,
    ) -> None:
        self.set_value(
            "notifications/minimize_to_tray",
            bool(value),
        )

    @property
    def start_minimized(self) -> bool:
        return self.get_bool(
            "notifications/start_minimized"
        )

    @start_minimized.setter
    def start_minimized(
        self,
        value: bool,
    ) -> None:
        self.set_value(
            "notifications/start_minimized",
            bool(value),
        )

    def get_value(
        self,
        key: str,
    ):
        """قراءة قيمة إعداد."""

        if key not in self.DEFAULTS:
            raise KeyError(
                f"Unknown setting key: {key}"
            )

        return self._settings.value(
            key,
            self.DEFAULTS[key],
        )

    def get_string(
        self,
        key: str,
    ) -> str:
        """قراءة قيمة نصية."""

        value = self.get_value(
            key
        )

        return str(
            value
        ).strip()

    def get_bool(
        self,
        key: str,
    ) -> bool:
        """قراءة Boolean بأمان."""

        value = self.get_value(
            key
        )

        if isinstance(
            value,
            bool,
        ):
            return value

        return (
            str(value)
            .strip()
            .casefold()
            in {
                "1",
                "true",
                "yes",
                "on",
            }
        )

    def get_int(
        self,
        key: str,
    ) -> int:
        """قراءة رقم صحيح بأمان."""

        value = self.get_value(
            key
        )

        try:
            return int(
                value
            )

        except (
            TypeError,
            ValueError,
        ):
            return int(
                self.DEFAULTS[key]
            )

    def set_value(
        self,
        key: str,
        value,
        sync: bool = True,
    ) -> None:
        """حفظ قيمة إعداد."""

        if key not in self.DEFAULTS:
            raise KeyError(
                f"Unknown setting key: {key}"
            )

        self._settings.setValue(
            key,
            value,
        )

        if sync:
            self.sync()

    def set_values(
        self,
        values: dict[str, object],
    ) -> None:
        """حفظ مجموعة إعدادات مرة واحدة."""

        for key, value in values.items():
            if key not in self.DEFAULTS:
                raise KeyError(
                    f"Unknown setting key: {key}"
                )

            self._settings.setValue(
                key,
                value,
            )

        self.sync()

    def restore_defaults(self) -> None:
        """استعادة جميع القيم الافتراضية."""

        self._settings.clear()

        for key, value in self.DEFAULTS.items():
            self._settings.setValue(
                key,
                value,
            )

        self.sync()

    def sync(self) -> None:
        """كتابة التغييرات داخل الملف."""

        self._settings.sync()

        if (
            self._settings.status()
            != QSettings.Status.NoError
        ):
            raise OSError(
                "Pixel Guardian settings could not be saved."
            )

    @staticmethod
    def default_settings_path() -> Path:
        """المسار الافتراضي لملف الإعدادات."""

        local_app_data = os.getenv(
            "LOCALAPPDATA"
        )

        if local_app_data:
            base_path = Path(
                local_app_data
            )

        else:
            base_path = (
                Path.home()
                / "AppData"
                / "Local"
            )

        return (
            base_path
            / "PixelGuardian"
            / "settings.ini"
        )