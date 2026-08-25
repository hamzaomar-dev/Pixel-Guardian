from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QApplication,
    QFrame,
    QGridLayout,
    QLabel,
    QVBoxLayout,
    QWidget,
)

from core.services.application_settings_service import (
    ApplicationSettingsService,
)
from core.services.localization_service import (
    LocalizationService,
)


class AboutPage(QWidget):
    """صفحة معلومات برنامج Pixel Guardian."""

    APP_NAME = "Pixel Guardian"
    APP_VERSION = "1.0.0"
    DEVELOPER_NAME = "Hamza Omar"

    def __init__(self) -> None:
        super().__init__()

        application = QApplication.instance()

        if application is None:
            raise RuntimeError(
                "QApplication has not been initialized."
            )

        self.settings_service = getattr(
            application,
            "settings_service",
            None,
        )

        if self.settings_service is None:
            self.settings_service = (
                ApplicationSettingsService()
            )

        self.localization = getattr(
            application,
            "localization_service",
            None,
        )

        if self.localization is None:
            self.localization = LocalizationService(
                settings_service=self.settings_service
            )

        self.is_rtl = self.localization.is_rtl

        self.setObjectName(
            "page"
        )

        self.setLayoutDirection(
            Qt.LayoutDirection.RightToLeft
            if self.is_rtl
            else Qt.LayoutDirection.LeftToRight
        )

        self._setup_ui()

    def _setup_ui(self) -> None:
        """إنشاء واجهة صفحة About."""

        page_layout = QVBoxLayout(
            self
        )

        page_layout.setContentsMargins(
            40,
            35,
            40,
            35,
        )

        page_layout.setSpacing(
            18
        )

        title = QLabel(
            self._text(
                "About Pixel Guardian",
                "حول بيكسل جارديان",
            )
        )

        title.setObjectName(
            "pageTitle"
        )

        subtitle = QLabel(
            self._text(
                (
                    "System monitoring, maintenance, "
                    "cleaning, and gaming tools in one app."
                ),
                (
                    "أدوات مراقبة وصيانة وتنظيف "
                    "وتحليل الألعاب في برنامج واحد."
                ),
            )
        )

        subtitle.setObjectName(
            "pageSubtitle"
        )

        subtitle.setWordWrap(
            True
        )

        info_card = QFrame()
        info_card.setObjectName(
            "cleanerSummaryCard"
        )

        info_layout = QGridLayout(
            info_card
        )

        info_layout.setContentsMargins(
            24,
            22,
            24,
            22,
        )

        info_layout.setHorizontalSpacing(
            35
        )

        info_layout.setVerticalSpacing(
            16
        )

        rows = (
            (
                self._text(
                    "Application",
                    "البرنامج",
                ),
                self.APP_NAME,
            ),
            (
                self._text(
                    "Version",
                    "الإصدار",
                ),
                self.APP_VERSION,
            ),
            (
                self._text(
                    "Developer",
                    "المطور",
                ),
                self.DEVELOPER_NAME,
            ),
            (
                self._text(
                    "Platform",
                    "المنصة",
                ),
                "Windows",
            ),
            (
                self._text(
                    "Gaming Data",
                    "بيانات الألعاب",
                ),
                "FPSHQ",
            ),
        )

        for row_index, (
            label_text,
            value_text,
        ) in enumerate(rows):
            label = QLabel(
                label_text
            )

            label.setObjectName(
                "cleanerSummaryTitle"
            )

            value = QLabel(
                value_text
            )

            value.setObjectName(
                "cleanerSummaryValue"
            )

            value.setWordWrap(
                True
            )

            info_layout.addWidget(
                label,
                row_index,
                0,
            )

            info_layout.addWidget(
                value,
                row_index,
                1,
            )

        info_layout.setColumnStretch(
            0,
            1,
        )

        info_layout.setColumnStretch(
            1,
            3,
        )

        features_card = QFrame()
        features_card.setObjectName(
            "cleanerSummaryCard"
        )

        features_layout = QVBoxLayout(
            features_card
        )

        features_layout.setContentsMargins(
            24,
            22,
            24,
            22,
        )

        features_layout.setSpacing(
            10
        )

        features_title = QLabel(
            self._text(
                "Included Modules",
                "الوحدات المتوفرة",
            )
        )

        features_title.setObjectName(
            "cardTitle"
        )

        features_text = QLabel(
            self._text(
                (
                    "Hardware Information • Live Monitor • "
                    "Disk Health • Drivers • Cleaner • "
                    "Game Library • Gaming Readiness • "
                    "Gaming Power"
                ),
                (
                    "معلومات الجهاز • المراقبة المباشرة • "
                    "صحة الأقراص • التعريفات • التنظيف • "
                    "مكتبة الألعاب • جاهزية الألعاب • "
                    "قوة الألعاب"
                ),
            )
        )

        features_text.setObjectName(
            "pageSubtitle"
        )

        features_text.setWordWrap(
            True
        )

        features_layout.addWidget(
            features_title
        )

        features_layout.addWidget(
            features_text
        )

        copyright_label = QLabel(
            self._text(
                (
                    "© 2026 Hamza Omar. "
                    "All rights reserved."
                ),
                (
                    "© 2026 حمزة عمر. "
                    "جميع الحقوق محفوظة."
                ),
            )
        )

        copyright_label.setObjectName(
            "pageSubtitle"
        )

        copyright_label.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        page_layout.addWidget(
            title
        )

        page_layout.addWidget(
            subtitle
        )

        page_layout.addWidget(
            info_card
        )

        page_layout.addWidget(
            features_card
        )

        page_layout.addStretch()

        page_layout.addWidget(
            copyright_label
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