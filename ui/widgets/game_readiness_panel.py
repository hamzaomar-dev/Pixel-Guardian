from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QApplication,
    QFrame,
    QHBoxLayout,
    QLabel,
    QVBoxLayout,
    QWidget,
)

from core.models.game_readiness import (
    GameReadinessReport,
    GamingSettingStatus,
)
from core.services.application_settings_service import (
    ApplicationSettingsService,
)
from core.services.localization_service import (
    LocalizationService,
)


class GameReadinessPanel(QFrame):
    """لوحة عرض تقرير جاهزية Windows للألعاب."""

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
            "cleanerSummaryCard"
        )

        self.setLayoutDirection(
            Qt.LayoutDirection.RightToLeft
            if self.is_rtl
            else Qt.LayoutDirection.LeftToRight
        )

        self._setup_ui()
        self.set_empty()

    def _setup_ui(self) -> None:
        """إنشاء عناصر لوحة الجاهزية."""

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(
            22,
            20,
            22,
            20,
        )
        main_layout.setSpacing(16)

        header_layout = QHBoxLayout()
        header_layout.setSpacing(12)

        title_layout = QVBoxLayout()
        title_layout.setSpacing(4)

        self.title_label = QLabel(
            self._text(
                "Gaming Readiness",
                "جاهزية الألعاب",
            )
        )
        self.title_label.setObjectName(
            "cardTitle"
        )
        self.title_label.setAlignment(
            Qt.AlignmentFlag.AlignLeading
            | Qt.AlignmentFlag.AlignVCenter
        )

        self.description_label = QLabel(
            self._text(
                (
                    "Review Windows settings that may "
                    "affect gaming performance."
                ),
                (
                    "راجع إعدادات ويندوز التي قد تؤثر "
                    "على أداء الألعاب."
                ),
            )
        )
        self.description_label.setObjectName(
            "pageSubtitle"
        )
        self.description_label.setWordWrap(
            True
        )
        self.description_label.setAlignment(
            Qt.AlignmentFlag.AlignLeading
            | Qt.AlignmentFlag.AlignVCenter
        )

        title_layout.addWidget(
            self.title_label
        )
        title_layout.addWidget(
            self.description_label
        )

        self.readiness_label = QLabel(
            "--"
        )
        self.readiness_label.setObjectName(
            "cleanerSummaryValue"
        )
        self.readiness_label.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )
        self.readiness_label.setMinimumWidth(
            120
        )

        header_layout.addLayout(
            title_layout,
            1,
        )
        header_layout.addWidget(
            self.readiness_label
        )

        stats_layout = QHBoxLayout()
        stats_layout.setSpacing(35)

        self.score_value = self._create_stat(
            stats_layout,
            self._text(
                "Readiness Score",
                "نسبة الجاهزية",
            ),
        )

        self.recommended_value = self._create_stat(
            stats_layout,
            self._text(
                "Recommended",
                "موصى به",
            ),
        )

        self.attention_value = self._create_stat(
            stats_layout,
            self._text(
                "Needs Attention",
                "يحتاج إلى انتباه",
            ),
        )

        self.unavailable_value = self._create_stat(
            stats_layout,
            self._text(
                "Unavailable",
                "غير متوفر",
            ),
        )

        stats_layout.addStretch()

        self.settings_container = QWidget()

        self.settings_layout = QVBoxLayout(
            self.settings_container
        )
        self.settings_layout.setContentsMargins(
            0,
            0,
            0,
            0,
        )
        self.settings_layout.setSpacing(
            10
        )

        main_layout.addLayout(
            header_layout
        )
        main_layout.addLayout(
            stats_layout
        )
        main_layout.addWidget(
            self.settings_container
        )

    def set_empty(self) -> None:
        """عرض الحالة الفارغة."""

        self.readiness_label.setText(
            self._text(
                "Not Scanned",
                "لم يتم الفحص",
            )
        )

        self._reset_stat_values()
        self._clear_settings()

        empty_label = QLabel(
            self._text(
                (
                    "Run the gaming readiness scan "
                    "to review Windows settings."
                ),
                (
                    "شغّل فحص جاهزية الألعاب لمراجعة "
                    "إعدادات ويندوز."
                ),
            )
        )
        empty_label.setObjectName(
            "cleanerCategoryDescription"
        )
        empty_label.setWordWrap(
            True
        )
        empty_label.setAlignment(
            Qt.AlignmentFlag.AlignLeading
            | Qt.AlignmentFlag.AlignVCenter
        )

        self.settings_layout.addWidget(
            empty_label
        )

    def set_loading(self) -> None:
        """عرض حالة الفحص."""

        self.readiness_label.setText(
            self._text(
                "Scanning...",
                "جارٍ الفحص...",
            )
        )

        self._reset_stat_values()
        self._clear_settings()

        loading_label = QLabel(
            self._text(
                "Reading Windows gaming settings...",
                "جارٍ قراءة إعدادات الألعاب في ويندوز...",
            )
        )
        loading_label.setObjectName(
            "cleanerCategoryDescription"
        )
        loading_label.setWordWrap(
            True
        )
        loading_label.setAlignment(
            Qt.AlignmentFlag.AlignLeading
            | Qt.AlignmentFlag.AlignVCenter
        )

        self.settings_layout.addWidget(
            loading_label
        )

    def set_report(
        self,
        report: GameReadinessReport,
    ) -> None:
        """عرض تقرير جاهزية الألعاب."""

        self.readiness_label.setText(
            self._translate_dynamic_text(
                report.readiness_label
            )
        )

        self.score_value.setText(
            f"{report.readiness_percentage}%"
        )

        self.recommended_value.setText(
            str(
                report.recommended_settings
            )
        )

        self.attention_value.setText(
            str(
                report.attention_settings
            )
        )

        self.unavailable_value.setText(
            str(
                report.unavailable_settings
            )
        )

        self._clear_settings()

        for setting in report.settings:
            setting_row = (
                self._create_setting_row(
                    setting
                )
            )

            self.settings_layout.addWidget(
                setting_row
            )

        if not report.settings:
            empty_label = QLabel(
                self._text(
                    "No gaming settings were detected.",
                    "لم يتم اكتشاف إعدادات متعلقة بالألعاب.",
                )
            )
            empty_label.setObjectName(
                "cleanerCategoryDescription"
            )
            empty_label.setWordWrap(
                True
            )
            empty_label.setAlignment(
                Qt.AlignmentFlag.AlignLeading
                | Qt.AlignmentFlag.AlignVCenter
            )

            self.settings_layout.addWidget(
                empty_label
            )

    def set_error(
        self,
        message: str,
    ) -> None:
        """عرض خطأ فحص الجاهزية."""

        self.readiness_label.setText(
            self._text(
                "Scan Failed",
                "فشل الفحص",
            )
        )

        self._reset_stat_values()
        self._clear_settings()

        error_label = QLabel(
            self._translate_dynamic_text(
                message
            )
        )
        error_label.setObjectName(
            "cleanerErrorLabel"
        )
        error_label.setWordWrap(
            True
        )
        error_label.setAlignment(
            Qt.AlignmentFlag.AlignLeading
            | Qt.AlignmentFlag.AlignVCenter
        )

        self.settings_layout.addWidget(
            error_label
        )

    def _create_stat(
        self,
        layout: QHBoxLayout,
        title: str,
    ) -> QLabel:
        """إنشاء قيمة إحصائية."""

        container = QWidget()

        container_layout = QVBoxLayout(
            container
        )
        container_layout.setContentsMargins(
            0,
            0,
            0,
            0,
        )
        container_layout.setSpacing(
            3
        )

        title_label = QLabel(
            title
        )
        title_label.setObjectName(
            "cleanerSummaryTitle"
        )
        title_label.setAlignment(
            Qt.AlignmentFlag.AlignLeading
            | Qt.AlignmentFlag.AlignVCenter
        )

        value_label = QLabel(
            "--"
        )
        value_label.setObjectName(
            "cleanerSummaryValue"
        )
        value_label.setAlignment(
            Qt.AlignmentFlag.AlignLeading
            | Qt.AlignmentFlag.AlignVCenter
        )

        container_layout.addWidget(
            title_label
        )
        container_layout.addWidget(
            value_label
        )

        layout.addWidget(
            container
        )

        return value_label

    def _create_setting_row(
        self,
        setting: GamingSettingStatus,
    ) -> QFrame:
        """إنشاء صف لإعداد ألعاب واحد."""

        row = QFrame()
        row.setObjectName(
            "cleanerCategoryCard"
        )

        row.setLayoutDirection(
            Qt.LayoutDirection.RightToLeft
            if self.is_rtl
            else Qt.LayoutDirection.LeftToRight
        )

        if not setting.available:
            status_key = "unavailable"

        elif setting.is_recommended:
            status_key = "recommended"

        else:
            status_key = "attention"

        row.setProperty(
            "readinessStatus",
            status_key,
        )

        row_layout = QHBoxLayout(
            row
        )
        row_layout.setContentsMargins(
            18,
            14,
            18,
            14,
        )
        row_layout.setSpacing(
            15
        )

        information_layout = QVBoxLayout()
        information_layout.setSpacing(
            4
        )

        title_label = QLabel(
            self._translate_dynamic_text(
                setting.title
            )
        )
        title_label.setObjectName(
            "cleanerCategoryTitle"
        )
        title_label.setAlignment(
            Qt.AlignmentFlag.AlignLeading
            | Qt.AlignmentFlag.AlignVCenter
        )

        current_label = QLabel(
            self._text(
                "Current: ",
                "الحالي: ",
            )
            + self._translate_dynamic_text(
                setting.current_value
            )
        )
        current_label.setObjectName(
            "cleanerCategoryDescription"
        )
        current_label.setWordWrap(
            True
        )
        current_label.setAlignment(
            Qt.AlignmentFlag.AlignLeading
            | Qt.AlignmentFlag.AlignVCenter
        )

        recommended_label = QLabel(
            self._text(
                "Recommended: ",
                "الموصى به: ",
            )
            + self._translate_dynamic_text(
                setting.recommended_value
            )
        )
        recommended_label.setObjectName(
            "cleanerCategoryDescription"
        )
        recommended_label.setWordWrap(
            True
        )
        recommended_label.setAlignment(
            Qt.AlignmentFlag.AlignLeading
            | Qt.AlignmentFlag.AlignVCenter
        )

        information_layout.addWidget(
            title_label
        )
        information_layout.addWidget(
            current_label
        )
        information_layout.addWidget(
            recommended_label
        )

        status_label = QLabel(
            self._status_text(
                setting=setting,
                status_key=status_key,
            )
        )
        status_label.setObjectName(
            "cleanerRiskBadge"
        )
        status_label.setProperty(
            "readinessStatus",
            status_key,
        )
        status_label.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )
        status_label.setMinimumWidth(
            145
        )
        status_label.setFixedHeight(
            28
        )
        status_label.setToolTip(
            self._translate_dynamic_text(
                setting.description
            )
        )

        row_layout.addLayout(
            information_layout,
            1,
        )
        row_layout.addWidget(
            status_label
        )

        return row

    def _status_text(
        self,
        setting: GamingSettingStatus,
        status_key: str,
    ) -> str:
        """ترجمة حالة إعداد الجاهزية."""

        translated_status = (
            self._translate_dynamic_text(
                setting.status_text
            )
        )

        if (
            translated_status
            and translated_status.strip()
            and translated_status.strip().casefold()
            != str(setting.status_text).strip().casefold()
        ):
            return translated_status

        if status_key == "recommended":
            return self._text(
                "Recommended",
                "موصى به",
            )

        if status_key == "attention":
            return self._text(
                "Needs Attention",
                "يحتاج إلى انتباه",
            )

        return self._text(
            "Unavailable",
            "غير متوفر",
        )

    def _translate_dynamic_text(
        self,
        value,
    ) -> str:
        """ترجمة النصوص الديناميكية الشائعة القادمة من الخدمة."""

        if value is None:
            return self._text(
                "Unavailable",
                "غير متوفر",
            )

        text = str(value).strip()

        if not text:
            return self._text(
                "Unavailable",
                "غير متوفر",
            )

        if not self.is_rtl:
            return text

        exact_translations = {
            "excellent": "ممتاز",
            "very good": "جيد جدًا",
            "good": "جيد",
            "fair": "مقبول",
            "limited": "محدود",
            "poor": "ضعيف",
            "not ready": "غير جاهز",
            "ready": "جاهز",
            "recommended": "موصى به",
            "needs attention": "يحتاج إلى انتباه",
            "attention required": "يحتاج إلى انتباه",
            "unavailable": "غير متوفر",
            "available": "متوفر",
            "enabled": "مفعّل",
            "disabled": "معطّل",
            "on": "مفعّل",
            "off": "معطّل",
            "yes": "نعم",
            "no": "لا",
            "true": "نعم",
            "false": "لا",
            "unknown": "غير معروف",
            "automatic": "تلقائي",
            "balanced": "متوازن",
            "high performance": "أداء عالٍ",
            "best performance": "أفضل أداء",
            "power saver": "توفير الطاقة",
            "game mode": "وضع الألعاب",
            "hardware-accelerated gpu scheduling": (
                "جدولة المعالج الرسومي المسرّعة بالأجهزة"
            ),
            "hardware accelerated gpu scheduling": (
                "جدولة المعالج الرسومي المسرّعة بالأجهزة"
            ),
            "xbox game bar": "شريط ألعاب Xbox",
            "game bar": "شريط الألعاب",
            "game dvr": "تسجيل الألعاب Game DVR",
            "background recording": "التسجيل في الخلفية",
            "power plan": "خطة الطاقة",
            "windows power plan": "خطة طاقة ويندوز",
            "windows version": "إصدار ويندوز",
            "graphics preference": "تفضيل الرسومات",
            "variable refresh rate": "معدل التحديث المتغير",
            "fullscreen optimizations": "تحسينات ملء الشاشة",
            "focus assist": "مساعد التركيز",
            "memory integrity": "تكامل الذاكرة",
            "core isolation": "عزل النواة",
            "gpu scheduling": "جدولة المعالج الرسومي",
            "gaming services": "خدمات الألعاب",
            "windows game mode": "وضع الألعاب في ويندوز",
            "not supported": "غير مدعوم",
            "supported": "مدعوم",
            "not detected": "لم يتم اكتشافه",
            "not configured": "غير مهيأ",
            "default": "افتراضي",
        }

        exact_result = exact_translations.get(
            text.casefold()
        )

        if exact_result is not None:
            return exact_result

        phrase_translations = (
            (
                "Gaming readiness scan failed:",
                "فشل فحص جاهزية الألعاب:",
            ),
            (
                "Could not read",
                "تعذرت قراءة",
            ),
            (
                "could not be read",
                "تعذرت قراءته",
            ),
            (
                "could not be detected",
                "تعذر اكتشافه",
            ),
            (
                "This setting is recommended.",
                "هذا الإعداد موصى به.",
            ),
            (
                "This setting needs attention.",
                "هذا الإعداد يحتاج إلى انتباه.",
            ),
            (
                "This setting is unavailable.",
                "هذا الإعداد غير متوفر.",
            ),
            (
                "Turn this setting on",
                "فعّل هذا الإعداد",
            ),
            (
                "Turn this setting off",
                "عطّل هذا الإعداد",
            ),
            (
                "Enable this setting",
                "فعّل هذا الإعداد",
            ),
            (
                "Disable this setting",
                "عطّل هذا الإعداد",
            ),
            (
                "for better gaming performance",
                "للحصول على أداء أفضل في الألعاب",
            ),
            (
                "for improved gaming performance",
                "لتحسين أداء الألعاب",
            ),
            (
                "Windows settings",
                "إعدادات ويندوز",
            ),
            (
                "gaming performance",
                "أداء الألعاب",
            ),
            (
                "Not available",
                "غير متوفر",
            ),
        )

        translated = text

        for english, arabic in phrase_translations:
            translated = translated.replace(
                english,
                arabic,
            )

        return translated

    def _reset_stat_values(self) -> None:
        """إعادة قيم الملخص إلى الحالة الفارغة."""

        self.score_value.setText(
            "--"
        )
        self.recommended_value.setText(
            "--"
        )
        self.attention_value.setText(
            "--"
        )
        self.unavailable_value.setText(
            "--"
        )

    def _clear_settings(self) -> None:
        """حذف صفوف الإعدادات الحالية."""

        while self.settings_layout.count():
            layout_item = (
                self.settings_layout.takeAt(0)
            )

            widget = layout_item.widget()

            if widget is not None:
                widget.setParent(
                    None
                )
                widget.deleteLater()

    def _text(
        self,
        english: str,
        arabic: str,
    ) -> str:
        """اختيار النص حسب لغة البرنامج."""

        if self.is_rtl:
            return arabic

        return english