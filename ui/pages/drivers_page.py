from __future__ import annotations

import subprocess

from PySide6.QtCore import (
    QObject,
    QThread,
    Qt,
    Signal,
    Slot,
)
from PySide6.QtGui import QShowEvent
from PySide6.QtWidgets import (
    QAbstractItemView,
    QApplication,
    QComboBox,
    QFrame,
    QGridLayout,
    QHeaderView,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from core.models.driver import (
    DriverInfo,
    DriverInventory,
)
from core.services.application_settings_service import (
    ApplicationSettingsService,
)
from core.services.driver_service import DriverService
from core.services.localization_service import (
    LocalizationService,
)
from infrastructure.logging.logger import get_logger


class DriverLoadWorker(QObject):
    """تشغيل فحص التعريفات خارج واجهة المستخدم."""

    finished = Signal(object)

    @Slot()
    def run(self) -> None:
        """قراءة تعريفات Windows."""

        service = DriverService()
        result = service.get_driver_inventory()

        self.finished.emit(result)


class DriverSummaryCard(QFrame):
    """بطاقة صغيرة لعرض إحصائية واحدة."""

    def __init__(
        self,
        title: str,
    ) -> None:
        super().__init__()

        self.setObjectName(
            "driverSummaryCard"
        )

        self.setMinimumHeight(
            110
        )

        layout = QVBoxLayout(
            self
        )

        layout.setContentsMargins(
            18,
            16,
            18,
            16,
        )

        layout.setSpacing(
            6
        )

        self.title_label = QLabel(
            title
        )

        self.title_label.setObjectName(
            "driverSummaryTitle"
        )

        self.title_label.setAlignment(
            Qt.AlignmentFlag.AlignLeading
            | Qt.AlignmentFlag.AlignVCenter
        )

        self.value_label = QLabel(
            "--"
        )

        self.value_label.setObjectName(
            "driverSummaryValue"
        )

        self.value_label.setAlignment(
            Qt.AlignmentFlag.AlignLeading
            | Qt.AlignmentFlag.AlignVCenter
        )

        layout.addWidget(
            self.title_label
        )

        layout.addWidget(
            self.value_label
        )

        layout.addStretch()

    def set_value(
        self,
        value: int | str,
    ) -> None:
        """تحديث قيمة البطاقة."""

        self.value_label.setText(
            str(value)
        )


class DriversPage(QWidget):
    """صفحة عرض تعريفات أجهزة Windows."""

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

        self.is_rtl = (
            self.localization.is_rtl
        )

        self.setObjectName(
            "page"
        )

        self.setLayoutDirection(
            Qt.LayoutDirection.RightToLeft
            if self.is_rtl
            else Qt.LayoutDirection.LeftToRight
        )

        self.logger = get_logger()

        self.inventory: DriverInventory | None = None

        self._load_thread: QThread | None = None
        self._load_worker: DriverLoadWorker | None = None
        self._loaded_once = False

        self._setup_ui()

    def _setup_ui(self) -> None:
        """إنشاء واجهة صفحة Drivers."""

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

        header_layout = QHBoxLayout()
        header_layout.setSpacing(
            12
        )

        title_layout = QVBoxLayout()
        title_layout.setSpacing(
            5
        )

        self.title_label = QLabel(
            self._text(
                "Drivers",
                "التعريفات",
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
                    "Inspect installed drivers and detect "
                    "missing, unsigned or problematic devices."
                ),
                (
                    "افحص التعريفات المثبتة واكتشف الأجهزة "
                    "ذات التعريفات المفقودة أو غير الموقعة "
                    "أو التي تحتوي على مشكلات."
                ),
            )
        )

        self.subtitle_label.setObjectName(
            "pageSubtitle"
        )

        self.subtitle_label.setWordWrap(
            True
        )

        self.subtitle_label.setAlignment(
            Qt.AlignmentFlag.AlignLeading
            | Qt.AlignmentFlag.AlignVCenter
        )

        title_layout.addWidget(
            self.title_label
        )

        title_layout.addWidget(
            self.subtitle_label
        )

        self.device_manager_button = QPushButton(
            self._text(
                "Open Device Manager",
                "فتح إدارة الأجهزة",
            )
        )

        self.device_manager_button.setObjectName(
            "secondaryButton"
        )

        self.device_manager_button.setMinimumHeight(
            42
        )

        self.device_manager_button.setCursor(
            Qt.CursorShape.PointingHandCursor
        )

        self.device_manager_button.clicked.connect(
            self._open_device_manager
        )

        self.refresh_button = QPushButton(
            self._text(
                "Refresh Drivers",
                "تحديث التعريفات",
            )
        )

        self.refresh_button.setObjectName(
            "refreshButton"
        )

        self.refresh_button.setMinimumHeight(
            42
        )

        self.refresh_button.setCursor(
            Qt.CursorShape.PointingHandCursor
        )

        self.refresh_button.clicked.connect(
            self._load_drivers
        )

        header_layout.addLayout(
            title_layout,
            1,
        )

        header_layout.addWidget(
            self.device_manager_button
        )

        header_layout.addWidget(
            self.refresh_button
        )

        self.error_label = QLabel()

        self.error_label.setObjectName(
            "driversErrorLabel"
        )

        self.error_label.setWordWrap(
            True
        )

        self.error_label.setVisible(
            False
        )

        self.error_label.setAlignment(
            Qt.AlignmentFlag.AlignLeading
            | Qt.AlignmentFlag.AlignVCenter
        )

        summary_layout = QGridLayout()

        summary_layout.setContentsMargins(
            0,
            0,
            0,
            0,
        )

        summary_layout.setHorizontalSpacing(
            12
        )

        summary_layout.setVerticalSpacing(
            12
        )

        self.total_card = DriverSummaryCard(
            self._text(
                "Detected Devices",
                "الأجهزة المكتشفة",
            )
        )

        self.working_card = DriverSummaryCard(
            self._text(
                "Working Correctly",
                "تعمل بشكل صحيح",
            )
        )

        self.problem_card = DriverSummaryCard(
            self._text(
                "Require Attention",
                "تحتاج إلى انتباه",
            )
        )

        self.missing_card = DriverSummaryCard(
            self._text(
                "Missing Drivers",
                "تعريفات مفقودة",
            )
        )

        self.unsigned_card = DriverSummaryCard(
            self._text(
                "Unsigned Drivers",
                "تعريفات غير موقعة",
            )
        )

        summary_cards = (
            self.total_card,
            self.working_card,
            self.problem_card,
            self.missing_card,
            self.unsigned_card,
        )

        for column, card in enumerate(
            summary_cards
        ):
            summary_layout.addWidget(
                card,
                0,
                column,
            )

            summary_layout.setColumnStretch(
                column,
                1,
            )

        filters_layout = QHBoxLayout()

        filters_layout.setSpacing(
            12
        )

        self.search_input = QLineEdit()

        self.search_input.setObjectName(
            "driverSearchBox"
        )

        self.search_input.setPlaceholderText(
            self._text(
                (
                    "Search by device, provider "
                    "or manufacturer..."
                ),
                (
                    "ابحث باسم الجهاز أو مزود التعريف "
                    "أو الشركة المصنعة..."
                ),
            )
        )

        self.search_input.setClearButtonEnabled(
            True
        )

        self.search_input.setMinimumHeight(
            42
        )

        self.search_input.textChanged.connect(
            self._apply_filters
        )

        self.status_filter = QComboBox()

        self.status_filter.setObjectName(
            "driverFilterBox"
        )

        self.status_filter.setMinimumHeight(
            42
        )

        self.status_filter.setMinimumWidth(
            170
        )

        self.status_filter.addItem(
            self._text(
                "All Statuses",
                "جميع الحالات",
            ),
            "all",
        )

        self.status_filter.addItem(
            self._text(
                "Working Correctly",
                "تعمل بشكل صحيح",
            ),
            "working",
        )

        self.status_filter.addItem(
            self._text(
                "Require Attention",
                "تحتاج إلى انتباه",
            ),
            "problems",
        )

        self.status_filter.addItem(
            self._text(
                "Missing Drivers",
                "تعريفات مفقودة",
            ),
            "missing",
        )

        self.status_filter.addItem(
            self._text(
                "Unsigned Drivers",
                "تعريفات غير موقعة",
            ),
            "unsigned",
        )

        self.status_filter.currentIndexChanged.connect(
            self._apply_filters
        )

        self.class_filter = QComboBox()

        self.class_filter.setObjectName(
            "driverFilterBox"
        )

        self.class_filter.setMinimumHeight(
            42
        )

        self.class_filter.setMinimumWidth(
            180
        )

        self.class_filter.addItem(
            self._text(
                "All Device Classes",
                "جميع فئات الأجهزة",
            ),
            "all",
        )

        self.class_filter.currentIndexChanged.connect(
            self._apply_filters
        )

        filters_layout.addWidget(
            self.search_input,
            1,
        )

        filters_layout.addWidget(
            self.status_filter
        )

        filters_layout.addWidget(
            self.class_filter
        )

        self.table = QTableWidget()

        self.table.setObjectName(
            "driversTable"
        )

        self.table.setColumnCount(
            7
        )

        self.table.setHorizontalHeaderLabels(
            [
                self._text(
                    "Device",
                    "الجهاز",
                ),
                self._text(
                    "Class",
                    "الفئة",
                ),
                self._text(
                    "Status",
                    "الحالة",
                ),
                self._text(
                    "Version",
                    "الإصدار",
                ),
                self._text(
                    "Date",
                    "التاريخ",
                ),
                self._text(
                    "Provider",
                    "المزود",
                ),
                self._text(
                    "Signed",
                    "موقّع",
                ),
            ]
        )

        self.table.setEditTriggers(
            QAbstractItemView.EditTrigger.NoEditTriggers
        )

        self.table.setSelectionBehavior(
            QAbstractItemView.SelectionBehavior.SelectRows
        )

        self.table.setSelectionMode(
            QAbstractItemView.SelectionMode.SingleSelection
        )

        self.table.setAlternatingRowColors(
            True
        )

        self.table.setSortingEnabled(
            True
        )

        self.table.verticalHeader().setVisible(
            False
        )

        self.table.verticalHeader().setDefaultSectionSize(
            40
        )

        header = self.table.horizontalHeader()

        header.setStretchLastSection(
            False
        )

        header.setDefaultAlignment(
            Qt.AlignmentFlag.AlignLeading
            | Qt.AlignmentFlag.AlignVCenter
        )

        header.setSectionResizeMode(
            0,
            QHeaderView.ResizeMode.Stretch,
        )

        for column in range(
            1,
            7,
        ):
            header.setSectionResizeMode(
                column,
                QHeaderView.ResizeMode.ResizeToContents,
            )

        self.result_label = QLabel(
            self._text(
                (
                    "Open the Drivers page "
                    "to start scanning."
                ),
                (
                    "افتح صفحة التعريفات "
                    "لبدء الفحص."
                ),
            )
        )

        self.result_label.setObjectName(
            "driversResultLabel"
        )

        self.result_label.setAlignment(
            Qt.AlignmentFlag.AlignLeading
            | Qt.AlignmentFlag.AlignVCenter
        )

        page_layout.addLayout(
            header_layout
        )

        page_layout.addWidget(
            self.error_label
        )

        page_layout.addLayout(
            summary_layout
        )

        page_layout.addLayout(
            filters_layout
        )

        page_layout.addWidget(
            self.table,
            1,
        )

        page_layout.addWidget(
            self.result_label
        )

    def showEvent(
        self,
        event: QShowEvent,
    ) -> None:
        """بدء الفحص عند فتح الصفحة أول مرة."""

        super().showEvent(
            event
        )

        if (
            not self._loaded_once
            and not self._is_loading()
        ):
            self._load_drivers()

    def _load_drivers(
        self,
        _checked: bool = False,
    ) -> None:
        """تشغيل فحص التعريفات في Thread منفصل."""

        if self._is_loading():
            return

        self._set_loading_state(
            True
        )

        self.error_label.setVisible(
            False
        )

        self._load_thread = QThread(
            self
        )

        self._load_worker = DriverLoadWorker()

        self._load_worker.moveToThread(
            self._load_thread
        )

        self._load_thread.started.connect(
            self._load_worker.run
        )

        self._load_worker.finished.connect(
            self._handle_driver_result
        )

        self._load_worker.finished.connect(
            self._load_thread.quit
        )

        self._load_worker.finished.connect(
            self._load_worker.deleteLater
        )

        self._load_thread.finished.connect(
            self._finish_loading
        )

        self._load_thread.finished.connect(
            self._load_thread.deleteLater
        )

        self._load_thread.start()

    def _handle_driver_result(
        self,
        result,
    ) -> None:
        """معالجة نتيجة فحص التعريفات."""

        if not result.success or result.data is None:
            self.inventory = None

            self.error_label.setText(
                self._text(
                    "Driver scan failed: ",
                    "فشل فحص التعريفات: ",
                )
                + f"{result.message}"
            )

            self.error_label.setVisible(
                True
            )

            self.result_label.setText(
                self._text(
                    (
                        "Windows driver information "
                        "could not be loaded."
                    ),
                    (
                        "تعذر تحميل معلومات تعريفات "
                        "ويندوز."
                    ),
                )
            )

            self.logger.error(
                "Drivers page failed to display data: %s",
                result.message,
            )

            return

        self.inventory = result.data
        self._loaded_once = True

        self._update_summary()
        self._populate_class_filter()
        self._apply_filters()

        self.logger.info(
            "Drivers page displayed successfully. "
            "Device count: %s",
            self.inventory.total_devices,
        )

    def _finish_loading(self) -> None:
        """تنظيف الـThread بعد انتهاء الفحص."""

        self._set_loading_state(
            False
        )

        self._load_worker = None
        self._load_thread = None

    def _set_loading_state(
        self,
        is_loading: bool,
    ) -> None:
        """تحديث حالة الفحص في الواجهة."""

        self.refresh_button.setEnabled(
            not is_loading
        )

        self.refresh_button.setText(
            self._text(
                (
                    "Scanning Drivers..."
                    if is_loading
                    else "Refresh Drivers"
                ),
                (
                    "جارٍ فحص التعريفات..."
                    if is_loading
                    else "تحديث التعريفات"
                ),
            )
        )

        if is_loading:
            self.result_label.setText(
                self._text(
                    (
                        "Reading Windows devices "
                        "and drivers..."
                    ),
                    (
                        "جارٍ قراءة أجهزة ويندوز "
                        "والتعريفات..."
                    ),
                )
            )

    def _update_summary(self) -> None:
        """تحديث بطاقات ملخص التعريفات."""

        if self.inventory is None:
            return

        self.total_card.set_value(
            self.inventory.total_devices
        )

        self.working_card.set_value(
            len(
                self.inventory.working_devices
            )
        )

        self.problem_card.set_value(
            len(
                self.inventory.problem_devices
            )
        )

        self.missing_card.set_value(
            len(
                self.inventory
                .missing_driver_devices
            )
        )

        self.unsigned_card.set_value(
            len(
                self.inventory
                .unsigned_driver_devices
            )
        )

    def _populate_class_filter(self) -> None:
        """إضافة فئات الأجهزة إلى فلتر الفئات."""

        if self.inventory is None:
            return

        current_value = (
            self.class_filter.currentData()
        )

        self.class_filter.blockSignals(
            True
        )

        self.class_filter.clear()

        self.class_filter.addItem(
            self._text(
                "All Device Classes",
                "جميع فئات الأجهزة",
            ),
            "all",
        )

        classes = sorted(
            {
                device.device_class
                for device in self.inventory.devices
                if device.device_class
                and device.device_class != "Unavailable"
            },
            key=str.lower,
        )

        for device_class in classes:
            self.class_filter.addItem(
                device_class,
                device_class,
            )

        index = self.class_filter.findData(
            current_value
        )

        if index >= 0:
            self.class_filter.setCurrentIndex(
                index
            )

        self.class_filter.blockSignals(
            False
        )

    def _apply_filters(self) -> None:
        """تطبيق البحث والفلاتر على التعريفات."""

        if self.inventory is None:
            self.table.setRowCount(
                0
            )

            return

        search_text = (
            self.search_input.text()
            .strip()
            .lower()
        )

        status_filter = (
            self.status_filter.currentData()
            or "all"
        )

        class_filter = (
            self.class_filter.currentData()
            or "all"
        )

        filtered_devices: list[DriverInfo] = []

        for device in self.inventory.devices:
            if not self._matches_search(
                device,
                search_text,
            ):
                continue

            if not self._matches_status(
                device,
                status_filter,
            ):
                continue

            if (
                class_filter != "all"
                and device.device_class
                != class_filter
            ):
                continue

            filtered_devices.append(
                device
            )

        self._populate_table(
            filtered_devices
        )

        self.result_label.setText(
            self._text(
                (
                    f"Showing {len(filtered_devices)} of "
                    f"{self.inventory.total_devices} devices."
                ),
                (
                    f"يتم عرض {len(filtered_devices)} من أصل "
                    f"{self.inventory.total_devices} جهاز."
                ),
            )
        )

    @staticmethod
    def _matches_search(
        device: DriverInfo,
        search_text: str,
    ) -> bool:
        """فحص تطابق الجهاز مع البحث."""

        if not search_text:
            return True

        searchable_values = (
            device.device_name,
            device.device_class,
            device.manufacturer,
            device.driver_provider,
            device.driver_version,
            device.inf_name,
        )

        return any(
            search_text in str(value).lower()
            for value in searchable_values
        )

    @staticmethod
    def _matches_status(
        device: DriverInfo,
        status_filter: str,
    ) -> bool:
        """فحص تطابق الجهاز مع فلتر الحالة."""

        if status_filter == "all":
            return True

        if status_filter == "working":
            return (
                device.is_working_correctly
                and device.is_signed is not False
            )

        if status_filter == "problems":
            return device.requires_attention

        if status_filter == "missing":
            return device.is_missing_driver

        if status_filter == "unsigned":
            return device.is_signed is False

        return True

    def _populate_table(
        self,
        devices: list[DriverInfo],
    ) -> None:
        """عرض الأجهزة داخل الجدول."""

        self.table.setSortingEnabled(
            False
        )

        self.table.setRowCount(
            len(devices)
        )

        item_alignment = (
            Qt.AlignmentFlag.AlignRight
            if self.is_rtl
            else Qt.AlignmentFlag.AlignLeft
        ) | Qt.AlignmentFlag.AlignVCenter

        for row, device in enumerate(
            devices
        ):
            status_text = self._get_status_text(
                device
            )

            signed_text = (
                self._text(
                    "Yes",
                    "نعم",
                )
                if device.is_signed is True
                else (
                    self._text(
                        "No",
                        "لا",
                    )
                    if device.is_signed is False
                    else self._text(
                        "Unknown",
                        "غير معروف",
                    )
                )
            )

            values = (
                device.device_name,
                device.device_class,
                status_text,
                device.driver_version,
                device.driver_date,
                device.driver_provider,
                signed_text,
            )

            for column, value in enumerate(
                values
            ):
                item = QTableWidgetItem(
                    self._display_value(
                        value
                    )
                )

                item.setTextAlignment(
                    item_alignment
                )

                self.table.setItem(
                    row,
                    column,
                    item,
                )

            details = (
                self._text(
                    "Device ID: ",
                    "معرّف الجهاز: ",
                )
                + f"{device.device_id}\n"
                + self._text(
                    "Manufacturer: ",
                    "الشركة المصنعة: ",
                )
                + f"{device.manufacturer}\n"
                + "INF: "
                + f"{device.inf_name}\n"
                + self._text(
                    "Signer: ",
                    "الموقّع: ",
                )
                + f"{device.signer}\n"
                + self._text(
                    "Status: ",
                    "الحالة: ",
                )
                + f"{device.device_status}\n"
                + self._text(
                    "Error Code: ",
                    "رمز الخطأ: ",
                )
                + f"{device.config_manager_error_code}\n"
                + self._text(
                    "Details: ",
                    "التفاصيل: ",
                )
                + f"{device.problem_description}"
            )

            for column in range(
                self.table.columnCount()
            ):
                table_item = self.table.item(
                    row,
                    column,
                )

                if table_item is not None:
                    table_item.setToolTip(
                        details
                    )

        self.table.setSortingEnabled(
            True
        )

    def _get_status_text(
        self,
        device: DriverInfo,
    ) -> str:
        """تنسيق حالة الجهاز."""

        if device.is_missing_driver:
            return self._text(
                "Missing Driver",
                "التعريف مفقود",
            )

        if device.is_signed is False:
            return self._text(
                "Unsigned",
                "غير موقّع",
            )

        if not device.is_working_correctly:
            return self._text(
                (
                    "Problem "
                    f"({device.config_manager_error_code})"
                ),
                (
                    "مشكلة "
                    f"({device.config_manager_error_code})"
                ),
            )

        return self._text(
            "Working",
            "يعمل",
        )

    def _open_device_manager(
        self,
        _checked: bool = False,
    ) -> None:
        """فتح Windows Device Manager."""

        try:
            subprocess.Popen(
                [
                    "mmc.exe",
                    "devmgmt.msc",
                ],
                close_fds=True,
            )

            self.logger.info(
                "Windows Device Manager opened"
            )

        except OSError as error:
            self.error_label.setText(
                self._text(
                    (
                        "Device Manager could not "
                        "be opened: "
                    ),
                    (
                        "تعذر فتح إدارة الأجهزة: "
                    ),
                )
                + f"{error}"
            )

            self.error_label.setVisible(
                True
            )

            self.logger.exception(
                "Failed to open Windows Device Manager"
            )

    def _is_loading(self) -> bool:
        """التحقق من وجود عملية فحص نشطة."""

        return (
            self._load_thread is not None
            and self._load_thread.isRunning()
        )

    def _display_value(
        self,
        value,
    ) -> str:
        """تنظيف القيمة قبل عرضها."""

        if value is None:
            return self._unavailable()

        cleaned_value = str(
            value
        ).strip()

        if (
            not cleaned_value
            or cleaned_value.casefold()
            == "unavailable"
        ):
            return self._unavailable()

        return cleaned_value

    def _unavailable(self) -> str:
        """إرجاع نص القيمة غير المتوفرة."""

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