from __future__ import annotations

import os
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from core.services.application_settings_service import (
    ApplicationSettingsService,
)
from core.services.localization_service import (
    LocalizationService,
)


class SettingsPage(QWidget):
    """صفحة إعدادات Pixel Guardian."""

    def __init__(self) -> None:
        super().__init__()

        application = QApplication.instance()

        if application is None:
            raise RuntimeError(
                "QApplication has not been initialized."
            )

        self.application = application

        self.settings_service = getattr(
            application,
            "settings_service",
            ApplicationSettingsService(),
        )

        self.localization = getattr(
            application,
            "localization_service",
            LocalizationService(
                settings_service=self.settings_service
            ),
        )

        self.current_language = (
            self.settings_service.language
        )

        self.settings_path = (
            self.settings_service.settings_path
        )

        self.setObjectName("page")

        self.setLayoutDirection(
            Qt.LayoutDirection.RightToLeft
            if self.current_language == "ar"
            else Qt.LayoutDirection.LeftToRight
        )

        self._setup_ui()
        self._load_settings()
        self._connect_live_notification_settings()

    def _setup_ui(self) -> None:
        """إنشاء واجهة صفحة الإعدادات."""

        main_layout = QVBoxLayout(self)

        main_layout.setContentsMargins(
            40,
            35,
            40,
            35,
        )

        main_layout.setSpacing(18)

        self.title_label = QLabel(
            self._text(
                "Settings",
                "الإعدادات",
            )
        )

        self.title_label.setObjectName(
            "pageTitle"
        )

        self.subtitle_label = QLabel(
            self._text(
                (
                    "Customize Pixel Guardian and manage "
                    "locally stored application preferences."
                ),
                (
                    "خصص بيكسل جارديان وأدر إعدادات "
                    "البرنامج المحفوظة محليًا."
                ),
            )
        )

        self.subtitle_label.setObjectName(
            "pageSubtitle"
        )

        self.subtitle_label.setWordWrap(
            True
        )

        main_layout.addWidget(
            self.title_label
        )

        main_layout.addWidget(
            self.subtitle_label
        )

        self.scroll_area = QScrollArea()

        self.scroll_area.setObjectName(
            "settingsScrollArea"
        )

        self.scroll_area.setWidgetResizable(
            True
        )

        self.scroll_area.setFrameShape(
            QFrame.Shape.NoFrame
        )

        self.scroll_container = QWidget()

        self.scroll_container.setObjectName(
            "settingsScrollContainer"
        )

        self.sections_layout = QVBoxLayout(
            self.scroll_container
        )

        self.sections_layout.setContentsMargins(
            0,
            4,
            10,
            4,
        )

        self.sections_layout.setSpacing(
            16
        )

        self._create_general_section()
        self._create_notifications_section()
        self._create_scanning_section()
        self._create_monitoring_section()
        self._create_gaming_section()
        self._create_maintenance_section()
        self._create_storage_section()

        self.sections_layout.addStretch()

        self.scroll_area.setWidget(
            self.scroll_container
        )

        main_layout.addWidget(
            self.scroll_area,
            1,
        )

        self._create_footer(
            main_layout
        )

    def _create_general_section(self) -> None:
        """إعدادات اللغة والسلوك العام."""

        section, layout = self._create_section(
            title=self._text(
                "General",
                "عام",
            ),
            description=self._text(
                (
                    "Choose the application language "
                    "and general startup behavior."
                ),
                (
                    "اختر لغة البرنامج وسلوك التشغيل "
                    "العام."
                ),
            ),
        )

        self.language_combo = QComboBox()

        self.language_combo.setObjectName(
            "settingsComboBox"
        )

        self.language_combo.setMinimumWidth(
            190
        )

        self.language_combo.setMinimumHeight(
            38
        )

        self.language_combo.addItem(
            "English",
            "en",
        )

        self.language_combo.addItem(
            "العربية",
            "ar",
        )

        self._add_control_row(
            layout=layout,
            title=self._text(
                "Language",
                "اللغة",
            ),
            description=self._text(
                (
                    "Choose the interface language. "
                    "Restart Pixel Guardian after saving "
                    "to apply it to every page."
                ),
                (
                    "اختر لغة الواجهة. أعد تشغيل بيكسل "
                    "جارديان بعد الحفظ لتطبيقها على "
                    "جميع الصفحات."
                ),
            ),
            control=self.language_combo,
        )

        self.restore_last_page_checkbox = QCheckBox(
            self._text(
                (
                    "Restore the last opened page "
                    "when Pixel Guardian starts"
                ),
                (
                    "فتح آخر صفحة مستخدمة عند "
                    "تشغيل بيكسل جارديان"
                ),
            )
        )

        self.restore_last_page_checkbox.setObjectName(
            "settingsCheckBox"
        )

        self._add_control_row(
            layout=layout,
            title=self._text(
                "Restore Last Page",
                "استعادة آخر صفحة",
            ),
            description=self._text(
                (
                    "Open the page that was active "
                    "before the application was closed."
                ),
                (
                    "فتح الصفحة التي كانت نشطة قبل "
                    "إغلاق البرنامج."
                ),
            ),
            control=self.restore_last_page_checkbox,
        )

        self.sections_layout.addWidget(
            section
        )

    def _create_notifications_section(self) -> None:
        """إعدادات الإشعارات والتشغيل المصغر."""

        section, layout = self._create_section(
            title=self._text(
                "Notifications",
                "الإشعارات",
            ),
            description=self._text(
                (
                    "Control Windows notifications, sounds "
                    "and background behavior."
                ),
                (
                    "تحكم بإشعارات ويندوز والأصوات "
                    "وطريقة عمل البرنامج بالخلفية."
                ),
            ),
        )

        self.notifications_enabled_checkbox = QCheckBox(
            self._text(
                "Enable Windows notifications",
                "تشغيل إشعارات ويندوز",
            )
        )

        self.notifications_enabled_checkbox.setObjectName(
            "settingsCheckBox"
        )

        self.notifications_enabled_checkbox.toggled.connect(
            self._update_notification_controls
        )

        self._add_control_row(
            layout=layout,
            title=self._text(
                "Windows Notifications",
                "إشعارات ويندوز",
            ),
            description=self._text(
                (
                    "Show notifications when scans, "
                    "cleaning and maintenance tasks finish."
                ),
                (
                    "عرض إشعار عند انتهاء الفحوصات "
                    "والتنظيف وعمليات الصيانة."
                ),
            ),
            control=self.notifications_enabled_checkbox,
        )

        self.notification_sound_checkbox = QCheckBox(
            self._text(
                "Play notification sounds",
                "تشغيل صوت الإشعارات",
            )
        )

        self.notification_sound_checkbox.setObjectName(
            "settingsCheckBox"
        )

        self._add_control_row(
            layout=layout,
            title=self._text(
                "Notification Sound",
                "صوت الإشعار",
            ),
            description=self._text(
                (
                    "Play the standard Windows sound "
                    "when Pixel Guardian shows a notification."
                ),
                (
                    "تشغيل صوت ويندوز الافتراضي عند "
                    "عرض إشعار من بيكسل جارديان."
                ),
            ),
            control=self.notification_sound_checkbox,
        )

        self.minimize_to_tray_checkbox = QCheckBox(
            self._text(
                (
                    "Keep Pixel Guardian in the system tray "
                    "when the window is closed"
                ),
                (
                    "إبقاء بيكسل جارديان بجانب الساعة "
                    "عند إغلاق النافذة"
                ),
            )
        )

        self.minimize_to_tray_checkbox.setObjectName(
            "settingsCheckBox"
        )

        self._add_control_row(
            layout=layout,
            title=self._text(
                "Minimize to System Tray",
                "التصغير بجانب الساعة",
            ),
            description=self._text(
                (
                    "Keep the application running in the "
                    "notification area instead of exiting."
                ),
                (
                    "إبقاء البرنامج يعمل في منطقة "
                    "الإشعارات بدلًا من إغلاقه بالكامل."
                ),
            ),
            control=self.minimize_to_tray_checkbox,
        )

        self.start_minimized_checkbox = QCheckBox(
            self._text(
                "Start Pixel Guardian minimized",
                "تشغيل بيكسل جارديان مصغرًا",
            )
        )

        self.start_minimized_checkbox.setObjectName(
            "settingsCheckBox"
        )

        self._add_control_row(
            layout=layout,
            title=self._text(
                "Start Minimized",
                "التشغيل مصغرًا",
            ),
            description=self._text(
                (
                    "Start the application without opening "
                    "the main window at full size."
                ),
                (
                    "تشغيل البرنامج بدون فتح النافذة "
                    "الرئيسية بالحجم الكامل."
                ),
            ),
            control=self.start_minimized_checkbox,
        )

        self.test_notification_button = QPushButton(
            self._text(
                "Test Notification",
                "اختبار الإشعار",
            )
        )

        self.test_notification_button.setObjectName(
            "secondaryButton"
        )

        self.test_notification_button.setMinimumHeight(
            40
        )

        self.test_notification_button.setMinimumWidth(
            150
        )

        self.test_notification_button.setCursor(
            Qt.CursorShape.PointingHandCursor
        )

        self.test_notification_button.clicked.connect(
            self._test_notification
        )

        self._add_control_row(
            layout=layout,
            title=self._text(
                "Notification Test",
                "اختبار الإشعارات",
            ),
            description=self._text(
                (
                    "Display a test notification using the "
                    "current notification and sound settings."
                ),
                (
                    "عرض إشعار تجريبي باستخدام إعدادات "
                    "الإشعارات والصوت الحالية."
                ),
            ),
            control=self.test_notification_button,
        )

        self.sections_layout.addWidget(
            section
        )

    def _create_scanning_section(self) -> None:
        """إعدادات الفحص التلقائي."""

        section, layout = self._create_section(
            title=self._text(
                "Automatic Scanning",
                "الفحص التلقائي",
            ),
            description=self._text(
                (
                    "Choose which modules should scan "
                    "automatically when opened."
                ),
                (
                    "اختر الوحدات التي تبدأ الفحص "
                    "تلقائيًا عند فتحها."
                ),
            ),
        )

        self.auto_scan_hardware_checkbox = QCheckBox(
            self._text(
                "Scan hardware automatically",
                "فحص معلومات الجهاز تلقائيًا",
            )
        )

        self.auto_scan_hardware_checkbox.setObjectName(
            "settingsCheckBox"
        )

        self._add_control_row(
            layout=layout,
            title=self._text(
                "Hardware Information",
                "معلومات الجهاز",
            ),
            description=self._text(
                (
                    "Read system and hardware details "
                    "when the Hardware page opens."
                ),
                (
                    "قراءة معلومات النظام والقطع عند "
                    "فتح صفحة معلومات الجهاز."
                ),
            ),
            control=self.auto_scan_hardware_checkbox,
        )

        self.auto_scan_games_checkbox = QCheckBox(
            self._text(
                "Scan installed games automatically",
                "فحص الألعاب المثبتة تلقائيًا",
            )
        )

        self.auto_scan_games_checkbox.setObjectName(
            "settingsCheckBox"
        )

        self._add_control_row(
            layout=layout,
            title=self._text(
                "Game Library",
                "مكتبة الألعاب",
            ),
            description=self._text(
                (
                    "Scan Steam and Epic Games when "
                    "Game Lab opens."
                ),
                (
                    "فحص ألعاب Steam وEpic Games عند "
                    "فتح مختبر الألعاب."
                ),
            ),
            control=self.auto_scan_games_checkbox,
        )

        self.auto_scan_readiness_checkbox = QCheckBox(
            self._text(
                "Scan gaming readiness automatically",
                "فحص جاهزية الألعاب تلقائيًا",
            )
        )

        self.auto_scan_readiness_checkbox.setObjectName(
            "settingsCheckBox"
        )

        self._add_control_row(
            layout=layout,
            title=self._text(
                "Gaming Readiness",
                "جاهزية الألعاب",
            ),
            description=self._text(
                (
                    "Read Windows gaming settings "
                    "when Game Lab opens."
                ),
                (
                    "قراءة إعدادات ويندوز المتعلقة "
                    "بالألعاب عند فتح مختبر الألعاب."
                ),
            ),
            control=self.auto_scan_readiness_checkbox,
        )

        self.sections_layout.addWidget(
            section
        )

    def _create_monitoring_section(self) -> None:
        """إعدادات المراقبة المباشرة."""

        section, layout = self._create_section(
            title=self._text(
                "Live Monitoring",
                "المراقبة المباشرة",
            ),
            description=self._text(
                (
                    "Configure how frequently live system "
                    "information is refreshed."
                ),
                (
                    "حدد سرعة تحديث معلومات النظام "
                    "المباشرة."
                ),
            ),
        )

        self.refresh_interval_combo = QComboBox()

        self.refresh_interval_combo.setObjectName(
            "settingsComboBox"
        )

        self.refresh_interval_combo.setMinimumWidth(
            190
        )

        self.refresh_interval_combo.setMinimumHeight(
            38
        )

        self.refresh_interval_combo.addItem(
            self._text(
                "Every 0.5 seconds",
                "كل نصف ثانية",
            ),
            500,
        )

        self.refresh_interval_combo.addItem(
            self._text(
                "Every 1 second",
                "كل ثانية",
            ),
            1000,
        )

        self.refresh_interval_combo.addItem(
            self._text(
                "Every 2 seconds",
                "كل ثانيتين",
            ),
            2000,
        )

        self.refresh_interval_combo.addItem(
            self._text(
                "Every 5 seconds",
                "كل 5 ثوانٍ",
            ),
            5000,
        )

        self._add_control_row(
            layout=layout,
            title=self._text(
                "Refresh Interval",
                "سرعة التحديث",
            ),
            description=self._text(
                (
                    "Lower intervals update information more "
                    "frequently but use slightly more resources."
                ),
                (
                    "الفترات الأقصر تحدث المعلومات بشكل "
                    "أسرع لكنها تستهلك موارد أكثر قليلًا."
                ),
            ),
            control=self.refresh_interval_combo,
        )

        self.sections_layout.addWidget(
            section
        )

    def _create_gaming_section(self) -> None:
        """إعدادات بيانات أداء الألعاب."""

        section, layout = self._create_section(
            title=self._text(
                "Gaming Performance",
                "أداء الألعاب",
            ),
            description=self._text(
                (
                    "Manage online performance requests "
                    "and locally cached FPS results."
                ),
                (
                    "أدر طلبات أداء الألعاب عبر الإنترنت "
                    "ونتائج FPS المحفوظة محليًا."
                ),
            ),
        )

        self.allow_online_performance_checkbox = QCheckBox(
            self._text(
                (
                    "Allow online gaming performance "
                    "requests"
                ),
                (
                    "السماح بطلب نتائج أداء الألعاب "
                    "عبر الإنترنت"
                ),
            )
        )

        self.allow_online_performance_checkbox.setObjectName(
            "settingsCheckBox"
        )

        self._add_control_row(
            layout=layout,
            title=self._text(
                "Online FPS Estimates",
                "تقديرات FPS عبر الإنترنت",
            ),
            description=self._text(
                (
                    "Allow Pixel Guardian to send the detected "
                    "CPU, GPU, game, resolution and preset "
                    "to the selected FPS provider."
                ),
                (
                    "السماح بإرسال اسم المعالج وكرت الشاشة "
                    "واللعبة والدقة والإعداد إلى مزود FPS "
                    "المختار."
                ),
            ),
            control=self.allow_online_performance_checkbox,
        )

        self.cache_days_combo = QComboBox()

        self.cache_days_combo.setObjectName(
            "settingsComboBox"
        )

        self.cache_days_combo.setMinimumWidth(
            190
        )

        self.cache_days_combo.setMinimumHeight(
            38
        )

        for days in (7, 14, 30, 60, 90):
            self.cache_days_combo.addItem(
                self._text(
                    f"{days} days",
                    f"{days} يوم",
                ),
                days,
            )

        self._add_control_row(
            layout=layout,
            title=self._text(
                "FPS Cache Lifetime",
                "مدة حفظ نتائج FPS",
            ),
            description=self._text(
                (
                    "Choose how long online gaming "
                    "performance results remain cached."
                ),
                (
                    "اختر مدة الاحتفاظ بنتائج أداء "
                    "الألعاب المحفوظة."
                ),
            ),
            control=self.cache_days_combo,
        )

        self.sections_layout.addWidget(
            section
        )

    def _create_maintenance_section(self) -> None:
        """إعدادات الأمان والتنظيف."""

        section, layout = self._create_section(
            title=self._text(
                "Maintenance and Safety",
                "الصيانة والأمان",
            ),
            description=self._text(
                (
                    "Manage safety behavior for system "
                    "maintenance operations."
                ),
                (
                    "تحكم بإجراءات الأمان الخاصة بعمليات "
                    "صيانة النظام."
                ),
            ),
        )

        self.confirm_cleanup_checkbox = QCheckBox(
            self._text(
                (
                    "Require confirmation before "
                    "cleaning files"
                ),
                (
                    "طلب تأكيد قبل تنظيف الملفات"
                ),
            )
        )

        self.confirm_cleanup_checkbox.setObjectName(
            "settingsCheckBox"
        )

        self._add_control_row(
            layout=layout,
            title=self._text(
                "Cleanup Confirmation",
                "تأكيد التنظيف",
            ),
            description=self._text(
                (
                    "Display a confirmation window before "
                    "Cleaner deletes selected files."
                ),
                (
                    "عرض نافذة تأكيد قبل حذف الملفات "
                    "المحددة بواسطة أداة التنظيف."
                ),
            ),
            control=self.confirm_cleanup_checkbox,
        )

        self.sections_layout.addWidget(
            section
        )

    def _create_storage_section(self) -> None:
        """إدارة ملفات البرنامج المحلية."""

        section, layout = self._create_section(
            title=self._text(
                "Application Data",
                "بيانات البرنامج",
            ),
            description=self._text(
                (
                    "Open locally stored data or clear "
                    "temporary gaming performance results."
                ),
                (
                    "افتح البيانات المحفوظة محليًا أو "
                    "احذف نتائج أداء الألعاب المؤقتة."
                ),
            ),
        )

        open_data_button = QPushButton(
            self._text(
                "Open App Data",
                "فتح بيانات البرنامج",
            )
        )

        open_data_button.setObjectName(
            "secondaryButton"
        )

        open_data_button.setMinimumHeight(
            40
        )

        open_data_button.setCursor(
            Qt.CursorShape.PointingHandCursor
        )

        open_data_button.clicked.connect(
            self._open_app_data_folder
        )

        self._add_control_row(
            layout=layout,
            title=self._text(
                "Pixel Guardian Data",
                "بيانات بيكسل جارديان",
            ),
            description=str(
                self.settings_path.parent
            ),
            control=open_data_button,
        )

        open_logs_button = QPushButton(
            self._text(
                "Open Logs",
                "فتح السجلات",
            )
        )

        open_logs_button.setObjectName(
            "secondaryButton"
        )

        open_logs_button.setMinimumHeight(
            40
        )

        open_logs_button.setCursor(
            Qt.CursorShape.PointingHandCursor
        )

        open_logs_button.clicked.connect(
            self._open_logs_folder
        )

        self._add_control_row(
            layout=layout,
            title=self._text(
                "Application Logs",
                "سجلات البرنامج",
            ),
            description=self._text(
                (
                    "Open the folder containing Pixel "
                    "Guardian diagnostic logs."
                ),
                (
                    "فتح المجلد الذي يحتوي على سجلات "
                    "تشخيص بيكسل جارديان."
                ),
            ),
            control=open_logs_button,
        )

        clear_cache_button = QPushButton(
            self._text(
                "Clear FPS Cache",
                "حذف كاش FPS",
            )
        )

        clear_cache_button.setObjectName(
            "dangerButton"
        )

        clear_cache_button.setMinimumHeight(
            40
        )

        clear_cache_button.setCursor(
            Qt.CursorShape.PointingHandCursor
        )

        clear_cache_button.clicked.connect(
            self._clear_gaming_cache
        )

        self._add_control_row(
            layout=layout,
            title=self._text(
                "Gaming Performance Cache",
                "كاش أداء الألعاب",
            ),
            description=self._text(
                (
                    "Delete locally saved FPS estimates. "
                    "This does not remove installed games."
                ),
                (
                    "حذف تقديرات FPS المحفوظة محليًا. "
                    "هذا لا يحذف الألعاب المثبتة."
                ),
            ),
            control=clear_cache_button,
        )

        self.sections_layout.addWidget(
            section
        )

    def _create_section(
        self,
        title: str,
        description: str,
    ) -> tuple[QFrame, QVBoxLayout]:
        """إنشاء بطاقة إعدادات."""

        section = QFrame()

        section.setObjectName(
            "settingsSection"
        )

        layout = QVBoxLayout(
            section
        )

        layout.setContentsMargins(
            24,
            22,
            24,
            22,
        )

        layout.setSpacing(
            14
        )

        title_label = QLabel(
            title
        )

        title_label.setObjectName(
            "settingsSectionTitle"
        )

        description_label = QLabel(
            description
        )

        description_label.setObjectName(
            "settingsSectionDescription"
        )

        description_label.setWordWrap(
            True
        )

        layout.addWidget(
            title_label
        )

        layout.addWidget(
            description_label
        )

        return section, layout

    def _add_control_row(
        self,
        layout: QVBoxLayout,
        title: str,
        description: str,
        control: QWidget,
    ) -> None:
        """إضافة صف إعداد داخل البطاقة."""

        row = QFrame()

        row.setObjectName(
            "settingsRow"
        )

        row_layout = QHBoxLayout(
            row
        )

        row_layout.setContentsMargins(
            16,
            14,
            16,
            14,
        )

        row_layout.setSpacing(
            20
        )

        text_layout = QVBoxLayout()

        text_layout.setContentsMargins(
            0,
            0,
            0,
            0,
        )

        text_layout.setSpacing(
            4
        )

        title_label = QLabel(
            title
        )

        title_label.setObjectName(
            "settingsRowTitle"
        )

        description_label = QLabel(
            description
        )

        description_label.setObjectName(
            "settingsRowDescription"
        )

        description_label.setWordWrap(
            True
        )

        text_layout.addWidget(
            title_label
        )

        text_layout.addWidget(
            description_label
        )

        row_layout.addLayout(
            text_layout,
            1,
        )

        row_layout.addWidget(
            control,
            0,
            Qt.AlignmentFlag.AlignVCenter,
        )

        layout.addWidget(
            row
        )

    def _create_footer(
        self,
        main_layout: QVBoxLayout,
    ) -> None:
        """إنشاء أزرار الحفظ والاستعادة."""

        footer = QFrame()

        footer.setObjectName(
            "settingsFooter"
        )

        footer_layout = QHBoxLayout(
            footer
        )

        footer_layout.setContentsMargins(
            18,
            14,
            18,
            14,
        )

        footer_layout.setSpacing(
            12
        )

        self.status_label = QLabel(
            self._text(
                "Settings are stored locally.",
                "يتم حفظ الإعدادات محليًا.",
            )
        )

        self.status_label.setObjectName(
            "settingsStatusLabel"
        )

        self.status_label.setWordWrap(
            True
        )

        self.reset_button = QPushButton(
            self._text(
                "Restore Defaults",
                "استعادة الافتراضي",
            )
        )

        self.reset_button.setObjectName(
            "secondaryButton"
        )

        self.reset_button.setMinimumHeight(
            42
        )

        self.reset_button.setCursor(
            Qt.CursorShape.PointingHandCursor
        )

        self.reset_button.clicked.connect(
            self._restore_defaults
        )

        self.save_button = QPushButton(
            self._text(
                "Save Settings",
                "حفظ الإعدادات",
            )
        )

        self.save_button.setObjectName(
            "refreshButton"
        )

        self.save_button.setMinimumHeight(
            42
        )

        self.save_button.setMinimumWidth(
            140
        )

        self.save_button.setCursor(
            Qt.CursorShape.PointingHandCursor
        )

        self.save_button.clicked.connect(
            self._save_settings
        )

        footer_layout.addWidget(
            self.status_label,
            1,
        )

        footer_layout.addWidget(
            self.reset_button
        )

        footer_layout.addWidget(
            self.save_button
        )

        main_layout.addWidget(
            footer
        )

    def _load_settings(self) -> None:
        """تحميل الإعدادات المحفوظة."""

        language_index = self.language_combo.findData(
            self.settings_service.language
        )

        self.language_combo.setCurrentIndex(
            max(
                0,
                language_index,
            )
        )

        self.restore_last_page_checkbox.setChecked(
            self.settings_service.get_bool(
                "general/restore_last_page"
            )
        )

        self.notifications_enabled_checkbox.setChecked(
            self.settings_service.get_bool(
                "notifications/enabled"
            )
        )

        self.notification_sound_checkbox.setChecked(
            self.settings_service.get_bool(
                "notifications/sound_enabled"
            )
        )

        self.minimize_to_tray_checkbox.setChecked(
            self.settings_service.get_bool(
                "notifications/minimize_to_tray"
            )
        )

        self.start_minimized_checkbox.setChecked(
            self.settings_service.get_bool(
                "notifications/start_minimized"
            )
        )

        self.auto_scan_hardware_checkbox.setChecked(
            self.settings_service.get_bool(
                "scanning/auto_scan_hardware"
            )
        )

        self.auto_scan_games_checkbox.setChecked(
            self.settings_service.get_bool(
                "scanning/auto_scan_game_library"
            )
        )

        self.auto_scan_readiness_checkbox.setChecked(
            self.settings_service.get_bool(
                "scanning/auto_scan_game_readiness"
            )
        )

        self.confirm_cleanup_checkbox.setChecked(
            self.settings_service.get_bool(
                "maintenance/confirm_before_cleanup"
            )
        )

        self.allow_online_performance_checkbox.setChecked(
            self.settings_service.get_bool(
                "gaming/allow_online_performance"
            )
        )

        refresh_interval = (
            self.settings_service.get_int(
                "monitoring/refresh_interval_ms"
            )
        )

        refresh_index = (
            self.refresh_interval_combo.findData(
                refresh_interval
            )
        )

        self.refresh_interval_combo.setCurrentIndex(
            max(
                0,
                refresh_index,
            )
        )

        cache_days = self.settings_service.get_int(
            "gaming/cache_days"
        )

        cache_index = self.cache_days_combo.findData(
            cache_days
        )

        self.cache_days_combo.setCurrentIndex(
            max(
                0,
                cache_index,
            )
        )

        self._update_notification_controls()

        self.status_label.setText(
            self._text(
                "Settings loaded successfully.",
                "تم تحميل الإعدادات بنجاح.",
            )
        )

    def _save_settings(
        self,
        _checked: bool = False,
        show_message: bool = True,
    ) -> None:
        """حفظ الإعدادات داخل AppData."""

        selected_language = str(
            self.language_combo.currentData()
            or "en"
        )

        language_changed = (
            selected_language
            != self.current_language
        )

        values = {
            "general/language": selected_language,
            "general/restore_last_page": (
                self.restore_last_page_checkbox.isChecked()
            ),
            "notifications/enabled": (
                self.notifications_enabled_checkbox.isChecked()
            ),
            "notifications/sound_enabled": (
                self.notification_sound_checkbox.isChecked()
            ),
            "notifications/minimize_to_tray": (
                self.minimize_to_tray_checkbox.isChecked()
            ),
            "notifications/start_minimized": (
                self.start_minimized_checkbox.isChecked()
            ),
            "scanning/auto_scan_hardware": (
                self.auto_scan_hardware_checkbox.isChecked()
            ),
            "scanning/auto_scan_game_library": (
                self.auto_scan_games_checkbox.isChecked()
            ),
            "scanning/auto_scan_game_readiness": (
                self.auto_scan_readiness_checkbox.isChecked()
            ),
            "monitoring/refresh_interval_ms": int(
                self.refresh_interval_combo.currentData()
            ),
            "maintenance/confirm_before_cleanup": (
                self.confirm_cleanup_checkbox.isChecked()
            ),
            "gaming/allow_online_performance": (
                self.allow_online_performance_checkbox.isChecked()
            ),
            "gaming/cache_days": int(
                self.cache_days_combo.currentData()
            ),
        }

        try:
            self.settings_service.set_values(
                values
            )

        except Exception as error:
            self.status_label.setText(
                self._text(
                    "Settings could not be saved.",
                    "تعذر حفظ الإعدادات.",
                )
            )

            QMessageBox.warning(
                self,
                self._text(
                    "Settings",
                    "الإعدادات",
                ),
                self._text(
                    (
                        "Pixel Guardian could not save "
                        "the settings file."
                    ),
                    (
                        "تعذر على بيكسل جارديان حفظ "
                        "ملف الإعدادات."
                    ),
                )
                + f"\n\n{error}",
            )

            return

        self.status_label.setText(
            self._text(
                "Settings saved successfully.",
                "تم حفظ الإعدادات بنجاح.",
            )
        )

        if not show_message:
            return

        message = self._text(
            (
                "Pixel Guardian settings were saved "
                "successfully."
            ),
            (
                "تم حفظ إعدادات بيكسل جارديان "
                "بنجاح."
            ),
        )

        if language_changed:
            message += "\n\n" + self._text(
                (
                    "Restart Pixel Guardian to apply "
                    "the selected language to every page."
                ),
                (
                    "أعد تشغيل بيكسل جارديان لتطبيق "
                    "اللغة المختارة على جميع الصفحات."
                ),
            )

        QMessageBox.information(
            self,
            self._text(
                "Settings",
                "الإعدادات",
            ),
            message,
        )

    def _restore_defaults(
        self,
        _checked: bool = False,
    ) -> None:
        """استعادة الإعدادات الافتراضية."""

        answer = QMessageBox.question(
            self,
            self._text(
                "Restore Default Settings",
                "استعادة الإعدادات الافتراضية",
            ),
            self._text(
                (
                    "Restore all Pixel Guardian settings "
                    "to their default values?"
                ),
                (
                    "هل تريد استعادة جميع إعدادات "
                    "بيكسل جارديان إلى القيم الافتراضية؟"
                ),
            ),
            (
                QMessageBox.StandardButton.Yes
                | QMessageBox.StandardButton.No
            ),
            QMessageBox.StandardButton.No,
        )

        if answer != QMessageBox.StandardButton.Yes:
            return

        try:
            self.settings_service.restore_defaults()

        except Exception as error:
            QMessageBox.warning(
                self,
                self._text(
                    "Settings",
                    "الإعدادات",
                ),
                self._text(
                    (
                        "Default settings could not "
                        "be restored."
                    ),
                    (
                        "تعذر استعادة الإعدادات "
                        "الافتراضية."
                    ),
                )
                + f"\n\n{error}",
            )

            return

        self._load_settings()

        self.status_label.setText(
            self._text(
                "Default settings were restored.",
                "تمت استعادة الإعدادات الافتراضية.",
            )
        )

        QMessageBox.information(
            self,
            self._text(
                "Settings",
                "الإعدادات",
            ),
            self._text(
                (
                    "Default settings were restored. "
                    "Restart Pixel Guardian to apply "
                    "the default language."
                ),
                (
                    "تمت استعادة الإعدادات الافتراضية. "
                    "أعد تشغيل بيكسل جارديان لتطبيق "
                    "اللغة الافتراضية."
                ),
            ),
        )

    def _update_notification_controls(
        self,
        _checked: bool | None = None,
    ) -> None:
        """تفعيل خيار الصوت حسب حالة الإشعارات."""

        notifications_enabled = (
            self.notifications_enabled_checkbox.isChecked()
        )

        self.notification_sound_checkbox.setEnabled(
            notifications_enabled
        )

    def _connect_live_notification_settings(
        self,
    ) -> None:
        """تطبيق إعدادات الإشعارات مباشرة عند تغييرها."""

        controls = (
            self.notifications_enabled_checkbox,
            self.notification_sound_checkbox,
            self.minimize_to_tray_checkbox,
            self.start_minimized_checkbox,
        )

        for control in controls:
            control.toggled.connect(
                self._apply_notification_settings_live
            )

    def _apply_notification_settings_live(
        self,
        _checked: bool | None = None,
    ) -> bool:
        """حفظ إعدادات الإشعارات الحالية فورًا."""

        notification_values = {
            "notifications/enabled": (
                self.notifications_enabled_checkbox.isChecked()
            ),
            "notifications/sound_enabled": (
                self.notification_sound_checkbox.isChecked()
            ),
            "notifications/minimize_to_tray": (
                self.minimize_to_tray_checkbox.isChecked()
            ),
            "notifications/start_minimized": (
                self.start_minimized_checkbox.isChecked()
            ),
        }

        try:
            self.settings_service.set_values(
                notification_values
            )

        except Exception as error:
            self.status_label.setText(
                self._text(
                    "Notification settings could not be applied.",
                    "تعذر تطبيق إعدادات الإشعارات.",
                )
            )

            QMessageBox.warning(
                self,
                self._text(
                    "Notifications",
                    "الإشعارات",
                ),
                self._text(
                    (
                        "Pixel Guardian could not save "
                        "the notification settings."
                    ),
                    (
                        "تعذر على بيكسل جارديان حفظ "
                        "إعدادات الإشعارات."
                    ),
                )
                + f"\n\n{error}",
            )

            return False

        tray_icon = getattr(
            self.application,
            "system_tray_icon",
            None,
        )

        tray_available = bool(
            tray_icon is not None
            and tray_icon.isVisible()
        )

        self.application.setQuitOnLastWindowClosed(
            not (
                notification_values[
                    "notifications/minimize_to_tray"
                ]
                and tray_available
            )
        )

        self._update_notification_controls()

        self.status_label.setText(
            self._text(
                "Notification settings applied immediately.",
                "تم تطبيق إعدادات الإشعارات مباشرة.",
            )
        )

        return True

    def _test_notification(
        self,
        _checked: bool = False,
    ) -> None:
        """إرسال إشعار تجريبي باستخدام الإعدادات الحالية."""

        if not self.notifications_enabled_checkbox.isChecked():
            QMessageBox.information(
                self,
                self._text(
                    "Notification Test",
                    "اختبار الإشعارات",
                ),
                self._text(
                    "Windows notifications are currently disabled.",
                    "إشعارات ويندوز متوقفة حاليًا.",
                ),
            )
            return

        if not self._apply_notification_settings_live():
            return

        tray_icon = getattr(
            self.application,
            "system_tray_icon",
            None,
        )

        if (
            tray_icon is None
            or not tray_icon.isVisible()
        ):
            QMessageBox.warning(
                self,
                self._text(
                    "Notification Test",
                    "اختبار الإشعارات",
                ),
                self._text(
                    (
                        "System Tray is unavailable. Restart "
                        "Pixel Guardian and try again."
                    ),
                    (
                        "أيقونة البرنامج بجانب الساعة غير متاحة. "
                        "أعد تشغيل بيكسل جارديان ثم جرّب مجددًا."
                    ),
                ),
            )
            return

        notification_service = getattr(
            self.application,
            "notification_service",
            None,
        )

        if notification_service is None:
            QMessageBox.warning(
                self,
                self._text(
                    "Notification Test",
                    "اختبار الإشعارات",
                ),
                self._text(
                    "The notification service was not initialized.",
                    "لم تتم تهيئة خدمة الإشعارات.",
                ),
            )
            return

        notification_sent = notification_service.info(
            title_en="Pixel Guardian Notification Test",
            title_ar="اختبار إشعارات بيكسل جارديان",
            message_en=(
                "Notifications are working correctly. "
                "The sound follows your current setting."
            ),
            message_ar=(
                "الإشعارات تعمل بشكل صحيح. "
                "الصوت يتبع إعدادك الحالي."
            ),
            duration_ms=5000,
        )

        if notification_sent:
            self.status_label.setText(
                self._text(
                    "Test notification sent successfully.",
                    "تم إرسال الإشعار التجريبي بنجاح.",
                )
            )
            return

        QMessageBox.warning(
            self,
            self._text(
                "Notification Test",
                "اختبار الإشعارات",
            ),
            self._text(
                "The test notification could not be displayed.",
                "تعذر عرض الإشعار التجريبي.",
            ),
        )

    def _open_app_data_folder(
        self,
        _checked: bool = False,
    ) -> None:
        """فتح مجلد بيانات Pixel Guardian."""

        self._open_folder(
            self.settings_path.parent,
            self._text(
                "Application Data",
                "بيانات البرنامج",
            ),
        )

    def _open_logs_folder(
        self,
        _checked: bool = False,
    ) -> None:
        """فتح مجلد السجلات."""

        logs_path = (
            self.settings_path.parent
            / "logs"
        )

        logs_path.mkdir(
            parents=True,
            exist_ok=True,
        )

        self._open_folder(
            logs_path,
            self._text(
                "Application Logs",
                "سجلات البرنامج",
            ),
        )

    def _clear_gaming_cache(
        self,
        _checked: bool = False,
    ) -> None:
        """حذف كاش نتائج FPS."""

        answer = QMessageBox.question(
            self,
            self._text(
                "Clear Gaming Performance Cache",
                "حذف كاش أداء الألعاب",
            ),
            self._text(
                (
                    "Delete all locally cached "
                    "FPS results?"
                ),
                (
                    "هل تريد حذف جميع نتائج FPS "
                    "المحفوظة محليًا؟"
                ),
            ),
            (
                QMessageBox.StandardButton.Yes
                | QMessageBox.StandardButton.No
            ),
            QMessageBox.StandardButton.No,
        )

        if answer != QMessageBox.StandardButton.Yes:
            return

        try:
            from core.services.gaming_performance_cache_service import (
                GamingPerformanceCacheService,
            )

            GamingPerformanceCacheService().clear()

        except Exception as error:
            self.status_label.setText(
                self._text(
                    (
                        "Gaming performance cache "
                        "could not be cleared."
                    ),
                    (
                        "تعذر حذف كاش أداء الألعاب."
                    ),
                )
            )

            QMessageBox.warning(
                self,
                self._text(
                    "Gaming Performance Cache",
                    "كاش أداء الألعاب",
                ),
                self._text(
                    (
                        "The gaming performance cache "
                        "could not be cleared."
                    ),
                    (
                        "تعذر حذف كاش أداء الألعاب."
                    ),
                )
                + f"\n\n{error}",
            )

            return

        self.status_label.setText(
            self._text(
                "Gaming performance cache cleared.",
                "تم حذف كاش أداء الألعاب.",
            )
        )

        QMessageBox.information(
            self,
            self._text(
                "Gaming Performance Cache",
                "كاش أداء الألعاب",
            ),
            self._text(
                (
                    "All cached FPS results "
                    "were deleted."
                ),
                (
                    "تم حذف جميع نتائج FPS "
                    "المحفوظة."
                ),
            ),
        )

    def _open_folder(
        self,
        path: Path,
        title: str,
    ) -> None:
        """فتح مجلد باستخدام Windows Explorer."""

        try:
            path.mkdir(
                parents=True,
                exist_ok=True,
            )

            os.startfile(
                str(path)
            )

        except OSError as error:
            QMessageBox.warning(
                self,
                title,
                self._text(
                    (
                        "The folder could not "
                        "be opened."
                    ),
                    (
                        "تعذر فتح المجلد."
                    ),
                )
                + f"\n\n{error}",
            )

    def _text(
        self,
        english: str,
        arabic: str,
    ) -> str:
        """اختيار النص حسب لغة البرنامج الحالية."""

        if self.current_language == "ar":
            return arabic

        return english