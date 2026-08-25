from __future__ import annotations

import time

from PySide6.QtCore import QThread, QTimer, Qt
from PySide6.QtGui import QCloseEvent
from PySide6.QtWidgets import (
    QApplication,
    QBoxLayout,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from core.services.localization_service import (
    LocalizationService,
)
from infrastructure.logging.logger import get_logger
from ui.navigation.page_router import PageRouter
from ui.navigation.sidebar import Sidebar
from ui.pages.about_page import AboutPage
from ui.pages.cleaner_page import CleanerPage
from ui.pages.disk_health_page import DiskHealthPage
from ui.pages.drivers_page import DriversPage
from ui.pages.game_lab_page import GameLabPage
from ui.pages.hardware_page import HardwarePage
from ui.pages.live_monitor_page import LiveMonitorPage
from ui.pages.settings_page import SettingsPage
from ui.styles.style_loader import load_app_style


class MainWindow(QMainWindow):
    """النافذة الرئيسية لبرنامج Pixel Guardian."""

    def __init__(self) -> None:
        super().__init__()

        self.logger = get_logger()

        self.logger.info(
            "Initializing main window"
        )

        application = QApplication.instance()

        if application is None:
            raise RuntimeError(
                "QApplication has not been initialized."
            )

        self.application = application

        self.settings_service = getattr(
            application,
            "settings_service",
            None,
        )

        self._tray_close_notice_shown = False
        self._shutdown_started = False

        self.application.aboutToQuit.connect(
            self._shutdown_background_workers
        )

        self.localization = getattr(
            application,
            "localization_service",
            LocalizationService(),
        )

        self.is_rtl = (
            self.localization.is_rtl
        )

        self._load_global_style()

        self.setWindowTitle(
            self.localization.tr(
                "app_name"
            )
        )

        self.setMinimumSize(
            1000,
            650,
        )

        self.resize(
            1200,
            750,
        )

        if self.is_rtl:
            self.setLayoutDirection(
                Qt.LayoutDirection.RightToLeft
            )
        else:
            self.setLayoutDirection(
                Qt.LayoutDirection.LeftToRight
            )

        self.sidebar = Sidebar()
        self.page_router = PageRouter()

        self.sidebar.setLayoutDirection(
            Qt.LayoutDirection.RightToLeft
            if self.is_rtl
            else Qt.LayoutDirection.LeftToRight
        )

        self.page_router.setLayoutDirection(
            Qt.LayoutDirection.RightToLeft
            if self.is_rtl
            else Qt.LayoutDirection.LeftToRight
        )

        self._setup_ui()

        self._show_page(
            "dashboard"
        )

        self.logger.info(
            "Main window initialized successfully"
        )

    def _load_global_style(self) -> None:
        """تحميل تصميم البرنامج على QApplication."""

        stylesheet = load_app_style()

        self.application.setStyleSheet(
            stylesheet
        )

        self.logger.info(
            "Application stylesheet loaded successfully. "
            "Characters: %s",
            len(stylesheet),
        )

    def _setup_ui(self) -> None:
        """إنشاء عناصر الواجهة وصفحات البرنامج."""

        central_widget = QWidget()

        central_widget.setObjectName(
            "centralWidget"
        )

        self.setCentralWidget(
            central_widget
        )

        root_layout = QHBoxLayout(
            central_widget
        )

        root_layout.setContentsMargins(
            0,
            0,
            0,
            0,
        )

        root_layout.setSpacing(
            0
        )

        # نخلي اتجاه الـLayout ثابتًا ونرتب العناصر
        # يدويًا حتى ينتقل Sidebar فعليًا.
        root_layout.setDirection(
            QBoxLayout.Direction.LeftToRight
        )

        dashboard_widget = (
            self._create_dashboard_page()
        )

        self.page_router.add_page(
            "dashboard",
            dashboard_widget,
        )

        self.page_router.add_page(
            "hardware",
            HardwarePage(),
        )

        self.page_router.add_page(
            "live_monitor",
            LiveMonitorPage(),
        )

        self.page_router.add_page(
            "disk_health",
            DiskHealthPage(),
        )

        self.page_router.add_page(
            "drivers",
            DriversPage(),
        )

        self.page_router.add_page(
            "cleaner",
            CleanerPage(),
        )

        self.page_router.add_page(
            "game_lab",
            GameLabPage(),
        )

        self.page_router.add_page(
            "settings",
            SettingsPage(),
        )

        self.page_router.add_page(
            "about",
            AboutPage(),
        )

        self.sidebar.page_selected.connect(
            self._show_page
        )

        if self.is_rtl:
            # المحتوى على اليسار والـSidebar على اليمين.
            root_layout.addWidget(
                self.page_router,
                1,
            )

            root_layout.addWidget(
                self.sidebar
            )

        else:
            # الـSidebar على اليسار والمحتوى على اليمين.
            root_layout.addWidget(
                self.sidebar
            )

            root_layout.addWidget(
                self.page_router,
                1,
            )

    def _create_dashboard_page(
        self,
    ) -> QWidget:
        """إنشاء صفحة Dashboard."""

        content_widget = QWidget()

        content_widget.setObjectName(
            "contentWidget"
        )

        main_layout = QVBoxLayout(
            content_widget
        )

        main_layout.setContentsMargins(
            40,
            40,
            40,
            40,
        )

        main_layout.setSpacing(
            20
        )

        header = QLabel(
            self._text(
                "PIXEL GUARDIAN",
                "بيكسل جارديان",
            )
        )

        header.setObjectName(
            "headerLabel"
        )

        header.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        subtitle = QLabel(
            self._text(
                (
                    "Smart PC Hardware Monitoring "
                    "and Maintenance"
                ),
                (
                    "مراقبة وصيانة ذكية "
                    "لجهاز الكمبيوتر"
                ),
            )
        )

        subtitle.setObjectName(
            "subtitleLabel"
        )

        subtitle.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        welcome_card = QFrame()

        welcome_card.setObjectName(
            "welcomeCard"
        )

        card_layout = QVBoxLayout(
            welcome_card
        )

        card_layout.setContentsMargins(
            30,
            30,
            30,
            30,
        )

        card_layout.setSpacing(
            15
        )

        welcome_title = QLabel(
            self._text(
                "Welcome to Pixel Guardian",
                "مرحبًا بك في بيكسل جارديان",
            )
        )

        welcome_title.setObjectName(
            "welcomeTitle"
        )

        welcome_title.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        welcome_description = QLabel(
            self._text(
                (
                    "Hardware Information, Live Monitor, "
                    "Disk Health, Drivers, Cleaner and "
                    "Game Lab modules are ready."
                ),
                (
                    "وحدات معلومات الجهاز والمراقبة "
                    "المباشرة وصحة الأقراص والتعريفات "
                    "والتنظيف ومختبر الألعاب جاهزة."
                ),
            )
        )

        welcome_description.setObjectName(
            "welcomeDescription"
        )

        welcome_description.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        welcome_description.setWordWrap(
            True
        )

        test_button = QPushButton(
            self._text(
                "Test Application",
                "اختبار البرنامج",
            )
        )

        test_button.setObjectName(
            "primaryButton"
        )

        test_button.setCursor(
            Qt.CursorShape.PointingHandCursor
        )

        test_button.clicked.connect(
            self._test_application
        )

        self.status_label = QLabel(
            self._text(
                "Application status: Ready",
                "حالة البرنامج: جاهز",
            )
        )

        self.status_label.setObjectName(
            "statusLabel"
        )

        self.status_label.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        card_layout.addWidget(
            welcome_title
        )

        card_layout.addWidget(
            welcome_description
        )

        card_layout.addSpacing(
            10
        )

        card_layout.addWidget(
            test_button
        )

        card_layout.addWidget(
            self.status_label
        )

        main_layout.addStretch()

        main_layout.addWidget(
            header
        )

        main_layout.addWidget(
            subtitle
        )

        main_layout.addSpacing(
            10
        )

        main_layout.addWidget(
            welcome_card
        )

        main_layout.addStretch()

        return content_widget

    def _show_page(
        self,
        page_name: str,
    ) -> None:
        """التنقل إلى الصفحة المطلوبة."""

        page_changed = (
            self.page_router.show_page(
                page_name
            )
        )

        if page_changed:
            self.sidebar.set_active_page(
                page_name
            )

            self.logger.info(
                "Page opened successfully: %s",
                page_name,
            )

        else:
            self.logger.warning(
                "Requested page was not found: %s",
                page_name,
            )

    def _test_application(self) -> None:
        """اختبار استجابة الواجهة."""

        self.logger.info(
            "Application test button "
            "clicked successfully"
        )

        self.status_label.setText(
            self._text(
                (
                    "Application status: "
                    "Working correctly"
                ),
                (
                    "حالة البرنامج: "
                    "يعمل بشكل صحيح"
                ),
            )
        )

    def closeEvent(
        self,
        event: QCloseEvent,
    ) -> None:
        """
        إخفاء النافذة في System Tray عند تفعيل الخيار.

        خيار Exit الموجود في قائمة الـTray يظل مسؤولًا
        عن إغلاق البرنامج فعليًا.
        """

        if self._should_minimize_to_tray():
            event.ignore()
            self.hide()

            self._show_tray_close_notice()

            self.logger.info(
                "Main window hidden in System Tray"
            )

            return

        self.logger.info(
            "Main window close accepted"
        )

        self._shutdown_background_workers()

        super().closeEvent(
            event
        )

    def _shutdown_background_workers(
        self,
    ) -> None:
        """
        إيقاف المؤقتات والـThreads قبل خروج البرنامج.

        يتم استخدام requestInterruption وquit أولًا،
        ثم انتظار قصير لمعالجة إشارات finished بأمان.
        """

        if self._shutdown_started:
            return

        self._shutdown_started = True

        self.logger.info(
            "Starting graceful application shutdown"
        )

        timers = self.findChildren(
            QTimer
        )

        for timer in timers:
            if timer.isActive():
                timer.stop()

        threads = [
            thread
            for thread in self.findChildren(
                QThread
            )
            if thread.isRunning()
        ]

        if not threads:
            self.logger.info(
                "Graceful shutdown completed: "
                "no active background threads"
            )
            return

        self.logger.info(
            "Stopping %s active background thread(s)",
            len(threads),
        )

        for thread in threads:
            thread.requestInterruption()
            thread.quit()

        deadline = time.monotonic() + 20.0

        while time.monotonic() < deadline:
            running_threads = [
                thread
                for thread in threads
                if thread.isRunning()
            ]

            if not running_threads:
                break

            self.application.processEvents()

            for thread in running_threads:
                thread.wait(
                    50
                )

        remaining_threads = [
            thread
            for thread in threads
            if thread.isRunning()
        ]

        if remaining_threads:
            self.logger.warning(
                "%s background thread(s) did not stop "
                "before the shutdown timeout",
                len(remaining_threads),
            )
        else:
            self.logger.info(
                "All background threads stopped safely"
            )

    def _should_minimize_to_tray(
        self,
    ) -> bool:
        """تحديد ما إذا كان زر X يجب أن يخفي النافذة."""

        if bool(
            getattr(
                self.application,
                "exit_requested",
                False,
            )
        ):
            return False

        settings_service = (
            self.settings_service
            or getattr(
                self.application,
                "settings_service",
                None,
            )
        )

        if settings_service is None:
            return False

        minimize_to_tray = bool(
            getattr(
                settings_service,
                "minimize_to_tray",
                False,
            )
        )

        if not minimize_to_tray:
            return False

        tray_icon = getattr(
            self.application,
            "system_tray_icon",
            None,
        )

        return bool(
            tray_icon is not None
            and tray_icon.isVisible()
        )

    def _show_tray_close_notice(
        self,
    ) -> None:
        """عرض إشعار واحد عبر خدمة الإشعارات المركزية."""

        if self._tray_close_notice_shown:
            return

        notification_service = getattr(
            self.application,
            "notification_service",
            None,
        )

        if notification_service is None:
            self.logger.warning(
                "Tray close notice skipped because "
                "NotificationService is unavailable"
            )
            return

        notification_sent = (
            notification_service.info(
                title_en=(
                    "Pixel Guardian is still running"
                ),
                title_ar=(
                    "بيكسل جارديان ما زال يعمل"
                ),
                message_en=(
                    "The window was hidden. "
                    "Use the icon beside the Windows clock "
                    "to open the app or exit."
                ),
                message_ar=(
                    "تم إخفاء النافذة. استخدم الأيقونة "
                    "بجانب ساعة ويندوز لفتح البرنامج "
                    "أو الخروج منه."
                ),
                duration_ms=5000,
            )
        )

        if not notification_sent:
            return

        self._tray_close_notice_shown = True

        self.logger.info(
            "System Tray close notice requested "
            "through NotificationService"
        )

    def _text(
        self,
        english: str,
        arabic: str,
    ) -> str:
        """اختيار النص حسب لغة البرنامج."""

        if self.is_rtl:
            return arabic

        return english