from __future__ import annotations

import sys

from typing import Literal

from PySide6.QtCore import (
    QObject,
    Qt,
    Signal,
    Slot,
)
from PySide6.QtWidgets import (
    QApplication,
    QSystemTrayIcon,
)

from core.services.application_settings_service import (
    ApplicationSettingsService,
)
from core.services.localization_service import (
    LocalizationService,
)
from infrastructure.logging.logger import get_logger


NotificationLevel = Literal[
    "info",
    "success",
    "warning",
    "error",
]


class NotificationService(QObject):
    """خدمة مركزية لإشعارات Pixel Guardian."""

    _notification_requested = Signal(
        str,
        str,
        str,
        int,
        bool,
    )

    def __init__(
        self,
        settings_service: (
            ApplicationSettingsService | None
        ) = None,
        localization_service: (
            LocalizationService | None
        ) = None,
        tray_icon: (
            QSystemTrayIcon | None
        ) = None,
    ) -> None:
        application = QApplication.instance()

        if application is None:
            raise RuntimeError(
                "QApplication has not been initialized."
            )

        super().__init__(
            application
        )

        self.logger = get_logger()
        self.application = application

        self.settings_service = (
            settings_service
            or getattr(
                application,
                "settings_service",
                None,
            )
            or ApplicationSettingsService()
        )

        self.localization = (
            localization_service
            or getattr(
                application,
                "localization_service",
                None,
            )
            or LocalizationService(
                settings_service=self.settings_service
            )
        )

        self._tray_icon = (
            tray_icon
            or getattr(
                application,
                "system_tray_icon",
                None,
            )
        )

        self._notification_requested.connect(
            self._display_notification,
            Qt.ConnectionType.QueuedConnection,
        )

    @property
    def notifications_enabled(self) -> bool:
        """هل الإشعارات مفعلة؟"""

        return bool(
            self.settings_service.notifications_enabled
        )

    @property
    def sound_enabled(self) -> bool:
        """هل صوت إشعارات البرنامج مفعل؟"""

        return bool(
            self.settings_service
            .notification_sound_enabled
        )

    def set_tray_icon(
        self,
        tray_icon: QSystemTrayIcon | None,
    ) -> None:
        """ربط أو تحديث أيقونة System Tray."""

        self._tray_icon = tray_icon

    def show(
        self,
        title_en: str,
        title_ar: str,
        message_en: str,
        message_ar: str,
        level: NotificationLevel = "info",
        duration_ms: int = 5000,
        force: bool = False,
    ) -> bool:
        """
        إرسال إشعار باستخدام لغة البرنامج الحالية.

        ترجع True عندما يتم قبول طلب الإشعار،
        وFalse عندما تكون الإشعارات متوقفة أو
        لا توجد أيقونة Tray متاحة.
        """

        if (
            not force
            and not self.notifications_enabled
        ):
            self.logger.info(
                "Notification skipped because "
                "notifications are disabled"
            )
            return False

        tray_icon = self._resolve_tray_icon()

        if (
            tray_icon is None
            or not tray_icon.isVisible()
        ):
            self.logger.warning(
                "Notification skipped because "
                "System Tray is unavailable"
            )
            return False

        title = self._text(
            title_en,
            title_ar,
        ).strip()

        message = self._text(
            message_en,
            message_ar,
        ).strip()

        if not title:
            title = "Pixel Guardian"

        if not message:
            self.logger.warning(
                "Notification skipped because "
                "the message is empty"
            )
            return False

        normalized_level = self._normalize_level(
            level
        )

        safe_duration = max(
            1000,
            min(
                int(duration_ms),
                30000,
            ),
        )

        self._notification_requested.emit(
            title,
            message,
            normalized_level,
            safe_duration,
            self.sound_enabled,
        )

        return True

    def info(
        self,
        title_en: str,
        title_ar: str,
        message_en: str,
        message_ar: str,
        duration_ms: int = 5000,
    ) -> bool:
        """إظهار إشعار معلومات."""

        return self.show(
            title_en=title_en,
            title_ar=title_ar,
            message_en=message_en,
            message_ar=message_ar,
            level="info",
            duration_ms=duration_ms,
        )

    def success(
        self,
        title_en: str,
        title_ar: str,
        message_en: str,
        message_ar: str,
        duration_ms: int = 5000,
    ) -> bool:
        """إظهار إشعار نجاح."""

        return self.show(
            title_en=title_en,
            title_ar=title_ar,
            message_en=message_en,
            message_ar=message_ar,
            level="success",
            duration_ms=duration_ms,
        )

    def warning(
        self,
        title_en: str,
        title_ar: str,
        message_en: str,
        message_ar: str,
        duration_ms: int = 6000,
    ) -> bool:
        """إظهار إشعار تحذير."""

        return self.show(
            title_en=title_en,
            title_ar=title_ar,
            message_en=message_en,
            message_ar=message_ar,
            level="warning",
            duration_ms=duration_ms,
        )

    def error(
        self,
        title_en: str,
        title_ar: str,
        message_en: str,
        message_ar: str,
        duration_ms: int = 7000,
    ) -> bool:
        """إظهار إشعار خطأ."""

        return self.show(
            title_en=title_en,
            title_ar=title_ar,
            message_en=message_en,
            message_ar=message_ar,
            level="error",
            duration_ms=duration_ms,
        )

    @Slot(
        str,
        str,
        str,
        int,
        bool,
    )
    def _display_notification(
        self,
        title: str,
        message: str,
        level: str,
        duration_ms: int,
        play_sound: bool,
    ) -> None:
        """عرض الإشعار داخل GUI Thread."""

        tray_icon = self._resolve_tray_icon()

        if (
            tray_icon is None
            or not tray_icon.isVisible()
        ):
            return

        tray_icon.showMessage(
            title,
            message,
            self._message_icon(
                level
            ),
            duration_ms,
        )

        if play_sound:
            self._play_sound(
                level
            )

        self.logger.info(
            "Notification displayed. "
            "Level: %s, title: %s",
            level,
            title,
        )

    def _resolve_tray_icon(
        self,
    ) -> QSystemTrayIcon | None:
        """إرجاع أيقونة الـTray الحالية."""

        if self._tray_icon is not None:
            return self._tray_icon

        tray_icon = getattr(
            self.application,
            "system_tray_icon",
            None,
        )

        if isinstance(
            tray_icon,
            QSystemTrayIcon,
        ):
            self._tray_icon = tray_icon
            return tray_icon

        return None

    @staticmethod
    def _normalize_level(
        level: str,
    ) -> str:
        """تنظيف مستوى الإشعار."""

        normalized_level = str(
            level or "info"
        ).strip().casefold()

        if normalized_level not in {
            "info",
            "success",
            "warning",
            "error",
        }:
            return "info"

        return normalized_level

    @staticmethod
    def _message_icon(
        level: str,
    ) -> QSystemTrayIcon.MessageIcon:
        """اختيار أيقونة الإشعار."""

        if level == "warning":
            return (
                QSystemTrayIcon
                .MessageIcon
                .Warning
            )

        if level == "error":
            return (
                QSystemTrayIcon
                .MessageIcon
                .Critical
            )

        return (
            QSystemTrayIcon
            .MessageIcon
            .Information
        )

    def _play_sound(
        self,
        level: str,
    ) -> None:
        """
        تشغيل صوت إشعار بسيط على Windows.

        هذا الصوت تابع للبرنامج. إعدادات إشعارات
        Windows قد تضيف أو تمنع أصواتًا أخرى.
        """

        if not sys.platform.startswith(
            "win"
        ):
            QApplication.beep()
            return

        try:
            import winsound

            sound_type = {
                "info": winsound.MB_ICONASTERISK,
                "success": winsound.MB_OK,
                "warning": winsound.MB_ICONEXCLAMATION,
                "error": winsound.MB_ICONHAND,
            }.get(
                level,
                winsound.MB_ICONASTERISK,
            )

            winsound.MessageBeep(
                sound_type
            )

        except (
            ImportError,
            OSError,
            RuntimeError,
        ) as error:
            self.logger.warning(
                "Notification sound could not "
                "be played: %s",
                error,
            )

    def _text(
        self,
        english: str,
        arabic: str,
    ) -> str:
        """اختيار النص حسب لغة البرنامج."""

        if self.localization.is_rtl:
            return arabic

        return english
    