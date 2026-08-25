from __future__ import annotations

from PySide6.QtCore import (
    Qt,
    Signal,
)
from PySide6.QtWidgets import (
    QApplication,
    QFrame,
    QLabel,
    QPushButton,
    QVBoxLayout,
)

from core.services.localization_service import (
    LocalizationService,
)


class Sidebar(QFrame):
    """القائمة الجانبية لبرنامج Pixel Guardian."""

    page_selected = Signal(str)

    def __init__(self) -> None:
        super().__init__()

        application = QApplication.instance()

        if application is None:
            raise RuntimeError(
                "QApplication has not been initialized."
            )

        self.localization = getattr(
            application,
            "localization_service",
            LocalizationService(),
        )

        self.is_rtl = self.localization.is_rtl

        self.setObjectName(
            "sidebar"
        )

        self.setProperty(
            "rtl",
            self.is_rtl,
        )

        self.setFixedWidth(
            240
        )

        self.setLayoutDirection(
            Qt.LayoutDirection.RightToLeft
            if self.is_rtl
            else Qt.LayoutDirection.LeftToRight
        )

        self._setup_ui()

    def _setup_ui(self) -> None:
        """إنشاء عناصر القائمة الجانبية."""

        layout = QVBoxLayout(
            self
        )

        layout.setContentsMargins(
            18,
            25,
            18,
            25,
        )

        layout.setSpacing(
            10
        )

        brand_title = QLabel(
            "PIXEL"
        )

        brand_title.setObjectName(
            "brandTitle"
        )

        brand_subtitle = QLabel(
            "GUARDIAN"
        )

        brand_subtitle.setObjectName(
            "brandSubtitle"
        )

        brand_alignment = (
            Qt.AlignmentFlag.AlignRight
            if self.is_rtl
            else Qt.AlignmentFlag.AlignLeft
        )

        brand_title.setAlignment(
            brand_alignment
        )

        brand_subtitle.setAlignment(
            brand_alignment
        )

        self.dashboard_button = (
            self._create_navigation_button(
                text=self.localization.tr(
                    "dashboard"
                ),
                page_name="dashboard",
                checked=True,
            )
        )

        self.hardware_button = (
            self._create_navigation_button(
                text=self.localization.tr(
                    "hardware_information"
                ),
                page_name="hardware",
            )
        )

        self.live_monitor_button = (
            self._create_navigation_button(
                text=self.localization.tr(
                    "live_monitor"
                ),
                page_name="live_monitor",
            )
        )

        self.disk_health_button = (
            self._create_navigation_button(
                text=self.localization.tr(
                    "disk_health"
                ),
                page_name="disk_health",
            )
        )

        self.drivers_button = (
            self._create_navigation_button(
                text=self.localization.tr(
                    "drivers"
                ),
                page_name="drivers",
            )
        )

        self.cleaner_button = (
            self._create_navigation_button(
                text=self.localization.tr(
                    "cleaner"
                ),
                page_name="cleaner",
            )
        )

        self.game_lab_button = (
            self._create_navigation_button(
                text=self.localization.tr(
                    "game_lab"
                ),
                page_name="game_lab",
            )
        )

        self.settings_button = (
            self._create_navigation_button(
                text=self.localization.tr(
                    "settings"
                ),
                page_name="settings",
            )
        )

        self.about_button = (
            self._create_navigation_button(
                text=self._text(
                    "About",
                    "حول البرنامج",
                ),
                page_name="about",
            )
        )

        version_label = QLabel(
            self._text(
                "Version 1.0.0",
                "الإصدار 1.0.0",
            )
        )

        version_label.setObjectName(
            "versionLabel"
        )

        version_label.setAlignment(
            brand_alignment
        )

        layout.addWidget(
            brand_title
        )

        layout.addWidget(
            brand_subtitle
        )

        layout.addSpacing(
            30
        )

        layout.addWidget(
            self.dashboard_button
        )

        layout.addWidget(
            self.hardware_button
        )

        layout.addWidget(
            self.live_monitor_button
        )

        layout.addWidget(
            self.disk_health_button
        )

        layout.addWidget(
            self.drivers_button
        )

        layout.addWidget(
            self.cleaner_button
        )

        layout.addWidget(
            self.game_lab_button
        )

        layout.addWidget(
            self.settings_button
        )

        layout.addWidget(
            self.about_button
        )

        layout.addStretch()

        layout.addWidget(
            version_label
        )

    def _create_navigation_button(
        self,
        text: str,
        page_name: str,
        checked: bool = False,
    ) -> QPushButton:
        """إنشاء زر تنقل موحد."""

        button = QPushButton(
            text
        )

        button.setObjectName(
            "navigationButton"
        )

        button.setProperty(
            "rtl",
            self.is_rtl,
        )

        button.setLayoutDirection(
            Qt.LayoutDirection.RightToLeft
            if self.is_rtl
            else Qt.LayoutDirection.LeftToRight
        )

        button.setCheckable(
            True
        )

        button.setChecked(
            checked
        )

        button.setMinimumHeight(
            48
        )

        button.setCursor(
            Qt.CursorShape.PointingHandCursor
        )

        button.clicked.connect(
            lambda _checked=False, name=page_name:
            self._select_page(
                name
            )
        )

        return button

    def _select_page(
        self,
        page_name: str,
    ) -> None:
        """اختيار الصفحة وإرسال اسمها."""

        self.set_active_page(
            page_name
        )

        self.page_selected.emit(
            page_name
        )

    def set_active_page(
        self,
        page_name: str,
    ) -> None:
        """تحديد زر الصفحة النشطة."""

        buttons = {
            "dashboard": (
                self.dashboard_button
            ),
            "hardware": (
                self.hardware_button
            ),
            "live_monitor": (
                self.live_monitor_button
            ),
            "disk_health": (
                self.disk_health_button
            ),
            "drivers": (
                self.drivers_button
            ),
            "cleaner": (
                self.cleaner_button
            ),
            "game_lab": (
                self.game_lab_button
            ),
            "settings": (
                self.settings_button
            ),
            "about": (
                self.about_button
            ),
        }

        for name, button in buttons.items():
            button.setChecked(
                name == page_name
            )

    def _text(
        self,
        english: str,
        arabic: str,
    ) -> str:
        """اختيار النص حسب اللغة الحالية."""

        if self.is_rtl:
            return arabic

        return english