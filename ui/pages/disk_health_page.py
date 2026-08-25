from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QApplication,
    QFrame,
    QGridLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from core.services.application_settings_service import (
    ApplicationSettingsService,
)
from core.services.inventory_service import InventoryService
from core.services.localization_service import (
    LocalizationService,
)
from infrastructure.logging.logger import get_logger
from ui.widgets.hardware_info_card import HardwareInfoCard


class DiskHealthPage(QWidget):
    """صفحة فحص صحة واعتمادية أقراص التخزين."""

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

        self.is_rtl = self.localization.is_rtl

        self.logger = get_logger()
        self.inventory_service = InventoryService()

        self.disk_cards: list[
            HardwareInfoCard
        ] = []

        self.setObjectName("page")
        self.setLayoutDirection(
            Qt.LayoutDirection.RightToLeft
            if self.is_rtl
            else Qt.LayoutDirection.LeftToRight
        )

        self._setup_ui()
        self._load_disk_health()

    def _setup_ui(self) -> None:
        """إنشاء واجهة صفحة Disk Health."""

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(
            40,
            35,
            40,
            35,
        )
        main_layout.setSpacing(18)

        header_layout = QGridLayout()
        header_layout.setContentsMargins(
            0,
            0,
            0,
            0,
        )
        header_layout.setHorizontalSpacing(20)
        header_layout.setVerticalSpacing(6)

        self.title_label = QLabel(
            self._text(
                "Disk Health",
                "صحة الأقراص",
            )
        )
        self.title_label.setObjectName(
            "pageTitle"
        )
        self.title_label.setAlignment(
            Qt.AlignmentFlag.AlignLeading
            | Qt.AlignmentFlag.AlignVCenter
        )

        self.subtitle_label = QLabel(
            self._text(
                (
                    "Monitor drive health, temperature, "
                    "wear and reliability information."
                ),
                (
                    "راقب صحة الأقراص ودرجة الحرارة "
                    "والاستهلاك وبيانات الاعتمادية."
                ),
            )
        )
        self.subtitle_label.setObjectName(
            "pageSubtitle"
        )
        self.subtitle_label.setWordWrap(True)
        self.subtitle_label.setAlignment(
            Qt.AlignmentFlag.AlignLeading
            | Qt.AlignmentFlag.AlignVCenter
        )

        self.refresh_button = QPushButton(
            self._text(
                "Refresh Disk Health",
                "تحديث صحة الأقراص",
            )
        )
        self.refresh_button.setObjectName(
            "diskHealthRefreshButton"
        )
        self.refresh_button.setMinimumWidth(190)
        self.refresh_button.setMinimumHeight(42)
        self.refresh_button.setCursor(
            Qt.CursorShape.PointingHandCursor
        )
        self.refresh_button.clicked.connect(
            self._load_disk_health
        )

        header_layout.addWidget(
            self.title_label,
            0,
            0,
        )

        header_layout.addWidget(
            self.refresh_button,
            0,
            1,
            2,
            1,
            (
                Qt.AlignmentFlag.AlignLeft
                if self.is_rtl
                else Qt.AlignmentFlag.AlignRight
            )
            | Qt.AlignmentFlag.AlignVCenter,
        )

        header_layout.addWidget(
            self.subtitle_label,
            1,
            0,
        )

        scroll_area = QScrollArea()
        scroll_area.setObjectName(
            "diskHealthScrollArea"
        )
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(
            QFrame.Shape.NoFrame
        )
        scroll_area.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        scroll_area.setVerticalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAsNeeded
        )

        scroll_container = QWidget()
        scroll_container.setObjectName(
            "diskHealthScrollContainer"
        )

        scroll_layout = QVBoxLayout(
            scroll_container
        )
        scroll_layout.setContentsMargins(
            0,
            0,
            10,
            0,
        )
        scroll_layout.setSpacing(18)

        self.summary_card = HardwareInfoCard(
            self._text(
                "Disk Health Summary",
                "ملخص صحة الأقراص",
            )
        )

        self.disk_cards_container = QWidget()
        self.disk_cards_container.setObjectName(
            "diskCardsContainer"
        )

        self.disk_cards_layout = QGridLayout(
            self.disk_cards_container
        )
        self.disk_cards_layout.setContentsMargins(
            0,
            0,
            0,
            0,
        )
        self.disk_cards_layout.setHorizontalSpacing(18)
        self.disk_cards_layout.setVerticalSpacing(18)
        self.disk_cards_layout.setColumnStretch(0, 1)
        self.disk_cards_layout.setColumnStretch(1, 1)
        self.disk_cards_layout.setAlignment(
            Qt.AlignmentFlag.AlignTop
        )

        scroll_layout.addWidget(
            self.summary_card
        )
        scroll_layout.addWidget(
            self.disk_cards_container
        )
        scroll_layout.addStretch()

        scroll_area.setWidget(
            scroll_container
        )

        main_layout.addLayout(
            header_layout
        )
        main_layout.addWidget(
            scroll_area,
            1,
        )

        self._apply_page_style()

    def _load_disk_health(self) -> None:
        """قراءة صحة الأقراص وعرض النتائج."""

        self._set_loading_state(True)
        self._clear_disk_cards()

        try:
            result = (
                self.inventory_service
                .get_disk_health_inventory()
            )

            self._display_disk_health(
                result
            )

        except Exception:
            self.logger.exception(
                "Unexpected error while displaying "
                "disk health information"
            )

            self.summary_card.set_error(
                self._text(
                    (
                        "An unexpected error occurred. "
                        "Details were saved in the log file."
                    ),
                    (
                        "حدث خطأ غير متوقع. تم حفظ "
                        "التفاصيل في ملف السجل."
                    ),
                ),
                "UNEXPECTED_DISK_HEALTH_PAGE_ERROR",
            )

        finally:
            self._set_loading_state(False)

    def _display_disk_health(
        self,
        result,
    ) -> None:
        """عرض نتيجة فحص صحة الأقراص."""

        if not result.success or result.data is None:
            self.summary_card.set_error(
                self._translated_result_message(
                    result.message
                ),
                result.error_code,
            )

            self.logger.error(
                "Disk health information could not "
                "be displayed: %s",
                result.message,
            )
            return

        disks = result.data.disks

        if not disks:
            self.summary_card.set_content(
                self._text(
                    (
                        "No physical storage drives "
                        "were detected."
                    ),
                    (
                        "لم يتم اكتشاف أقراص تخزين "
                        "فعلية."
                    ),
                )
            )
            return

        healthy_count = sum(
            1
            for disk in disks
            if str(
                disk.health_status
            ).strip().casefold()
            == "healthy"
        )

        reliability_count = sum(
            1
            for disk in disks
            if disk.reliability_available
        )

        warning_count = (
            len(disks) - healthy_count
        )

        if warning_count == 0:
            overall_status = self._text(
                "All detected drives are healthy.",
                "جميع الأقراص المكتشفة سليمة.",
            )
        else:
            overall_status = self._text(
                (
                    f"{warning_count} drive(s) "
                    "require attention."
                ),
                (
                    f"{warning_count} من الأقراص "
                    "تحتاج إلى الانتباه."
                ),
            )

        self.summary_card.set_content(
            self._text(
                (
                    f"Overall Status\n"
                    f"{overall_status}\n\n"
                    f"Detected Drives\n"
                    f"{len(disks)}\n\n"
                    f"Healthy Drives\n"
                    f"{healthy_count}\n\n"
                    f"Reliability Data Available\n"
                    f"{reliability_count} of {len(disks)}\n\n"
                    f"Important\n"
                    f"Run Pixel Guardian as administrator "
                    f"to access all supported SMART and "
                    f"reliability information."
                ),
                (
                    f"الحالة العامة\n"
                    f"{overall_status}\n\n"
                    f"الأقراص المكتشفة\n"
                    f"{len(disks)}\n\n"
                    f"الأقراص السليمة\n"
                    f"{healthy_count}\n\n"
                    f"بيانات الاعتمادية المتوفرة\n"
                    f"{reliability_count} من {len(disks)}\n\n"
                    f"مهم\n"
                    f"شغّل بيكسل جارديان كمسؤول للوصول "
                    f"إلى جميع بيانات SMART والاعتمادية "
                    f"المدعومة."
                ),
            )
        )

        for index, disk in enumerate(disks):
            card_title = self._text(
                (
                    f"Disk {disk.device_id} — "
                    f"{disk.friendly_name}"
                ),
                (
                    f"القرص {disk.device_id} — "
                    f"{disk.friendly_name}"
                ),
            )

            disk_card = HardwareInfoCard(
                card_title
            )

            disk_card.set_content(
                self._format_disk_information(
                    disk
                )
            )

            row = index // 2
            column = index % 2

            self.disk_cards_layout.addWidget(
                disk_card,
                row,
                column,
            )

            self.disk_cards.append(
                disk_card
            )

        self.logger.info(
            "Disk health page displayed successfully. "
            "Disk count: %s",
            len(disks),
        )

    def _format_disk_information(
        self,
        disk,
    ) -> str:
        """تنسيق معلومات قرص واحد."""

        operational_status = (
            ", ".join(
                self._translate_status(
                    value
                )
                for value in disk.operational_status
            )
            if disk.operational_status
            else self._unavailable()
        )

        reliability_status = (
            self._text(
                "Available",
                "متوفر",
            )
            if disk.reliability_available
            else self._unavailable()
        )

        reliability_note = ""

        if not disk.reliability_available:
            reliability_note = self._text(
                (
                    "\nRun the application as administrator, "
                    "or this drive may not support the counters."
                ),
                (
                    "\nشغّل البرنامج كمسؤول، أو قد لا يدعم "
                    "هذا القرص عدادات الاعتمادية."
                ),
            )

        temperature = self._format_temperature(
            disk.temperature_celsius
        )

        maximum_temperature = (
            self._format_temperature(
                disk.temperature_max_celsius
            )
        )

        power_on_time = self._format_power_on_hours(
            disk.power_on_hours
        )

        wear_text = self._format_wear(
            disk
        )

        read_errors = self._format_error_counters(
            total=disk.read_errors_total,
            corrected=disk.read_errors_corrected,
            uncorrected=(
                disk.read_errors_uncorrected
            ),
        )

        write_errors = self._format_error_counters(
            total=disk.write_errors_total,
            corrected=disk.write_errors_corrected,
            uncorrected=(
                disk.write_errors_uncorrected
            ),
        )

        return self._text(
            (
                f"Model\n"
                f"{self._display_value(disk.model)}\n\n"
                f"Drive Type\n"
                f"{self._display_value(disk.media_type)}\n\n"
                f"Bus Type\n"
                f"{self._display_value(disk.bus_type)}\n\n"
                f"Capacity\n"
                f"{self._format_gb(disk.size_gb)}\n\n"
                f"Firmware\n"
                f"{self._display_value(disk.firmware_version)}\n\n"
                f"Health Status\n"
                f"{self._translate_status(disk.health_status)}\n\n"
                f"Operational Status\n"
                f"{operational_status}\n\n"
                f"Reliability Counters\n"
                f"{reliability_status}"
                f"{reliability_note}\n\n"
                f"Current Temperature\n"
                f"{temperature}\n\n"
                f"Maximum Temperature\n"
                f"{maximum_temperature}\n\n"
                f"Power-on Time\n"
                f"{power_on_time}\n\n"
                f"Drive Wear\n"
                f"{wear_text}\n\n"
                f"Read Errors\n"
                f"{read_errors}\n\n"
                f"Write Errors\n"
                f"{write_errors}\n\n"
                f"Start / Stop Cycles\n"
                f"{self._format_counter(disk.start_stop_cycle_count)}\n\n"
                f"Load / Unload Cycles\n"
                f"{self._format_counter(disk.load_unload_cycle_count)}"
            ),
            (
                f"الموديل\n"
                f"{self._display_value(disk.model)}\n\n"
                f"نوع القرص\n"
                f"{self._display_value(disk.media_type)}\n\n"
                f"نوع الناقل\n"
                f"{self._display_value(disk.bus_type)}\n\n"
                f"السعة\n"
                f"{self._format_gb(disk.size_gb)}\n\n"
                f"البرنامج الثابت\n"
                f"{self._display_value(disk.firmware_version)}\n\n"
                f"حالة الصحة\n"
                f"{self._translate_status(disk.health_status)}\n\n"
                f"حالة التشغيل\n"
                f"{operational_status}\n\n"
                f"عدادات الاعتمادية\n"
                f"{reliability_status}"
                f"{reliability_note}\n\n"
                f"درجة الحرارة الحالية\n"
                f"{temperature}\n\n"
                f"أعلى درجة حرارة\n"
                f"{maximum_temperature}\n\n"
                f"مدة التشغيل\n"
                f"{power_on_time}\n\n"
                f"استهلاك القرص\n"
                f"{wear_text}\n\n"
                f"أخطاء القراءة\n"
                f"{read_errors}\n\n"
                f"أخطاء الكتابة\n"
                f"{write_errors}\n\n"
                f"دورات التشغيل والإيقاف\n"
                f"{self._format_counter(disk.start_stop_cycle_count)}\n\n"
                f"دورات التحميل والتفريغ\n"
                f"{self._format_counter(disk.load_unload_cycle_count)}"
            ),
        )

    def _clear_disk_cards(self) -> None:
        """حذف بطاقات الأقراص القديمة قبل التحديث."""

        for card in self.disk_cards:
            self.disk_cards_layout.removeWidget(
                card
            )
            card.setParent(None)
            card.deleteLater()

        self.disk_cards.clear()

    def _set_loading_state(
        self,
        is_loading: bool,
    ) -> None:
        """تحديث حالة تحميل الصفحة."""

        self.refresh_button.setEnabled(
            not is_loading
        )

        self.refresh_button.setText(
            self._text(
                (
                    "Reading Disk Health..."
                    if is_loading
                    else "Refresh Disk Health"
                ),
                (
                    "جارٍ قراءة صحة الأقراص..."
                    if is_loading
                    else "تحديث صحة الأقراص"
                ),
            )
        )

        if is_loading:
            self.summary_card.set_loading()

    def _apply_page_style(self) -> None:
            """تنسيق صفحة Disk Health."""

            self.setStyleSheet(
                """
                QScrollArea#diskHealthScrollArea,
                QWidget#diskHealthScrollContainer,
                QWidget#diskCardsContainer {
                    background-color: transparent;
                    border: none;
                }

                QFrame#hardwareInfoCard {
                    background-color: #131b2f;
                    border: 1px solid #253451;
                    border-radius: 16px;
                }

                QLabel#hardwareCardTitle {
                    color: #66e3ff;
                    font-family: "Segoe UI";
                    font-size: 19px;
                    font-weight: 700;
                }

                QLabel#hardwareCardContent {
                    color: #c2ccdc;
                    font-family: "Segoe UI";
                    font-size: 14px;
                }

                QPushButton#diskHealthRefreshButton {
                    padding: 0 18px;
                    color: #07101d;
                    background-color: #66e3ff;
                    border: none;
                    border-radius: 9px;
                    font-family: "Segoe UI";
                    font-size: 14px;
                    font-weight: 700;
                }

                QPushButton#diskHealthRefreshButton:hover {
                    background-color: #8aeaff;
                }

                QPushButton#diskHealthRefreshButton:pressed {
                    background-color: #3fc8e7;
                }

                QPushButton#diskHealthRefreshButton:disabled {
                    color: #697487;
                    background-color: #26344f;
                }

                QScrollBar:vertical {
                    width: 10px;
                    margin: 0;
                    background-color: #10182a;
                    border: none;
                    border-radius: 5px;
                }

                QScrollBar::handle:vertical {
                    min-height: 35px;
                    background-color: #3a4d6d;
                    border-radius: 5px;
                }

                QScrollBar::handle:vertical:hover {
                    background-color: #66e3ff;
                }

                QScrollBar::add-line:vertical,
                QScrollBar::sub-line:vertical {
                    height: 0;
                    border: none;
                    background: none;
                }

                QScrollBar::add-page:vertical,
                QScrollBar::sub-page:vertical {
                    background: none;
                }
                """
            )


    def _format_temperature(
        self,
        value: int | None,
    ) -> str:
        """تنسيق درجة الحرارة."""

        if value is None:
            return self._unavailable()

        return f"{value}°C"

    def _format_gb(
        self,
        value,
    ) -> str:
        """تنسيق حجم القرص."""

        if value is None:
            return self._unavailable()

        return f"{value} GB"

    def _format_power_on_hours(
        self,
        hours: int | None,
    ) -> str:
        """تنسيق ساعات تشغيل القرص."""

        if hours is None:
            return self._unavailable()

        days = round(
            hours / 24,
            1,
        )

        return self._text(
            (
                f"{hours:,} hours "
                f"(approximately {days:,} days)"
            ),
            (
                f"{hours:,} ساعة "
                f"(حوالي {days:,} يوم)"
            ),
        )

    def _format_wear(
        self,
        disk,
    ) -> str:
        """تنسيق نسبة استهلاك القرص."""

        media_type = (
            str(disk.media_type)
            .strip()
            .lower()
        )

        if "ssd" not in media_type:
            return self._text(
                "Not applicable to this drive type",
                "لا ينطبق على هذا النوع من الأقراص",
            )

        if disk.wear_percent is None:
            return self._unavailable()

        remaining_life = (
            disk.estimated_remaining_life_percent
        )

        remaining_text = (
            f"{remaining_life}%"
            if remaining_life is not None
            else self._unavailable()
        )

        return self._text(
            (
                f"Reported Wear: {disk.wear_percent}%\n"
                f"Estimated Remaining Life: "
                f"{remaining_text}"
            ),
            (
                f"الاستهلاك المسجل: {disk.wear_percent}%\n"
                f"العمر المتبقي المقدر: "
                f"{remaining_text}"
            ),
        )

    def _format_error_counters(
        self,
        total: int | None,
        corrected: int | None,
        uncorrected: int | None,
    ) -> str:
        """تنسيق عدادات أخطاء القرص."""

        if (
            total is None
            and corrected is None
            and uncorrected is None
        ):
            return self._unavailable()

        total_text = (
            f"{total:,}"
            if total is not None
            else self._unavailable()
        )

        corrected_text = (
            f"{corrected:,}"
            if corrected is not None
            else self._unavailable()
        )

        uncorrected_text = (
            f"{uncorrected:,}"
            if uncorrected is not None
            else self._unavailable()
        )

        return self._text(
            (
                f"Total: {total_text}\n"
                f"Corrected: {corrected_text}\n"
                f"Uncorrected: {uncorrected_text}"
            ),
            (
                f"الإجمالي: {total_text}\n"
                f"المصححة: {corrected_text}\n"
                f"غير المصححة: {uncorrected_text}"
            ),
        )

    def _format_counter(
        self,
        value: int | None,
    ) -> str:
        """تنسيق عداد رقمي."""

        if value is None:
            return self._unavailable()

        return f"{value:,}"

    def _display_value(
        self,
        value,
    ) -> str:
        """تنظيف قيمة نصية قبل العرض."""

        if value is None:
            return self._unavailable()

        cleaned_value = str(value).strip()

        return (
            cleaned_value
            or self._unavailable()
        )

    def _translate_status(
        self,
        value,
    ) -> str:
        """ترجمة حالات الأقراص الشائعة."""

        cleaned_value = str(
            value or ""
        ).strip()

        if not cleaned_value:
            return self._unavailable()

        if not self.is_rtl:
            return cleaned_value

        translations = {
            "healthy": "سليم",
            "ok": "سليم",
            "warning": "تحذير",
            "unhealthy": "غير سليم",
            "critical": "حرج",
            "online": "متصل",
            "offline": "غير متصل",
            "degraded": "متدهور",
            "unknown": "غير معروف",
            "lost communication": "فقدان الاتصال",
            "predictive failure": "فشل متوقع",
            "stressed": "تحت ضغط",
            "error": "خطأ",
        }

        return translations.get(
            cleaned_value.casefold(),
            cleaned_value,
        )

    def _translated_result_message(
        self,
        message,
    ) -> str:
        """ترجمة رسائل الخدمة الشائعة."""

        cleaned_message = str(
            message or ""
        ).strip()

        if not cleaned_message:
            return self._text(
                (
                    "Disk health information "
                    "is unavailable."
                ),
                (
                    "معلومات صحة الأقراص "
                    "غير متوفرة."
                ),
            )

        if not self.is_rtl:
            return cleaned_message

        lowered_message = cleaned_message.casefold()

        if "administrator" in lowered_message:
            return (
                "تعذر قراءة جميع معلومات صحة الأقراص. "
                "شغّل البرنامج كمسؤول ثم أعد المحاولة."
            )

        if "no physical" in lowered_message:
            return (
                "لم يتم اكتشاف أقراص تخزين فعلية."
            )

        if "unavailable" in lowered_message:
            return (
                "معلومات صحة الأقراص غير متوفرة."
            )

        return cleaned_message

    def _unavailable(self) -> str:
        """نص القيمة غير المتوفرة."""

        return self._text(
            "Unavailable",
            "غير متوفر",
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