from __future__ import annotations

import sys
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QAction, QIcon
from PySide6.QtWidgets import (
    QApplication,
    QMenu,
    QStyle,
    QSystemTrayIcon,
)

from core.services.application_settings_service import (
    ApplicationSettingsService,
)
from core.services.localization_service import (
    LocalizationService,
)
from core.services.notification_service import (
    NotificationService,
)
from infrastructure.logging.crash_handler import (
    install_global_exception_handler,
)
from infrastructure.logging.logger import get_logger
from ui.main_window import MainWindow


def _resource_path(
    relative_path: str,
) -> Path:
    """
    إرجاع مسار ملف الموارد أثناء التطوير
    وبعد تجميع البرنامج باستخدام PyInstaller.
    """

    base_path = Path(
        getattr(
            sys,
            "_MEIPASS",
            Path(__file__).resolve().parent.parent,
        )
    )

    return (
        base_path
        / relative_path
    )


def start_application() -> None:
    """تشغيل تطبيق Pixel Guardian."""

    logger = get_logger()
    install_global_exception_handler()

    logger.info(
        "Starting Pixel Guardian"
    )

    app = QApplication(
        sys.argv
    )

    app.setApplicationName(
        "Pixel Guardian"
    )

    app.setApplicationVersion(
        "1.0.0"
    )

    app.setOrganizationName(
        "Pixel Guardian"
    )

    icon_path = _resource_path(
        "assets/icons/pixel_guardian_icon.ico"
    )

    app_icon = QIcon(
        str(icon_path)
    )

    if not app_icon.isNull():
        app.setWindowIcon(
            app_icon
        )

        logger.info(
            "Application icon loaded successfully: %s",
            icon_path,
        )

    else:
        app_icon = (
            app.style().standardIcon(
                QStyle.StandardPixmap.SP_ComputerIcon
            )
        )

        app.setWindowIcon(
            app_icon
        )

        logger.warning(
            "Application icon could not be loaded. "
            "Fallback icon is being used: %s",
            icon_path,
        )

    # تستخدمه MainWindow لمعرفة هل الإغلاق جاء
    # من خيار Exit الحقيقي داخل قائمة الـTray.
    app.exit_requested = False

    settings_service = (
        ApplicationSettingsService()
    )

    localization_service = (
        LocalizationService(
            settings_service=settings_service
        )
    )

    # حفظ الخدمات داخل QApplication حتى تستطيع
    # الصفحات والنوافذ استخدامها لاحقًا.
    app.settings_service = (
        settings_service
    )

    app.localization_service = (
        localization_service
    )

    app.setApplicationDisplayName(
        localization_service.tr(
            "app_name"
        )
    )

    if localization_service.is_rtl:
        app.setLayoutDirection(
            Qt.LayoutDirection.RightToLeft
        )

        logger.info(
            "Application language loaded: Arabic"
        )

    else:
        app.setLayoutDirection(
            Qt.LayoutDirection.LeftToRight
        )

        logger.info(
            "Application language loaded: English"
        )

    window = MainWindow()

    window.setWindowIcon(
        app_icon
    )

    # حفظ مرجع النافذة داخل QApplication حتى يبقى
    # متاحًا لخدمة الـSystem Tray والإشعارات.
    app.main_window = window

    minimize_to_tray = bool(
        settings_service.minimize_to_tray
    )

    start_minimized = bool(
        settings_service.start_minimized
    )

    tray_available = (
        QSystemTrayIcon.isSystemTrayAvailable()
    )

    tray_icon: QSystemTrayIcon | None = None
    tray_menu: QMenu | None = None

    if tray_available:
        tray_icon = QSystemTrayIcon(
            app
        )

        tray_icon.setIcon(
            app_icon
        )

        tray_icon.setToolTip(
            "Pixel Guardian"
        )

        tray_menu = QMenu(
            window
        )

        open_action = QAction(
            (
                "فتح Pixel Guardian"
                if localization_service.is_rtl
                else "Open Pixel Guardian"
            ),
            tray_menu,
        )

        hide_action = QAction(
            (
                "إخفاء النافذة"
                if localization_service.is_rtl
                else "Hide Window"
            ),
            tray_menu,
        )

        exit_action = QAction(
            (
                "خروج"
                if localization_service.is_rtl
                else "Exit"
            ),
            tray_menu,
        )

        def show_main_window() -> None:
            """إظهار نافذة البرنامج وإعادتها للواجهة."""

            if window.isMinimized():
                window.showNormal()

            else:
                window.show()

            window.raise_()
            window.activateWindow()

        def hide_main_window() -> None:
            """إخفاء نافذة البرنامج مع إبقائه يعمل."""

            window.hide()

        def quit_application() -> None:
            """إغلاق البرنامج فعليًا من قائمة الـTray."""

            app.exit_requested = True

            if tray_icon is not None:
                tray_icon.hide()

            window.close()
            app.quit()

        def handle_tray_activation(
            reason: QSystemTrayIcon.ActivationReason,
        ) -> None:
            """فتح النافذة عند الضغط على أيقونة الـTray."""

            if reason in (
                QSystemTrayIcon.ActivationReason.Trigger,
                QSystemTrayIcon.ActivationReason.DoubleClick,
            ):
                show_main_window()

        open_action.triggered.connect(
            show_main_window
        )

        hide_action.triggered.connect(
            hide_main_window
        )

        exit_action.triggered.connect(
            quit_application
        )

        tray_menu.addAction(
            open_action
        )

        tray_menu.addAction(
            hide_action
        )

        tray_menu.addSeparator()

        tray_menu.addAction(
            exit_action
        )

        tray_icon.setContextMenu(
            tray_menu
        )

        tray_icon.activated.connect(
            handle_tray_activation
        )

        tray_icon.show()

        # حفظ المراجع حتى لا يتم حذف عناصر الـTray.
        app.system_tray_icon = tray_icon
        app.system_tray_menu = tray_menu
        app.tray_open_action = open_action
        app.tray_hide_action = hide_action
        app.tray_exit_action = exit_action

        logger.info(
            "System Tray initialized successfully"
        )

    else:
        app.system_tray_icon = None

        logger.warning(
            "System Tray is not available on this system"
        )

    # إنشاء خدمة الإشعارات بعد تجهيز أيقونة الـTray،
    # ثم حفظها داخل QApplication لتستخدمها كل الصفحات.
    notification_service = NotificationService(
        settings_service=settings_service,
        localization_service=localization_service,
        tray_icon=tray_icon,
    )

    app.notification_service = (
        notification_service
    )

    logger.info(
        "Notification service initialized successfully. "
        "Enabled: %s, sound: %s",
        notification_service.notifications_enabled,
        notification_service.sound_enabled,
    )

    # عند تفعيل Minimize to Tray يجب ألا يغلق التطبيق
    # عندما تُغلق آخر نافذة.
    tray_mode_enabled = (
        minimize_to_tray
        and tray_available
    )

    app.setQuitOnLastWindowClosed(
        not tray_mode_enabled
    )

    if (
        start_minimized
        and tray_mode_enabled
    ):
        window.hide()

        logger.info(
            "Main window started hidden in System Tray"
        )

    elif start_minimized:
        window.showMinimized()

        logger.info(
            "Main window started minimized"
        )

    else:
        window.show()

        logger.info(
            "Main window displayed successfully"
        )

    exit_code = app.exec()

    if tray_icon is not None:
        tray_icon.hide()

    logger.info(
        "Pixel Guardian closed with exit code: %s",
        exit_code,
    )

    sys.exit(
        exit_code
    )