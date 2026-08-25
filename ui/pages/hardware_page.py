
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

from core.services.inventory_service import InventoryService
from core.services.localization_service import LocalizationService
from infrastructure.logging.logger import get_logger
from ui.widgets.hardware_info_card import HardwareInfoCard


class HardwarePage(QWidget):
    """صفحة معلومات مكونات الجهاز."""

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

        self.logger = get_logger()
        self.inventory_service = InventoryService()

        self.setObjectName("page")
        self.setLayoutDirection(
            Qt.LayoutDirection.RightToLeft
            if self.is_rtl
            else Qt.LayoutDirection.LeftToRight
        )

        self._setup_ui()
        self._load_hardware_information()

    def _setup_ui(self) -> None:
        """إنشاء صفحة Hardware والبطاقات."""

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(40, 35, 40, 35)
        main_layout.setSpacing(18)

        header_layout = QGridLayout()
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setHorizontalSpacing(20)
        header_layout.setVerticalSpacing(6)

        self.title_label = QLabel(
            self._text(
                "Hardware Information",
                "معلومات الجهاز",
            )
        )
        self.title_label.setObjectName("pageTitle")

        self.subtitle_label = QLabel(
            self._text(
                "Detailed information about your computer components.",
                "معلومات تفصيلية عن مكونات جهاز الكمبيوتر.",
            )
        )
        self.subtitle_label.setObjectName("pageSubtitle")
        self.subtitle_label.setWordWrap(True)

        text_alignment = (
            Qt.AlignmentFlag.AlignRight
            if self.is_rtl
            else Qt.AlignmentFlag.AlignLeft
        )

        self.title_label.setAlignment(text_alignment)
        self.subtitle_label.setAlignment(text_alignment)

        self.refresh_button = QPushButton(
            self._text(
                "Refresh Information",
                "تحديث المعلومات",
            )
        )
        self.refresh_button.setObjectName(
            "hardwareRefreshButton"
        )
        self.refresh_button.setMinimumWidth(180)
        self.refresh_button.setMinimumHeight(42)
        self.refresh_button.setCursor(
            Qt.CursorShape.PointingHandCursor
        )
        self.refresh_button.clicked.connect(
            self._load_hardware_information
        )

        if self.is_rtl:
            header_layout.addWidget(
                self.refresh_button,
                0,
                0,
                2,
                1,
                Qt.AlignmentFlag.AlignLeft
                | Qt.AlignmentFlag.AlignVCenter,
            )
            header_layout.addWidget(
                self.title_label,
                0,
                1,
            )
            header_layout.addWidget(
                self.subtitle_label,
                1,
                1,
            )
            header_layout.setColumnStretch(1, 1)
        else:
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
                Qt.AlignmentFlag.AlignRight
                | Qt.AlignmentFlag.AlignVCenter,
            )
            header_layout.addWidget(
                self.subtitle_label,
                1,
                0,
            )
            header_layout.setColumnStretch(0, 1)

        scroll_area = QScrollArea()
        scroll_area.setObjectName(
            "hardwareScrollArea"
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
            "hardwareScrollContainer"
        )
        scroll_container.setLayoutDirection(
            Qt.LayoutDirection.RightToLeft
            if self.is_rtl
            else Qt.LayoutDirection.LeftToRight
        )

        self.cards_layout = QGridLayout(
            scroll_container
        )
        self.cards_layout.setContentsMargins(
            0,
            0,
            10,
            0,
        )
        self.cards_layout.setHorizontalSpacing(18)
        self.cards_layout.setVerticalSpacing(18)
        self.cards_layout.setColumnStretch(0, 1)
        self.cards_layout.setColumnStretch(1, 1)

        self.system_card = HardwareInfoCard(
            self._text(
                "Operating System",
                "نظام التشغيل",
            )
        )
        self.processor_card = HardwareInfoCard(
            self._text(
                "Processor",
                "المعالج",
            )
        )
        self.memory_card = HardwareInfoCard(
            self._text(
                "Memory",
                "الذاكرة",
            )
        )
        self.graphics_card = HardwareInfoCard(
            self._text(
                "Graphics Cards",
                "كروت الشاشة",
            )
        )
        self.motherboard_card = HardwareInfoCard(
            self._text(
                "Motherboard",
                "اللوحة الأم",
            )
        )
        self.bios_card = HardwareInfoCard("BIOS")
        self.storage_card = HardwareInfoCard(
            self._text(
                "Storage Devices",
                "أجهزة التخزين",
            )
        )
        self.network_card = HardwareInfoCard(
            self._text(
                "Network Adapters",
                "محولات الشبكة",
            )
        )
        self.battery_card = HardwareInfoCard(
            self._text(
                "Battery",
                "البطارية",
            )
        )

        for card in self._all_cards():
            card.setLayoutDirection(
                Qt.LayoutDirection.RightToLeft
                if self.is_rtl
                else Qt.LayoutDirection.LeftToRight
            )

        self.cards_layout.addWidget(
            self.system_card,
            0,
            0,
        )
        self.cards_layout.addWidget(
            self.processor_card,
            0,
            1,
        )
        self.cards_layout.addWidget(
            self.memory_card,
            1,
            0,
        )
        self.cards_layout.addWidget(
            self.graphics_card,
            1,
            1,
        )
        self.cards_layout.addWidget(
            self.motherboard_card,
            2,
            0,
        )
        self.cards_layout.addWidget(
            self.bios_card,
            2,
            1,
        )
        self.cards_layout.addWidget(
            self.storage_card,
            3,
            0,
        )
        self.cards_layout.addWidget(
            self.network_card,
            3,
            1,
        )
        self.cards_layout.addWidget(
            self.battery_card,
            4,
            0,
            1,
            2,
        )
        self.cards_layout.setRowStretch(
            5,
            1,
        )

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

    def _load_hardware_information(self) -> None:
        """قراءة وتوزيع معلومات الجهاز على البطاقات."""

        self._set_loading_state(True)

        try:
            basic_result = (
                self.inventory_service
                .get_basic_system_info()
            )

            identity_result = (
                self.inventory_service
                .get_hardware_identity()
            )

            storage_result = (
                self.inventory_service
                .get_storage_inventory()
            )

            network_result = (
                self.inventory_service
                .get_network_inventory()
            )

            battery_result = (
                self.inventory_service
                .get_battery_inventory()
            )

            self._display_basic_information(
                basic_result
            )

            self._display_identity_information(
                identity_result
            )

            self._display_storage_information(
                storage_result
            )

            self._display_network_information(
                network_result
            )

            self._display_battery_information(
                battery_result
            )

            self.logger.info(
                "Hardware cards updated successfully"
            )

        except Exception:
            self.logger.exception(
                "Unexpected error while updating "
                "hardware cards"
            )

            self._show_unexpected_error()

        finally:
            self._set_loading_state(False)


    def _display_basic_information(
        self,
        result,
    ) -> None:
        """عرض النظام والمعالج والرام."""

        if not result.success or result.data is None:
            for card in (
                self.system_card,
                self.processor_card,
                self.memory_card,
            ):
                card.set_error(
                    self._localized_service_message(
                        result.message
                    ),
                    result.error_code,
                )

            self.logger.error(
                "Basic system information could "
                "not be displayed: %s",
                result.message,
            )
            return

        info = result.data

        physical_cores = self._display_value(
            info.physical_cores
        )
        logical_cores = self._display_value(
            info.logical_cores
        )

        used_memory_bytes = (
            info.total_memory_bytes
            - info.available_memory_bytes
        )
        used_memory_gb = round(
            used_memory_bytes / (1024 ** 3),
            2,
        )

        self.system_card.set_content(
            self._join_fields(
                (
                    self._text("Name", "الاسم"),
                    info.operating_system,
                ),
                (
                    self._text("Version", "الإصدار"),
                    info.os_version,
                ),
                (
                    self._text("Build", "رقم البناء"),
                    info.os_build,
                ),
                (
                    self._text("Architecture", "المعمارية"),
                    info.architecture,
                ),
                (
                    self._text(
                        "Computer Name",
                        "اسم الكمبيوتر",
                    ),
                    info.computer_name,
                ),
            )
        )

        self.processor_card.set_content(
            self._join_fields(
                (
                    self._text("Model", "الطراز"),
                    info.cpu_name,
                ),
                (
                    self._text(
                        "Physical Cores",
                        "الأنوية الفعلية",
                    ),
                    physical_cores,
                ),
                (
                    self._text(
                        "Logical Cores",
                        "الأنوية المنطقية",
                    ),
                    logical_cores,
                ),
            )
        )

        self.memory_card.set_content(
            self._join_fields(
                (
                    self._text(
                        "Installed RAM",
                        "الرام المثبتة",
                    ),
                    f"{info.total_memory_gb} GB",
                ),
                (
                    self._text(
                        "Available RAM",
                        "الرام المتاحة",
                    ),
                    f"{info.available_memory_gb} GB",
                ),
                (
                    self._text(
                        "RAM In Use",
                        "الرام المستخدمة",
                    ),
                    f"{used_memory_gb} GB",
                ),
            )
        )

    def _display_identity_information(
        self,
        result,
    ) -> None:
        """عرض GPU واللوحة الأم وBIOS."""

        if not result.success or result.data is None:
            for card in (
                self.graphics_card,
                self.motherboard_card,
                self.bios_card,
            ):
                card.set_error(
                    self._localized_service_message(
                        result.message
                    ),
                    result.error_code,
                )

            self.logger.error(
                "Hardware identity could not "
                "be displayed: %s",
                result.message,
            )
            return

        identity = result.data

        self.graphics_card.set_content(
            self._format_gpu_information(
                identity.gpus
            )
        )
        self.motherboard_card.set_content(
            self._format_motherboard_information(
                identity.motherboards
            )
        )
        self.bios_card.set_content(
            self._format_bios_information(
                identity.bios
            )
        )

    def _display_storage_information(
        self,
        result,
    ) -> None:
        """عرض الأقراص والأقسام داخل بطاقة Storage."""

        if not result.success or result.data is None:
            self.storage_card.set_error(
                self._localized_service_message(
                    result.message
                ),
                result.error_code,
            )

            self.logger.error(
                "Storage information could not "
                "be displayed: %s",
                result.message,
            )
            return

        devices = result.data.devices

        if not devices:
            self.storage_card.set_content(
                self._text(
                    "No storage devices were detected.",
                    "لم يتم اكتشاف أي أجهزة تخزين.",
                )
            )
            return

        self.storage_card.set_content(
            self._format_storage_information(
                devices
            )
        )

    def _display_network_information(
        self,
        result,
    ) -> None:
        """عرض معلومات كروت الشبكة."""

        if not result.success or result.data is None:
            self.network_card.set_error(
                self._localized_service_message(
                    result.message
                ),
                result.error_code,
            )

            self.logger.error(
                "Network information could not "
                "be displayed: %s",
                result.message,
            )
            return

        adapters = result.data.adapters

        if not adapters:
            self.network_card.set_content(
                self._text(
                    (
                        "No physical network adapters "
                        "were detected."
                    ),
                    (
                        "لم يتم اكتشاف أي محولات "
                        "شبكة فعلية."
                    ),
                )
            )
            return

        self.network_card.set_content(
            self._format_network_information(
                adapters
            )
        )

    def _display_battery_information(
        self,
        result,
    ) -> None:
        """عرض معلومات البطارية."""

        if not result.success or result.data is None:
            self.battery_card.set_error(
                self._localized_service_message(
                    result.message
                ),
                result.error_code,
            )

            self.logger.error(
                "Battery information could not "
                "be displayed: %s",
                result.message,
            )
            return

        batteries = result.data.batteries

        if not batteries:
            self.battery_card.set_content(
                self._text(
                    (
                        "No battery detected.\n\n"
                        "This device may be a desktop computer."
                    ),
                    (
                        "لم يتم اكتشاف بطارية.\n\n"
                        "قد يكون هذا الجهاز كمبيوتر مكتبيًا."
                    ),
                )
            )
            return

        self.battery_card.set_content(
            self._format_battery_information(
                batteries
            )
        )

    def _format_gpu_information(
        self,
        gpus,
    ) -> str:
        """تنسيق جميع كروت الشاشة."""

        if not gpus:
            return self._text(
                (
                    "No graphics card information "
                    "was available."
                ),
                (
                    "لا تتوفر معلومات عن "
                    "كرت الشاشة."
                ),
            )

        sections: list[str] = []

        for index, gpu in enumerate(
            gpus,
            start=1,
        ):
            sections.append(
                self._join_fields(
                    (
                        self._text(
                            f"GPU {index}",
                            f"كرت الشاشة {index}",
                        ),
                        gpu.name,
                    ),
                    (
                        self._text(
                            "Manufacturer",
                            "الشركة المصنعة",
                        ),
                        gpu.manufacturer,
                    ),
                    (
                        self._text(
                            "Video Processor",
                            "معالج الرسومات",
                        ),
                        gpu.video_processor,
                    ),
                    (
                        self._text(
                            "Driver Version",
                            "إصدار التعريف",
                        ),
                        gpu.driver_version,
                    ),
                    (
                        self._text(
                            "Status",
                            "الحالة",
                        ),
                        gpu.status,
                    ),
                )
            )

        return self._section_separator().join(
            sections
        )

    def _format_motherboard_information(
        self,
        motherboards,
    ) -> str:
        """تنسيق معلومات اللوحة الأم."""

        if not motherboards:
            return self._text(
                "Motherboard information was unavailable.",
                "معلومات اللوحة الأم غير متوفرة.",
            )

        sections: list[str] = []

        for index, board in enumerate(
            motherboards,
            start=1,
        ):
            title = self._text(
                (
                    "Motherboard"
                    if len(motherboards) == 1
                    else f"Motherboard {index}"
                ),
                (
                    "اللوحة الأم"
                    if len(motherboards) == 1
                    else f"اللوحة الأم {index}"
                ),
            )

            sections.append(
                self._join_fields(
                    (
                        title,
                        "",
                    ),
                    (
                        self._text(
                            "Manufacturer",
                            "الشركة المصنعة",
                        ),
                        board.manufacturer,
                    ),
                    (
                        self._text(
                            "Model",
                            "الطراز",
                        ),
                        board.product,
                    ),
                    (
                        self._text(
                            "Version",
                            "الإصدار",
                        ),
                        board.version,
                    ),
                    (
                        self._text(
                            "Serial Number",
                            "الرقم التسلسلي",
                        ),
                        self._normalize_serial(
                            board.serial_number
                        ),
                    ),
                )
            )

        return self._section_separator().join(
            sections
        )

    def _format_bios_information(
        self,
        bios,
    ) -> str:
        """تنسيق معلومات BIOS."""

        if bios is None:
            return self._text(
                "BIOS information was unavailable.",
                "معلومات BIOS غير متوفرة.",
            )

        return self._join_fields(
            (
                self._text(
                    "Manufacturer",
                    "الشركة المصنعة",
                ),
                bios.manufacturer,
            ),
            (
                self._text(
                    "Version",
                    "الإصدار",
                ),
                bios.version,
            ),
            (
                self._text(
                    "Release Date",
                    "تاريخ الإصدار",
                ),
                bios.release_date,
            ),
            (
                self._text(
                    "Serial Number",
                    "الرقم التسلسلي",
                ),
                self._normalize_serial(
                    bios.serial_number
                ),
            ),
        )

    def _format_storage_information(
        self,
        devices,
    ) -> str:
        """تنسيق جميع أقراص التخزين والأقسام."""

        device_sections: list[str] = []

        for index, device in enumerate(
            devices,
            start=1,
        ):
            volume_sections: list[str] = []

            for partition in device.partitions:
                for volume in partition.volumes:
                    volume_title = str(
                        volume.device_id
                    )

                    if volume.volume_name:
                        volume_title += (
                            f" — {volume.volume_name}"
                        )

                    volume_sections.append(
                        self._join_fields(
                            (
                                volume_title,
                                "",
                            ),
                            (
                                self._text(
                                    "File System",
                                    "نظام الملفات",
                                ),
                                volume.file_system,
                            ),
                            (
                                self._text(
                                    "Capacity",
                                    "السعة",
                                ),
                                self._format_gb(
                                    volume.size_gb
                                ),
                            ),
                            (
                                self._text(
                                    "Used",
                                    "المستخدم",
                                ),
                                self._format_gb(
                                    volume.used_gb
                                ),
                            ),
                            (
                                self._text(
                                    "Free",
                                    "المتاح",
                                ),
                                self._format_gb(
                                    volume.free_gb
                                ),
                            ),
                        )
                    )

            volumes_text = (
                self._section_separator().join(
                    volume_sections
                )
                if volume_sections
                else self._text(
                    "No mounted volumes.",
                    "لا توجد وحدات تخزين مركبة.",
                )
            )

            device_sections.append(
                self._join_fields(
                    (
                        self._text(
                            f"Disk {index}",
                            f"القرص {index}",
                        ),
                        device.model,
                    ),
                    (
                        self._text(
                            "Type",
                            "النوع",
                        ),
                        device.storage_type,
                    ),
                    (
                        self._text(
                            "Capacity",
                            "السعة",
                        ),
                        self._format_gb(
                            device.size_gb
                        ),
                    ),
                    (
                        self._text(
                            "Bus",
                            "الناقل",
                        ),
                        device.bus_type,
                    ),
                    (
                        self._text(
                            "Interface",
                            "الواجهة",
                        ),
                        device.interface_type,
                    ),
                    (
                        self._text(
                            "Status",
                            "الحالة",
                        ),
                        device.status,
                    ),
                    (
                        self._text(
                            "Volumes",
                            "وحدات التخزين",
                        ),
                        volumes_text,
                    ),
                )
            )

        return "\n\n════════════════\n\n".join(
            device_sections
        )

    def _format_network_information(
        self,
        adapters,
    ) -> str:
        """تنسيق معلومات كروت الشبكة."""

        adapter_sections: list[str] = []

        for index, adapter in enumerate(
            adapters,
            start=1,
        ):
            adapter_sections.append(
                self._join_fields(
                    (
                        self._text(
                            f"Adapter {index}",
                            f"المحول {index}",
                        ),
                        adapter.name,
                    ),
                    (
                        self._text(
                            "Type",
                            "النوع",
                        ),
                        adapter.adapter_type,
                    ),
                    (
                        self._text(
                            "Description",
                            "الوصف",
                        ),
                        adapter.description,
                    ),
                    (
                        self._text(
                            "Status",
                            "الحالة",
                        ),
                        adapter.status,
                    ),
                    (
                        self._text(
                            "Link Speed",
                            "سرعة الاتصال",
                        ),
                        adapter.link_speed,
                    ),
                    (
                        self._text(
                            "IPv4 Address",
                            "عنوان IPv4",
                        ),
                        self._format_text_values(
                            adapter.ipv4_addresses
                        ),
                    ),
                    (
                        self._text(
                            "Default Gateway",
                            "البوابة الافتراضية",
                        ),
                        adapter.default_gateway,
                    ),
                    (
                        self._text(
                            "DNS Servers",
                            "خوادم DNS",
                        ),
                        self._format_text_values(
                            adapter.dns_servers
                        ),
                    ),
                )
            )

        return self._section_separator().join(
            adapter_sections
        )

    def _format_battery_information(
        self,
        batteries,
    ) -> str:
        """تنسيق معلومات البطاريات."""

        battery_sections: list[str] = []

        for index, battery in enumerate(
            batteries,
            start=1,
        ):
            title = self._text(
                (
                    "Battery"
                    if len(batteries) == 1
                    else f"Battery {index}"
                ),
                (
                    "البطارية"
                    if len(batteries) == 1
                    else f"البطارية {index}"
                ),
            )

            battery_sections.append(
                self._join_fields(
                    (
                        title,
                        battery.name,
                    ),
                    (
                        self._text(
                            "Charge",
                            "نسبة الشحن",
                        ),
                        self._format_percent(
                            battery.charge_percent
                        ),
                    ),
                    (
                        self._text(
                            "Power State",
                            "حالة الطاقة",
                        ),
                        self._format_power_state(
                            battery.power_plugged
                        ),
                    ),
                    (
                        self._text(
                            "Battery Status",
                            "حالة البطارية",
                        ),
                        battery.battery_status,
                    ),
                    (
                        self._text(
                            "Chemistry",
                            "نوع الخلايا",
                        ),
                        battery.chemistry,
                    ),
                    (
                        self._text(
                            "Estimated Runtime",
                            "الوقت المتبقي المتوقع",
                        ),
                        self._format_runtime(
                            battery.estimated_runtime_minutes
                        ),
                    ),
                )
            )

        return self._section_separator().join(
            battery_sections
        )

    def _set_loading_state(
        self,
        is_loading: bool,
    ) -> None:
        """تحديث حالة التحميل."""

        self.refresh_button.setEnabled(
            not is_loading
        )

        self.refresh_button.setText(
            self._text(
                "Reading Information...",
                "جارٍ قراءة المعلومات...",
            )
            if is_loading
            else self._text(
                "Refresh Information",
                "تحديث المعلومات",
            )
        )

        if not is_loading:
            return

        for card in self._all_cards():
            card.set_loading()

    def _show_unexpected_error(self) -> None:
        """عرض الخطأ العام داخل جميع البطاقات."""

        for card in self._all_cards():
            card.set_error(
                self._text(
                    (
                        "An unexpected error occurred. "
                        "Details were saved in the log file."
                    ),
                    (
                        "حدث خطأ غير متوقع. تم حفظ "
                        "التفاصيل داخل ملف السجل."
                    ),
                ),
                "UNEXPECTED_HARDWARE_PAGE_ERROR",
            )

    def _all_cards(
        self,
    ) -> tuple[HardwareInfoCard, ...]:
        """إرجاع جميع بطاقات الصفحة."""

        return (
            self.system_card,
            self.processor_card,
            self.memory_card,
            self.graphics_card,
            self.motherboard_card,
            self.bios_card,
            self.storage_card,
            self.network_card,
            self.battery_card,
        )

    def _apply_page_style(self) -> None:
        """تنسيق صفحة Hardware والبطاقات."""

        self.setStyleSheet(
            """
            QScrollArea#hardwareScrollArea,
            QWidget#hardwareScrollContainer {
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

            QPushButton#hardwareRefreshButton {
                padding: 0 18px;
                color: #07101d;
                background-color: #66e3ff;
                border: none;
                border-radius: 9px;
                font-family: "Segoe UI";
                font-size: 14px;
                font-weight: 700;
            }

            QPushButton#hardwareRefreshButton:hover {
                background-color: #8aeaff;
            }

            QPushButton#hardwareRefreshButton:pressed {
                background-color: #3fc8e7;
            }

            QPushButton#hardwareRefreshButton:disabled {
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

    def _format_text_values(
        self,
        values,
    ) -> str:
        """تنسيق قائمة من القيم النصية."""

        if not values:
            return self._unavailable()

        cleaned_values = [
            str(value)
            for value in values
            if str(value).strip()
        ]

        return (
            "\n".join(cleaned_values)
            or self._unavailable()
        )

    def _format_gb(
        self,
        value,
    ) -> str:
        """تنسيق قيمة الجيجابايت."""

        if value is None:
            return self._unavailable()

        return f"{value} GB"

    def _format_percent(
        self,
        value,
    ) -> str:
        """تنسيق نسبة البطارية."""

        if value is None:
            return self._unavailable()

        numeric_value = float(value)

        if numeric_value.is_integer():
            return f"{int(numeric_value)}%"

        return f"{numeric_value}%"

    def _format_power_state(
        self,
        power_plugged: bool | None,
    ) -> str:
        """تنسيق حالة الشاحن."""

        if power_plugged is True:
            return self._text(
                "Plugged In",
                "موصول بالشاحن",
            )

        if power_plugged is False:
            return self._text(
                "Running on Battery",
                "يعمل على البطارية",
            )

        return self._unavailable()

    def _format_runtime(
        self,
        minutes: int | None,
    ) -> str:
        """تنسيق مدة البطارية المتبقية."""

        if minutes is None:
            return self._unavailable()

        hours, remaining_minutes = divmod(
            minutes,
            60,
        )

        if self.is_rtl:
            if hours > 0:
                return (
                    f"{hours} ساعة و"
                    f"{remaining_minutes} دقيقة"
                )

            return f"{remaining_minutes} دقيقة"

        if hours > 0:
            return (
                f"{hours} hour(s), "
                f"{remaining_minutes} minute(s)"
            )

        return f"{remaining_minutes} minute(s)"

    def _display_value(
        self,
        value,
    ) -> str:
        """تحويل القيمة الفارغة إلى نص مناسب."""

        if value is None:
            return self._unavailable()

        cleaned_value = str(value).strip()

        return (
            cleaned_value
            or self._unavailable()
        )

    def _normalize_serial(
        self,
        value,
    ) -> str:
        """إخفاء أرقام Serial الافتراضية."""

        if value is None:
            return self._unavailable()

        cleaned_value = str(value).strip()

        invalid_values = {
            "",
            "system serial number",
            "to be filled by o.e.m.",
            "default string",
            "unknown",
            "none",
            "not specified",
            "unavailable",
        }

        if cleaned_value.lower() in invalid_values:
            return self._unavailable()

        return cleaned_value

    def _localized_service_message(
        self,
        message,
    ) -> str:
        """إظهار رسالة خدمة مناسبة للغة الحالية."""

        if not self.is_rtl:
            return self._display_value(
                message
            )

        return self._text(
            self._display_value(message),
            (
                "تعذر قراءة معلومات هذا القسم. "
                "راجع ملف السجل لمزيد من التفاصيل."
            ),
        )

    def _join_fields(
        self,
        *fields: tuple[str, object],
    ) -> str:
        """تنسيق اسم الحقل والقيمة داخل البطاقة."""

        sections: list[str] = []

        for label, value in fields:
            display_value = (
                ""
                if value == ""
                else self._display_value(value)
            )

            if display_value:
                sections.append(
                    f"{label}\n{display_value}"
                )
            else:
                sections.append(
                    str(label)
                )

        return "\n\n".join(
            sections
        )

    @staticmethod
    def _section_separator() -> str:
        """الفاصل بين عدة أجهزة داخل البطاقة."""

        return "\n\n──────────────\n\n"

    def _unavailable(self) -> str:
        """النص المستخدم عند عدم توفر قيمة."""

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