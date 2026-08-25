import json
import tempfile
import time
import uuid
from pathlib import Path

from PySide6.QtCore import (
    QObject,
    QThread,
    QTimer,
    Qt,
    Signal,
    Slot,
)
from PySide6.QtGui import QShowEvent
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from core.models.cleaner import (
    CleanerCategoryScan,
    CleanerScanInventory,
)
from core.models.cleaner_cleanup import (
    CleanerCategoryCleanResult,
    CleanerCleanInventory,
)
from core.services.cleaner_cleanup_service import (
    CleanerCleanupService,
)
from core.services.application_settings_service import (
    ApplicationSettingsService,
)
from core.services.cleaner_service import CleanerService
from core.services.localization_service import (
    LocalizationService,
)
from infrastructure.logging.logger import get_logger
from infrastructure.system.windows_elevation import (
    ElevationRequestError,
    is_running_as_admin,
    request_elevated_python_module,
)


class CleanerScanWorker(QObject):
    """تشغيل فحص Cleaner خارج UI Thread."""

    finished = Signal(object)

    @Slot()
    def run(self) -> None:
        """تشغيل الفحص وإرسال النتيجة."""

        result = (
            CleanerService()
            .scan_cleanable_files()
        )

        self.finished.emit(result)


class CleanerCleanupWorker(QObject):
    """تشغيل تنظيف الأقسام خارج UI Thread."""

    finished = Signal(object)

    def __init__(
        self,
        category_keys: tuple[str, ...],
    ) -> None:
        super().__init__()

        self.category_keys = category_keys

    @Slot()
    def run(self) -> None:
        """تشغيل التنظيف وإرسال النتيجة."""

        result = (
            CleanerCleanupService()
            .clean_categories(
                self.category_keys
            )
        )

        self.finished.emit(result)


class CleanerCategoryCard(QFrame):
    """بطاقة قسم واحد من أقسام Cleaner."""

    selection_changed = Signal()

    def __init__(
        self,
        category: CleanerCategoryScan,
        is_rtl: bool = False,
    ) -> None:
        super().__init__()

        self.category = category
        self.is_rtl = is_rtl

        self.setLayoutDirection(
            Qt.LayoutDirection.RightToLeft
            if self.is_rtl
            else Qt.LayoutDirection.LeftToRight
        )

        self.setObjectName(
            "cleanerCategoryCard"
        )

        self._setup_ui()

    def _setup_ui(self) -> None:
        """إنشاء محتويات البطاقة."""

        layout = QVBoxLayout(self)
        layout.setContentsMargins(
            20,
            18,
            20,
            18,
        )
        layout.setSpacing(10)

        header_layout = QHBoxLayout()
        header_layout.setSpacing(10)

        self.checkbox = QCheckBox(
            self._translate_category_title()
        )
        self.checkbox.setObjectName(
            "cleanerCategoryCheckBox"
        )
        self.checkbox.setChecked(
            self.category.selected_by_default
        )
        self.checkbox.stateChanged.connect(
            lambda _state:
            self.selection_changed.emit()
        )

        risk_badge = QLabel(
            self._translate_risk_level()
        )
        risk_badge.setObjectName(
            "cleanerRiskBadge"
        )
        risk_badge.setProperty(
            "riskLevel",
            self.category.risk_level,
        )
        risk_badge.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )
        risk_badge.setMinimumWidth(80)
        risk_badge.setFixedHeight(26)

        header_layout.addWidget(
            self.checkbox,
            1,
        )
        header_layout.addWidget(
            risk_badge
        )

        if self.category.requires_admin:
            admin_badge = QLabel(
                self._text(
                    "ADMIN",
                    "مسؤول",
                )
            )
            admin_badge.setObjectName(
                "cleanerAdminBadge"
            )
            admin_badge.setAlignment(
                Qt.AlignmentFlag.AlignCenter
            )
            admin_badge.setMinimumWidth(70)
            admin_badge.setFixedHeight(26)

            header_layout.addWidget(
                admin_badge
            )

        description = QLabel(
            self._translate_category_description()
        )
        description.setObjectName(
            "cleanerCategoryDescription"
        )
        description.setWordWrap(True)

        stats_layout = QHBoxLayout()
        stats_layout.setSpacing(25)

        stats_layout.addWidget(
            self._create_stat(
                title=self._text(
                    "Detected Size",
                    "الحجم المكتشف",
                ),
                value=self._format_size(
                    self.category.total_size_bytes
                ),
            )
        )

        stats_layout.addWidget(
            self._create_stat(
                title=self._text(
                    "Detected Items",
                    "العناصر المكتشفة",
                ),
                value=(
                    f"{self.category.file_count:,}"
                ),
            )
        )

        stats_layout.addWidget(
            self._create_stat(
                title=self._text(
                    "Skipped",
                    "تم تخطيها",
                ),
                value=(
                    f"{self.category.skipped_items:,}"
                ),
            )
        )

        stats_layout.addStretch()

        notes: list[str] = []

        if self.category.minimum_age_hours:
            notes.append(
                self._text(
                    (
                        "Only files older than "
                        f"{self.category.minimum_age_hours} "
                        "hour(s) are included."
                    ),
                    (
                        "يتم تضمين الملفات الأقدم من "
                        f"{self.category.minimum_age_hours} "
                        "ساعة فقط."
                    ),
                )
            )

        if self.category.requires_admin:
            notes.append(
                self._text(
                    (
                        "Administrator permission may be "
                        "required to scan or clean every item."
                    ),
                    (
                        "قد تكون صلاحية المسؤول مطلوبة "
                        "لفحص أو تنظيف جميع العناصر."
                    ),
                )
            )

        if self.category.skipped_items:
            notes.append(
                self._text(
                    (
                        f"{self.category.skipped_items:,} "
                        "item(s) could not be accessed "
                        "or were locked."
                    ),
                    (
                        f"تعذر الوصول إلى "
                        f"{self.category.skipped_items:,} "
                        "عنصر أو كانت مقفلة."
                    ),
                )
            )

        if self.category.missing_paths:
            notes.append(
                self._text(
                    (
                        f"{len(self.category.missing_paths)} "
                        "configured path(s) were not found."
                    ),
                    (
                        f"لم يتم العثور على "
                        f"{len(self.category.missing_paths)} "
                        "مسار مضبوط."
                    ),
                )
            )

        notes.extend(
            self._translate_warning(
                warning
            )
            for warning in self.category.warnings
        )

        notes_label = QLabel(
            "\n".join(notes)
        )
        notes_label.setObjectName(
            "cleanerCategoryNotes"
        )
        notes_label.setWordWrap(True)
        notes_label.setVisible(
            bool(notes)
        )

        layout.addLayout(
            header_layout
        )
        layout.addWidget(
            description
        )
        layout.addLayout(
            stats_layout
        )
        layout.addWidget(
            notes_label
        )

    @staticmethod
    def _create_stat(
        title: str,
        value: str,
    ) -> QWidget:
        """إنشاء إحصائية داخل البطاقة."""

        container = QWidget()
        container.setObjectName(
            "cleanerStatContainer"
        )

        layout = QVBoxLayout(
            container
        )
        layout.setContentsMargins(
            0,
            0,
            0,
            0,
        )
        layout.setSpacing(2)

        title_label = QLabel(title)
        title_label.setObjectName(
            "cleanerStatTitle"
        )

        value_label = QLabel(value)
        value_label.setObjectName(
            "cleanerStatValue"
        )

        layout.addWidget(
            title_label
        )
        layout.addWidget(
            value_label
        )

        return container

    def _translate_category_title(self) -> str:
        """ترجمة اسم قسم التنظيف."""

        if not self.is_rtl:
            return self.category.title

        titles = {
            "user_temp": "ملفات المستخدم المؤقتة",
            "windows_temp": "ملفات ويندوز المؤقتة",
            "browser_cache": "ذاكرة المتصفح المؤقتة",
            "recycle_bin": "سلة المحذوفات",
            "thumbnail_cache": "ذاكرة الصور المصغرة",
            "directx_shader_cache": "ذاكرة DirectX Shader",
            "delivery_optimization": "ملفات تحسين التسليم",
            "windows_update_cache": "ذاكرة تحديثات ويندوز",
            "crash_dumps": "ملفات تقارير التعطل",
            "windows_error_reports": "تقارير أخطاء ويندوز",
            "log_files": "ملفات السجل",
        }

        key = str(
            self.category.key
        ).strip().casefold()

        return titles.get(
            key,
            self.category.title,
        )

    def _translate_category_description(self) -> str:
        """ترجمة وصف قسم التنظيف عند توفره."""

        if not self.is_rtl:
            return self.category.description

        descriptions = {
            "user_temp": (
                "ملفات مؤقتة أنشأتها برامج المستخدم "
                "ويمكن تنظيفها بأمان."
            ),
            "windows_temp": (
                "ملفات مؤقتة أنشأها ويندوز والبرامج "
                "أثناء التشغيل."
            ),
            "browser_cache": (
                "ملفات مؤقتة تحفظها المتصفحات لتسريع "
                "تحميل المواقع."
            ),
            "recycle_bin": (
                "الملفات الموجودة داخل سلة المحذوفات."
            ),
            "thumbnail_cache": (
                "نسخ مصغرة يحتفظ بها ويندوز للصور "
                "وملفات الوسائط."
            ),
            "directx_shader_cache": (
                "ملفات Shader مؤقتة تنشئها الألعاب "
                "وبرامج الرسوم."
            ),
            "delivery_optimization": (
                "ملفات مؤقتة يستخدمها ويندوز لتحسين "
                "تنزيل التحديثات."
            ),
            "windows_update_cache": (
                "ملفات تحديثات ويندوز المؤقتة التي "
                "لم تعد مطلوبة."
            ),
            "crash_dumps": (
                "ملفات تشخيص تم إنشاؤها بعد تعطل "
                "البرامج أو النظام."
            ),
            "windows_error_reports": (
                "تقارير تشخيص أخطاء ويندوز المحفوظة."
            ),
            "log_files": (
                "ملفات سجلات مؤقتة أنشأها النظام "
                "والبرامج."
            ),
        }

        key = str(
            self.category.key
        ).strip().casefold()

        return descriptions.get(
            key,
            self.category.description,
        )

    def _translate_risk_level(self) -> str:
        """ترجمة مستوى الخطورة."""

        risk_level = str(
            self.category.risk_level
        ).strip().casefold()

        if not self.is_rtl:
            return risk_level.upper()

        values = {
            "low": "منخفض",
            "medium": "متوسط",
            "high": "مرتفع",
            "safe": "آمن",
        }

        return values.get(
            risk_level,
            self.category.risk_level,
        )

    def _translate_warning(
        self,
        warning: str,
    ) -> str:
        """ترجمة تحذيرات Cleaner المعروفة."""

        if not self.is_rtl:
            return warning

        translations = {
            (
                "Recycle Bin contents will be "
                "permanently deleted."
            ): (
                "سيتم حذف محتويات سلة المحذوفات "
                "بشكل نهائي."
            ),
            (
                "Administrator permission may be required."
            ): (
                "قد تكون صلاحية المسؤول مطلوبة."
            ),
        }

        return translations.get(
            warning,
            warning,
        )

    def _text(
        self,
        english: str,
        arabic: str,
    ) -> str:
        """اختيار النص حسب لغة الواجهة."""

        if self.is_rtl:
            return arabic

        return english

    def is_selected(self) -> bool:
        """هل القسم محدد؟"""

        return self.checkbox.isChecked()

    @staticmethod
    def _format_size(
        size_bytes: int,
    ) -> str:
        """تنسيق الحجم تلقائيًا."""

        value = max(
            0.0,
            float(size_bytes),
        )

        units = (
            "B",
            "KB",
            "MB",
            "GB",
            "TB",
        )

        unit_index = 0

        while (
            value >= 1024
            and unit_index < len(units) - 1
        ):
            value /= 1024
            unit_index += 1

        if unit_index == 0:
            return (
                f"{value:.0f} "
                f"{units[unit_index]}"
            )

        return (
            f"{value:.2f} "
            f"{units[unit_index]}"
        )


class CleanerPage(QWidget):
    """صفحة فحص وتنظيف الملفات المؤقتة بأمان."""

    ADMIN_SCAN_TIMEOUT_SECONDS = 180
    ADMIN_CLEAN_TIMEOUT_SECONDS = 300
    ADMIN_POLL_INTERVAL_MS = 350

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

        self.setObjectName("page")

        self.setLayoutDirection(
            Qt.LayoutDirection.RightToLeft
            if self.is_rtl
            else Qt.LayoutDirection.LeftToRight
        )

        self.logger = get_logger()

        self.inventory: (
            CleanerScanInventory | None
        ) = None

        self.category_cards: dict[
            str,
            CleanerCategoryCard,
        ] = {}

        self._scan_thread: (
            QThread | None
        ) = None

        self._scan_worker: (
            CleanerScanWorker | None
        ) = None

        self._scan_is_elevated = False
        self._scanned_once = False

        self._cleanup_thread: (
            QThread | None
        ) = None

        self._cleanup_worker: (
            CleanerCleanupWorker | None
        ) = None

        self._rescan_after_cleanup = False

        self._admin_scan_result_path: (
            Path | None
        ) = None

        self._admin_scan_deadline = 0.0

        self._admin_scan_timer = QTimer(
            self
        )
        self._admin_scan_timer.setInterval(
            self.ADMIN_POLL_INTERVAL_MS
        )
        self._admin_scan_timer.timeout.connect(
            self._poll_admin_scan_result
        )

        self._admin_cleanup_result_path: (
            Path | None
        ) = None

        self._admin_cleanup_deadline = 0.0

        self._admin_cleanup_timer = QTimer(
            self
        )
        self._admin_cleanup_timer.setInterval(
            self.ADMIN_POLL_INTERVAL_MS
        )
        self._admin_cleanup_timer.timeout.connect(
            self._poll_admin_cleanup_result
        )

        self._setup_ui()

    def _setup_ui(self) -> None:
        """إنشاء واجهة Cleaner."""

        page_layout = QVBoxLayout(
            self
        )
        page_layout.setContentsMargins(
            40,
            35,
            40,
            35,
        )
        page_layout.setSpacing(18)

        header_layout = QHBoxLayout()
        header_layout.setSpacing(12)

        title_layout = QVBoxLayout()
        title_layout.setSpacing(5)

        title = QLabel(
            self._text(
                "Cleaner",
                "تنظيف الجهاز",
            )
        )
        title.setObjectName(
            "pageTitle"
        )

        subtitle = QLabel(
            self._text(
                (
                    "Scan temporary and unnecessary "
                    "files before safely cleaning "
                    "selected categories."
                ),
                (
                    "افحص الملفات المؤقتة وغير الضرورية "
                    "قبل تنظيف الأقسام المحددة بأمان."
                ),
            )
        )
        subtitle.setObjectName(
            "pageSubtitle"
        )

        title_layout.addWidget(
            title
        )
        title_layout.addWidget(
            subtitle
        )

        self.admin_scan_button = QPushButton(
            self._text(
                "Rescan as Administrator",
                "إعادة الفحص كمسؤول",
            )
        )
        self.admin_scan_button.setObjectName(
            "secondaryButton"
        )
        self.admin_scan_button.setMinimumHeight(
            42
        )
        self.admin_scan_button.setCursor(
            Qt.CursorShape.PointingHandCursor
        )
        self.admin_scan_button.setToolTip(
            self._text(
                (
                    "Request Administrator permission "
                    "and repeat the scan with elevated access."
                ),
                (
                    "طلب صلاحية المسؤول وإعادة الفحص "
                    "بصلاحيات مرتفعة."
                ),
            )
        )
        self.admin_scan_button.clicked.connect(
            self._start_admin_scan
        )

        self.scan_button = QPushButton(
            self._text(
                "Scan Files",
                "فحص الملفات",
            )
        )
        self.scan_button.setObjectName(
            "refreshButton"
        )
        self.scan_button.setMinimumHeight(
            42
        )
        self.scan_button.setCursor(
            Qt.CursorShape.PointingHandCursor
        )
        self.scan_button.clicked.connect(
            lambda _checked=False:
            self._start_scan()
        )

        header_layout.addLayout(
            title_layout,
            1,
        )
        header_layout.addWidget(
            self.admin_scan_button
        )
        header_layout.addWidget(
            self.scan_button
        )

        self.error_label = QLabel()
        self.error_label.setObjectName(
            "cleanerErrorLabel"
        )
        self.error_label.setWordWrap(
            True
        )
        self.error_label.setVisible(
            False
        )

        summary_card = QFrame()
        summary_card.setObjectName(
            "cleanerSummaryCard"
        )

        summary_layout = QHBoxLayout(
            summary_card
        )
        summary_layout.setContentsMargins(
            22,
            18,
            22,
            18,
        )
        summary_layout.setSpacing(35)

        self.total_size_label = (
            self._create_summary_value(
                summary_layout,
                self._text(
                    "Total Detected",
                    "إجمالي المكتشف",
                ),
            )
        )

        self.total_items_label = (
            self._create_summary_value(
                summary_layout,
                self._text(
                    "Total Items",
                    "إجمالي العناصر",
                ),
            )
        )

        self.selected_size_label = (
            self._create_summary_value(
                summary_layout,
                self._text(
                    "Selected Size",
                    "الحجم المحدد",
                ),
            )
        )

        self.selected_items_label = (
            self._create_summary_value(
                summary_layout,
                self._text(
                    "Selected Items",
                    "العناصر المحددة",
                ),
            )
        )

        summary_layout.addStretch()

        self.clean_button = QPushButton(
            self._text(
                "Clean Selected",
                "تنظيف المحدد",
            )
        )
        self.clean_button.setObjectName(
            "cleanSelectedButton"
        )
        self.clean_button.setMinimumHeight(
            44
        )
        self.clean_button.setMinimumWidth(
            160
        )
        self.clean_button.setEnabled(
            False
        )
        self.clean_button.setCursor(
            Qt.CursorShape.PointingHandCursor
        )
        self.clean_button.setToolTip(
            self._text(
                (
                    "Delete files from the selected "
                    "Cleaner categories after confirmation."
                ),
                (
                    "حذف الملفات من أقسام التنظيف المحددة "
                    "بعد التأكيد."
                ),
            )
        )
        self.clean_button.clicked.connect(
            self._confirm_cleanup
        )

        summary_layout.addWidget(
            self.clean_button
        )

        scroll_area = QScrollArea()
        scroll_area.setObjectName(
            "cleanerScrollArea"
        )
        scroll_area.setWidgetResizable(
            True
        )
        scroll_area.setFrameShape(
            QFrame.Shape.NoFrame
        )
        scroll_area.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )

        scroll_content = QWidget()
        scroll_content.setObjectName(
            "cleanerScrollContent"
        )

        self.categories_layout = QVBoxLayout(
            scroll_content
        )
        self.categories_layout.setContentsMargins(
            0,
            0,
            10,
            0,
        )
        self.categories_layout.setSpacing(
            14
        )
        self.categories_layout.addStretch()

        scroll_area.setWidget(
            scroll_content
        )

        self.status_label = QLabel(
            self._text(
                "Open Cleaner to begin scanning.",
                "افتح أداة التنظيف لبدء الفحص.",
            )
        )
        self.status_label.setObjectName(
            "cleanerStatusLabel"
        )

        page_layout.addLayout(
            header_layout
        )
        page_layout.addWidget(
            self.error_label
        )
        page_layout.addWidget(
            summary_card
        )
        page_layout.addWidget(
            scroll_area,
            1,
        )
        page_layout.addWidget(
            self.status_label
        )

    def showEvent(
        self,
        event: QShowEvent,
    ) -> None:
        """تشغيل الفحص عند فتح الصفحة."""

        super().showEvent(event)

        if (
            not self._scanned_once
            and not self._is_busy()
        ):
            self._start_scan()

    def _start_scan(
        self,
        elevated_context: bool = False,
    ) -> None:
        """تشغيل الفحص العادي."""

        if self._is_busy():
            return

        self._scan_is_elevated = (
            elevated_context
        )

        self._set_scanning_state(
            True
        )

        self.error_label.setVisible(
            False
        )

        self._scan_thread = QThread(
            self
        )
        self._scan_worker = (
            CleanerScanWorker()
        )

        self._scan_worker.moveToThread(
            self._scan_thread
        )

        self._scan_thread.started.connect(
            self._scan_worker.run
        )
        self._scan_worker.finished.connect(
            self._handle_scan_result
        )
        self._scan_worker.finished.connect(
            self._scan_thread.quit
        )
        self._scan_worker.finished.connect(
            self._scan_worker.deleteLater
        )
        self._scan_thread.finished.connect(
            self._finish_scan
        )
        self._scan_thread.finished.connect(
            self._scan_thread.deleteLater
        )

        self._scan_thread.start()

    def _handle_scan_result(
        self,
        result,
    ) -> None:
        """معالجة نتيجة الفحص."""

        if (
            not result.success
            or result.data is None
        ):
            self.inventory = None

            self.error_label.setText(
                self._text(
                    "Cleaner scan failed: ",
                    "فشل فحص التنظيف: ",
                )
                + f"{result.message}"
            )
            self.error_label.setVisible(
                True
            )

            self.status_label.setText(
                self._text(
                    (
                        "The cleaner scan could "
                        "not be completed."
                    ),
                    (
                        "تعذر إكمال فحص التنظيف."
                    ),
                )
            )

            self.logger.error(
                "Cleaner page failed to "
                "display scan: %s",
                result.message,
            )
            return

        self._apply_inventory(
            inventory=result.data,
            elevated=self._scan_is_elevated,
        )

    def _finish_scan(self) -> None:
        """إنهاء Thread الفحص."""

        self._scan_is_elevated = False
        self._scan_worker = None
        self._scan_thread = None

        self._set_scanning_state(
            False
        )

    def _start_admin_scan(self) -> None:
        """تشغيل الفحص بصلاحية Administrator."""

        if self._is_busy():
            return

        if is_running_as_admin():
            self._start_scan(
                elevated_context=True
            )
            return

        try:
            result_path = (
                self._create_admin_result_path(
                    "cleaner_scan"
                )
            )

            request_elevated_python_module(
                module_name=(
                    "core.services."
                    "cleaner_admin_scan_runner"
                ),
                arguments=[
                    "--output",
                    str(result_path),
                ],
            )

        except (
            ElevationRequestError,
            OSError,
        ) as error:
            self._show_error(
                message=str(error),
                status=self._text(
                    (
                        "Administrator scan "
                        "was not started."
                    ),
                    (
                        "لم يبدأ الفحص بصلاحية المسؤول."
                    ),
                ),
            )
            return

        self._admin_scan_result_path = (
            result_path
        )

        self._admin_scan_deadline = (
            time.monotonic()
            + self.ADMIN_SCAN_TIMEOUT_SECONDS
        )

        self._set_admin_scan_state(
            True
        )

        self.status_label.setText(
            self._text(
                (
                    "Waiting for the Administrator "
                    "scan. Approve the Windows UAC prompt..."
                ),
                (
                    "بانتظار فحص المسؤول. وافق على رسالة "
                    "صلاحيات ويندوز UAC..."
                ),
            )
        )

        self._admin_scan_timer.start()

    def _poll_admin_scan_result(self) -> None:
        """انتظار نتيجة Admin Scan."""

        result_path = (
            self._admin_scan_result_path
        )

        if result_path is None:
            self._finish_admin_scan_state()
            return

        if result_path.is_file():
            try:
                payload = (
                    self._read_json_payload(
                        result_path
                    )
                )

                self._handle_admin_scan_payload(
                    payload
                )

            except Exception as error:
                self.logger.exception(
                    "Failed to process "
                    "administrator Cleaner scan result"
                )

                self._show_error(
                    message=self._text(
                        (
                            "Administrator scan returned "
                            f"invalid data: {error}"
                        ),
                        (
                            "أعاد فحص المسؤول بيانات "
                            f"غير صالحة: {error}"
                        ),
                    ),
                    status=self._text(
                        (
                            "Administrator scan could "
                            "not be processed."
                        ),
                        (
                            "تعذر معالجة نتيجة فحص المسؤول."
                        ),
                    ),
                )

            finally:
                self._delete_temp_file(
                    result_path
                )
                self._finish_admin_scan_state()

            return

        if (
            time.monotonic()
            >= self._admin_scan_deadline
        ):
            self._show_error(
                message=self._text(
                    (
                        "Administrator scan timed out. "
                        "The elevated process may have "
                        "been closed or blocked."
                    ),
                    (
                        "انتهت مهلة فحص المسؤول. ربما تم "
                        "إغلاق العملية أو حظرها."
                    ),
                ),
                status=self._text(
                    "Administrator scan timed out.",
                    "انتهت مهلة فحص المسؤول.",
                ),
            )

            self._delete_temp_file(
                result_path
            )

            self._finish_admin_scan_state()

    def _handle_admin_scan_payload(
        self,
        payload: dict,
    ) -> None:
        """تحويل نتيجة Admin Scan."""

        if not payload.get("success"):
            self._show_error(
                message=self._text(
                    (
                        "Administrator scan failed: "
                        f"{payload.get('message', 'Unknown error')}"
                    ),
                    (
                        "فشل فحص المسؤول: "
                        f"{payload.get('message', 'خطأ غير معروف')}"
                    ),
                ),
                status=self._text(
                    "Administrator scan failed.",
                    "فشل فحص المسؤول.",
                ),
            )
            return

        inventory = (
            self._deserialize_scan_inventory(
                payload.get("data")
            )
        )

        self.error_label.setVisible(
            False
        )

        self._apply_inventory(
            inventory=inventory,
            elevated=True,
        )

    def _finish_admin_scan_state(
        self,
    ) -> None:
        """إعادة الواجهة بعد Admin Scan."""

        self._admin_scan_timer.stop()

        self._admin_scan_result_path = None
        self._admin_scan_deadline = 0.0

        self._set_admin_scan_state(
            False
        )

        self._update_summary()

    def _confirm_cleanup(self) -> None:
        """إظهار تأكيد قبل التنظيف."""

        if (
            self.inventory is None
            or self._is_busy()
        ):
            return

        selected = (
            self._selected_categories()
        )

        if not selected:
            QMessageBox.information(
                self,
                self._text(
                    "Cleaner",
                    "تنظيف الجهاز",
                ),
                self._text(
                    (
                        "Select at least one category "
                        "that contains detected items."
                    ),
                    (
                        "حدد قسمًا واحدًا على الأقل "
                        "يحتوي على عناصر مكتشفة."
                    ),
                ),
            )
            return

        selected_size = sum(
            category.total_size_bytes
            for category in selected
        )

        selected_items = sum(
            category.file_count
            for category in selected
        )

        category_names = "\n".join(
            (
                f"• {self._category_title(category)} — "
                f"{category.file_count:,} "
                + self._text(
                    "item(s), ",
                    "عنصر، ",
                )
                + f"{self._format_size(category.total_size_bytes)}"
            )
            for category in selected
        )

        warnings = [
            self._text(
                (
                    "Locked or protected files "
                    "will be skipped."
                ),
                (
                    "سيتم تخطي الملفات المقفلة "
                    "أو المحمية."
                ),
            ),
            self._text(
                (
                    "Only the selected Cleaner "
                    "categories will be processed."
                ),
                (
                    "ستتم معالجة أقسام التنظيف "
                    "المحددة فقط."
                ),
            ),
        ]

        if any(
            category.key == "recycle_bin"
            for category in selected
        ):
            warnings.append(
                self._text(
                    (
                        "Recycle Bin contents will "
                        "be permanently deleted."
                    ),
                    (
                        "سيتم حذف محتويات سلة المحذوفات "
                        "بشكل نهائي."
                    ),
                )
            )

        if any(
            category.requires_admin
            for category in selected
        ):
            warnings.append(
                self._text(
                    (
                        "Windows may request "
                        "Administrator permission."
                    ),
                    (
                        "قد يطلب ويندوز صلاحية المسؤول."
                    ),
                )
            )

        message_box = QMessageBox(
            self
        )
        message_box.setWindowTitle(
            self._text(
                "Confirm Cleaner",
                "تأكيد التنظيف",
            )
        )
        message_box.setIcon(
            QMessageBox.Icon.Warning
        )
        message_box.setText(
            self._text(
                (
                    f"Clean {selected_items:,} "
                    "selected item(s)?"
                ),
                (
                    f"تنظيف {selected_items:,} "
                    "عنصر محدد؟"
                ),
            )
        )
        message_box.setInformativeText(
            (
                self._text(
                    "Estimated size: ",
                    "الحجم التقديري: ",
                )
                + f"{self._format_size(selected_size)}"
                + self._text(
                    "\n\nSelected categories:\n",
                    "\n\nالأقسام المحددة:\n",
                )
                + f"{category_names}"
                + "\n\n"
                + "\n".join(warnings)
            )
        )
        message_box.setStandardButtons(
            QMessageBox.StandardButton.Yes
            | QMessageBox.StandardButton.Cancel
        )
        message_box.setDefaultButton(
            QMessageBox.StandardButton.Cancel
        )

        answer = message_box.exec()

        if (
            answer
            != QMessageBox.StandardButton.Yes
        ):
            return

        category_keys = tuple(
            category.key
            for category in selected
        )

        requires_admin = any(
            category.requires_admin
            for category in selected
        )

        if (
            requires_admin
            and not is_running_as_admin()
        ):
            self._start_admin_cleanup(
                category_keys
            )
        else:
            self._start_local_cleanup(
                category_keys
            )

    def _start_local_cleanup(
        self,
        category_keys: tuple[str, ...],
    ) -> None:
        """تشغيل التنظيف بدون عملية UAC منفصلة."""

        if self._is_busy():
            return

        self._set_cleanup_state(
            True
        )

        self.error_label.setVisible(
            False
        )

        self._cleanup_thread = QThread(
            self
        )
        self._cleanup_worker = (
            CleanerCleanupWorker(
                category_keys
            )
        )

        self._cleanup_worker.moveToThread(
            self._cleanup_thread
        )

        self._cleanup_thread.started.connect(
            self._cleanup_worker.run
        )
        self._cleanup_worker.finished.connect(
            self._handle_cleanup_result
        )
        self._cleanup_worker.finished.connect(
            self._cleanup_thread.quit
        )
        self._cleanup_worker.finished.connect(
            self._cleanup_worker.deleteLater
        )
        self._cleanup_thread.finished.connect(
            self._finish_local_cleanup
        )
        self._cleanup_thread.finished.connect(
            self._cleanup_thread.deleteLater
        )

        self._cleanup_thread.start()

    def _handle_cleanup_result(
        self,
        result,
    ) -> None:
        """معالجة نتيجة التنظيف العادي."""

        if (
            not result.success
            or result.data is None
        ):
            self._show_error(
                message=self._text(
                    (
                        "Cleaner failed: "
                        f"{result.message}"
                    ),
                    (
                        "فشل التنظيف: "
                        f"{result.message}"
                    ),
                ),
                status=self._text(
                    (
                        "The selected categories "
                        "could not be cleaned."
                    ),
                    (
                        "تعذر تنظيف الأقسام المحددة."
                    ),
                ),
            )

            self._rescan_after_cleanup = False
            return

        self._show_cleanup_report(
            result.data
        )

        self._rescan_after_cleanup = True

    def _finish_local_cleanup(self) -> None:
        """إنهاء Thread التنظيف."""

        should_rescan = (
            self._rescan_after_cleanup
        )

        self._rescan_after_cleanup = False
        self._cleanup_worker = None
        self._cleanup_thread = None

        self._set_cleanup_state(
            False
        )

        if should_rescan:
            QTimer.singleShot(
                0,
                self._start_scan,
            )

    def _start_admin_cleanup(
        self,
        category_keys: tuple[str, ...],
    ) -> None:
        """تشغيل التنظيف بصلاحية Administrator."""

        if self._is_busy():
            return

        try:
            result_path = (
                self._create_admin_result_path(
                    "cleaner_cleanup"
                )
            )

            request_elevated_python_module(
                module_name=(
                    "core.services."
                    "cleaner_admin_cleanup_runner"
                ),
                arguments=[
                    "--output",
                    str(result_path),
                    "--categories",
                    *category_keys,
                ],
            )

        except (
            ElevationRequestError,
            OSError,
        ) as error:
            self._show_error(
                message=str(error),
                status=self._text(
                    (
                        "Administrator cleaning "
                        "was not started."
                    ),
                    (
                        "لم يبدأ التنظيف بصلاحية المسؤول."
                    ),
                ),
            )
            return

        self._admin_cleanup_result_path = (
            result_path
        )

        self._admin_cleanup_deadline = (
            time.monotonic()
            + self.ADMIN_CLEAN_TIMEOUT_SECONDS
        )

        self._set_cleanup_state(
            True
        )

        self.status_label.setText(
            self._text(
                (
                    "Waiting for Administrator cleaning. "
                    "Approve the Windows UAC prompt..."
                ),
                (
                    "بانتظار التنظيف بصلاحية المسؤول. "
                    "وافق على رسالة UAC..."
                ),
            )
        )

        self._admin_cleanup_timer.start()

    def _poll_admin_cleanup_result(
        self,
    ) -> None:
        """انتظار نتيجة التنظيف كمسؤول."""

        result_path = (
            self._admin_cleanup_result_path
        )

        if result_path is None:
            self._finish_admin_cleanup_state(
                False
            )
            return

        if result_path.is_file():
            should_rescan = False

            try:
                payload = (
                    self._read_json_payload(
                        result_path
                    )
                )

                should_rescan = (
                    self._handle_admin_cleanup_payload(
                        payload
                    )
                )

            except Exception as error:
                self.logger.exception(
                    "Failed to process administrator "
                    "Cleaner result"
                )

                self._show_error(
                    message=self._text(
                        (
                            "Administrator cleaning returned "
                            f"invalid data: {error}"
                        ),
                        (
                            "أعاد تنظيف المسؤول بيانات "
                            f"غير صالحة: {error}"
                        ),
                    ),
                    status=self._text(
                        (
                            "Administrator cleaning could "
                            "not be processed."
                        ),
                        (
                            "تعذر معالجة نتيجة تنظيف المسؤول."
                        ),
                    ),
                )

            finally:
                self._delete_temp_file(
                    result_path
                )

                self._finish_admin_cleanup_state(
                    should_rescan
                )

            return

        if (
            time.monotonic()
            >= self._admin_cleanup_deadline
        ):
            self._show_error(
                message=self._text(
                    (
                        "Administrator cleaning timed out. "
                        "The elevated process may have "
                        "been closed or blocked."
                    ),
                    (
                        "انتهت مهلة تنظيف المسؤول. ربما تم "
                        "إغلاق العملية أو حظرها."
                    ),
                ),
                status=self._text(
                    "Administrator cleaning timed out.",
                    "انتهت مهلة تنظيف المسؤول.",
                ),
            )

            self._delete_temp_file(
                result_path
            )

            self._finish_admin_cleanup_state(
                False
            )

    def _handle_admin_cleanup_payload(
        self,
        payload: dict,
    ) -> bool:
        """تحويل تقرير التنظيف كمسؤول."""

        if not payload.get("success"):
            self._show_error(
                message=self._text(
                    (
                        "Administrator cleaning failed: "
                        f"{payload.get('message', 'Unknown error')}"
                    ),
                    (
                        "فشل تنظيف المسؤول: "
                        f"{payload.get('message', 'خطأ غير معروف')}"
                    ),
                ),
                status=self._text(
                    "Administrator cleaning failed.",
                    "فشل تنظيف المسؤول.",
                ),
            )
            return False

        inventory = (
            self._deserialize_cleanup_inventory(
                payload.get("data")
            )
        )

        self.error_label.setVisible(
            False
        )

        self._show_cleanup_report(
            inventory
        )

        return True

    def _finish_admin_cleanup_state(
        self,
        should_rescan: bool,
    ) -> None:
        """إعادة الواجهة بعد Admin Cleanup."""

        self._admin_cleanup_timer.stop()

        self._admin_cleanup_result_path = None
        self._admin_cleanup_deadline = 0.0

        self._set_cleanup_state(
            False
        )

        if should_rescan:
            QTimer.singleShot(
                0,
                self._start_scan,
            )

    def _apply_inventory(
        self,
        inventory: CleanerScanInventory,
        elevated: bool,
    ) -> None:
        """عرض نتيجة الفحص."""

        self.inventory = inventory
        self._scanned_once = True

        self._render_categories()
        self._update_summary()

        scan_type = self._text(
            (
                "Administrator scan"
                if elevated
                else "Standard scan"
            ),
            (
                "فحص المسؤول"
                if elevated
                else "الفحص العادي"
            ),
        )

        self.status_label.setText(
            self._text(
                (
                    f"{scan_type} completed: "
                    f"{inventory.total_file_count:,} "
                    "item(s), "
                    f"{self._format_size(inventory.total_size_bytes)} "
                    "detected."
                ),
                (
                    f"اكتمل {scan_type}: تم اكتشاف "
                    f"{inventory.total_file_count:,} عنصر، "
                    f"بحجم "
                    f"{self._format_size(inventory.total_size_bytes)}."
                ),
            )
        )

        self.logger.info(
            "%s displayed successfully. "
            "Items: %s, size: %s bytes",
            scan_type,
            inventory.total_file_count,
            inventory.total_size_bytes,
        )

    def _render_categories(self) -> None:
        """عرض أقسام Cleaner."""

        self._clear_category_cards()

        if self.inventory is None:
            return

        for category in self.inventory.categories:
            card = CleanerCategoryCard(
                category,
                is_rtl=self.is_rtl,
            )

            card.selection_changed.connect(
                self._update_summary
            )

            insert_index = max(
                0,
                self.categories_layout.count() - 1,
            )

            self.categories_layout.insertWidget(
                insert_index,
                card,
            )

            self.category_cards[
                category.key
            ] = card

    def _clear_category_cards(self) -> None:
        """حذف بطاقات الفحص السابقة."""

        for card in self.category_cards.values():
            self.categories_layout.removeWidget(
                card
            )

            card.setParent(None)
            card.deleteLater()

        self.category_cards.clear()

    def _selected_categories(
        self,
    ) -> tuple[CleanerCategoryScan, ...]:
        """الأقسام المحددة وتحتوي ملفات."""

        if self.inventory is None:
            return ()

        selected: list[
            CleanerCategoryScan
        ] = []

        for category in self.inventory.categories:
            card = self.category_cards.get(
                category.key
            )

            if (
                category.file_count > 0
                and card is not None
                and card.is_selected()
            ):
                selected.append(
                    category
                )

        return tuple(selected)

    def _update_summary(self) -> None:
        """تحديث الملخص وتفعيل زر التنظيف."""

        if self.inventory is None:
            self.total_size_label.setText("--")
            self.total_items_label.setText("--")
            self.selected_size_label.setText("--")
            self.selected_items_label.setText("--")

            self.clean_button.setEnabled(
                False
            )
            return

        selected = (
            self._selected_categories()
        )

        selected_size = sum(
            category.total_size_bytes
            for category in selected
        )

        selected_items = sum(
            category.file_count
            for category in selected
        )

        self.total_size_label.setText(
            self._format_size(
                self.inventory.total_size_bytes
            )
        )

        self.total_items_label.setText(
            f"{self.inventory.total_file_count:,}"
        )

        self.selected_size_label.setText(
            self._format_size(
                selected_size
            )
        )

        self.selected_items_label.setText(
            f"{selected_items:,}"
        )

        self.clean_button.setEnabled(
            selected_items > 0
            and not self._is_busy()
        )

    def _set_scanning_state(
        self,
        is_scanning: bool,
    ) -> None:
        """تحديث حالة الفحص."""

        self.scan_button.setEnabled(
            not is_scanning
        )

        self.admin_scan_button.setEnabled(
            not is_scanning
        )

        self.clean_button.setEnabled(
            False
        )

        for card in self.category_cards.values():
            card.checkbox.setEnabled(
                not is_scanning
            )

        self.scan_button.setText(
            self._text(
                (
                    "Scanning..."
                    if is_scanning
                    else "Scan Again"
                ),
                (
                    "جارٍ الفحص..."
                    if is_scanning
                    else "إعادة الفحص"
                ),
            )
        )

        if is_scanning:
            self.status_label.setText(
                self._text(
                    (
                        "Scanning temporary files. "
                        "No files are being deleted..."
                    ),
                    (
                        "جارٍ فحص الملفات المؤقتة. "
                        "لن يتم حذف أي ملفات..."
                    ),
                )
            )
        else:
            self._update_summary()

    def _set_admin_scan_state(
        self,
        is_waiting: bool,
    ) -> None:
        """تحديث حالة انتظار Admin Scan."""

        self.scan_button.setEnabled(
            not is_waiting
        )

        self.admin_scan_button.setEnabled(
            not is_waiting
        )

        self.clean_button.setEnabled(
            False
        )

        self.admin_scan_button.setText(
            self._text(
                (
                    "Waiting for Administrator..."
                    if is_waiting
                    else "Rescan as Administrator"
                ),
                (
                    "بانتظار صلاحية المسؤول..."
                    if is_waiting
                    else "إعادة الفحص كمسؤول"
                ),
            )
        )

        for card in self.category_cards.values():
            card.checkbox.setEnabled(
                not is_waiting
            )

    def _set_cleanup_state(
        self,
        is_cleaning: bool,
    ) -> None:
        """تحديث حالة التنظيف."""

        self.scan_button.setEnabled(
            not is_cleaning
        )

        self.admin_scan_button.setEnabled(
            not is_cleaning
        )

        self.clean_button.setEnabled(
            False
        )

        self.clean_button.setText(
            self._text(
                (
                    "Cleaning..."
                    if is_cleaning
                    else "Clean Selected"
                ),
                (
                    "جارٍ التنظيف..."
                    if is_cleaning
                    else "تنظيف المحدد"
                ),
            )
        )

        for card in self.category_cards.values():
            card.checkbox.setEnabled(
                not is_cleaning
            )

        if is_cleaning:
            self.status_label.setText(
                self._text(
                    (
                        "Cleaning selected files. "
                        "Locked files will be skipped..."
                    ),
                    (
                        "جارٍ تنظيف الملفات المحددة. "
                        "سيتم تخطي الملفات المقفلة..."
                    ),
                )
            )
        else:
            self._update_summary()

    def _show_cleanup_report(
        self,
        inventory: CleanerCleanInventory,
    ) -> None:
        """عرض تقرير التنظيف."""

        detail_lines: list[str] = []

        for category in inventory.categories:
            detail_lines.append(
                self._text(
                    (
                        f"{category.title}: "
                        f"{category.deleted_files:,} file(s), "
                        f"{self._format_size(category.deleted_size_bytes)}, "
                        f"{category.skipped_items:,} skipped, "
                        f"{category.failed_items:,} failed"
                    ),
                    (
                        f"{self._cleanup_category_title(category)}: "
                        f"{category.deleted_files:,} ملف، "
                        f"{self._format_size(category.deleted_size_bytes)}، "
                        f"{category.skipped_items:,} تم تخطيه، "
                        f"{category.failed_items:,} فشل"
                    ),
                )
            )

            for error in category.errors:
                detail_lines.append(
                    f"    {error}"
                )

        summary = self._text(
            (
                "Deleted files: "
                f"{inventory.total_deleted_files:,}\n"
                "Deleted folders: "
                f"{inventory.total_deleted_directories:,}\n"
                "Freed space: "
                f"{self._format_size(inventory.total_deleted_size_bytes)}\n"
                "Skipped: "
                f"{inventory.total_skipped_items:,}\n"
                "Failed: "
                f"{inventory.total_failed_items:,}"
            ),
            (
                "الملفات المحذوفة: "
                f"{inventory.total_deleted_files:,}\n"
                "المجلدات المحذوفة: "
                f"{inventory.total_deleted_directories:,}\n"
                "المساحة المحررة: "
                f"{self._format_size(inventory.total_deleted_size_bytes)}\n"
                "تم تخطيه: "
                f"{inventory.total_skipped_items:,}\n"
                "فشل: "
                f"{inventory.total_failed_items:,}"
            ),
        )

        report_box = QMessageBox(
            self
        )
        report_box.setWindowTitle(
            self._text(
                "Cleaner Report",
                "تقرير التنظيف",
            )
        )
        report_box.setIcon(
            QMessageBox.Icon.Information
            if inventory.total_failed_items == 0
            else QMessageBox.Icon.Warning
        )
        report_box.setText(
            self._text(
                (
                    "Cleaner finished processing "
                    "the selected categories."
                ),
                (
                    "انتهى Cleaner من معالجة "
                    "الأقسام المحددة."
                ),
            )
        )
        report_box.setInformativeText(
            summary
        )
        report_box.setDetailedText(
            "\n".join(detail_lines)
        )
        report_box.setStandardButtons(
            QMessageBox.StandardButton.Ok
        )
        report_box.exec()

        self.status_label.setText(
            self._text(
                (
                    "Cleaner completed: "
                    f"{self._format_size(inventory.total_deleted_size_bytes)} "
                    "freed, "
                    f"{inventory.total_skipped_items:,} skipped, "
                    f"{inventory.total_failed_items:,} failed."
                ),
                (
                    "اكتمل التنظيف: تم تحرير "
                    f"{self._format_size(inventory.total_deleted_size_bytes)}، "
                    f"تم تخطي {inventory.total_skipped_items:,}، "
                    f"وفشل {inventory.total_failed_items:,}."
                ),
            )
        )

        self.logger.info(
            "Cleaner report displayed. "
            "Deleted bytes: %s, skipped: %s, "
            "failed: %s",
            inventory.total_deleted_size_bytes,
            inventory.total_skipped_items,
            inventory.total_failed_items,
        )

    def _show_error(
        self,
        message: str,
        status: str,
    ) -> None:
        """إظهار خطأ في الصفحة."""

        self.error_label.setText(
            message
        )
        self.error_label.setVisible(
            True
        )
        self.status_label.setText(
            status
        )

    @staticmethod
    def _deserialize_scan_inventory(
        data,
    ) -> CleanerScanInventory:
        """تحويل JSON إلى Scan Inventory."""

        if not isinstance(data, dict):
            raise RuntimeError(
                "Administrator scan did not "
                "return an inventory."
            )

        raw_categories = data.get(
            "categories",
            [],
        )

        if not isinstance(
            raw_categories,
            list,
        ):
            raise RuntimeError(
                "Administrator scan categories "
                "are invalid."
            )

        categories: list[
            CleanerCategoryScan
        ] = []

        tuple_fields = (
            "scanned_paths",
            "missing_paths",
            "unavailable_paths",
            "sample_files",
            "warnings",
        )

        for raw_category in raw_categories:
            if not isinstance(
                raw_category,
                dict,
            ):
                continue

            category_data = dict(
                raw_category
            )

            for field_name in tuple_fields:
                value = category_data.get(
                    field_name,
                    [],
                )

                category_data[
                    field_name
                ] = tuple(
                    value
                    if isinstance(value, list)
                    else []
                )

            categories.append(
                CleanerCategoryScan(
                    **category_data
                )
            )

        return CleanerScanInventory(
            scanned_at=str(
                data.get(
                    "scanned_at",
                    "",
                )
            ),
            categories=tuple(
                categories
            ),
        )

    @staticmethod
    def _deserialize_cleanup_inventory(
        data,
    ) -> CleanerCleanInventory:
        """تحويل JSON إلى Cleanup Inventory."""

        if not isinstance(data, dict):
            raise RuntimeError(
                "Administrator cleaning did not "
                "return a report."
            )

        raw_categories = data.get(
            "categories",
            [],
        )

        if not isinstance(
            raw_categories,
            list,
        ):
            raise RuntimeError(
                "Administrator cleaning categories "
                "are invalid."
            )

        categories: list[
            CleanerCategoryCleanResult
        ] = []

        for raw_category in raw_categories:
            if not isinstance(
                raw_category,
                dict,
            ):
                continue

            category_data = dict(
                raw_category
            )

            errors = category_data.get(
                "errors",
                [],
            )

            category_data["errors"] = tuple(
                errors
                if isinstance(errors, list)
                else []
            )

            categories.append(
                CleanerCategoryCleanResult(
                    **category_data
                )
            )

        requested = data.get(
            "requested_categories",
            [],
        )

        return CleanerCleanInventory(
            cleaned_at=str(
                data.get(
                    "cleaned_at",
                    "",
                )
            ),
            requested_categories=tuple(
                requested
                if isinstance(requested, list)
                else []
            ),
            categories=tuple(
                categories
            ),
        )

    @staticmethod
    def _read_json_payload(
        result_path: Path,
    ) -> dict:
        """قراءة ملف نتيجة Administrator."""

        payload = json.loads(
            result_path.read_text(
                encoding="utf-8"
            )
        )

        if not isinstance(
            payload,
            dict,
        ):
            raise RuntimeError(
                "Unexpected Administrator "
                "result format."
            )

        return payload

    @staticmethod
    def _create_admin_result_path(
        prefix: str,
    ) -> Path:
        """إنشاء مسار مؤقت لنتيجة Administrator."""

        directory = (
            Path(tempfile.gettempdir())
            / "PixelGuardian"
            / "admin_tasks"
        )

        directory.mkdir(
            parents=True,
            exist_ok=True,
        )

        return (
            directory
            / (
                f"{prefix}_"
                f"{uuid.uuid4().hex}.json"
            )
        )

    def _delete_temp_file(
        self,
        path: Path,
    ) -> None:
        """حذف ملف النتيجة المؤقت."""

        try:
            path.unlink(
                missing_ok=True
            )

        except OSError:
            self.logger.warning(
                "Could not remove temporary "
                "Cleaner result: %s",
                path,
            )

    def _is_scanning(self) -> bool:
        """هل الفحص العادي يعمل؟"""

        return (
            self._scan_thread is not None
            and self._scan_thread.isRunning()
        )

    def _is_cleaning(self) -> bool:
        """هل التنظيف العادي يعمل؟"""

        return (
            self._cleanup_thread is not None
            and self._cleanup_thread.isRunning()
        )

    def _is_busy(self) -> bool:
        """هل Cleaner ينفذ عملية حاليًا؟"""

        return (
            self._is_scanning()
            or self._is_cleaning()
            or self._admin_scan_timer.isActive()
            or self._admin_cleanup_timer.isActive()
        )

    def _category_title(
        self,
        category: CleanerCategoryScan,
    ) -> str:
        """اسم قسم الفحص حسب اللغة."""

        if not self.is_rtl:
            return category.title

        title_map = {
            "user_temp": "ملفات المستخدم المؤقتة",
            "windows_temp": "ملفات ويندوز المؤقتة",
            "browser_cache": "ذاكرة المتصفح المؤقتة",
            "recycle_bin": "سلة المحذوفات",
            "thumbnail_cache": "ذاكرة الصور المصغرة",
            "directx_shader_cache": "ذاكرة DirectX Shader",
            "delivery_optimization": "ملفات تحسين التسليم",
            "windows_update_cache": "ذاكرة تحديثات ويندوز",
            "crash_dumps": "ملفات تقارير التعطل",
            "windows_error_reports": "تقارير أخطاء ويندوز",
            "log_files": "ملفات السجل",
        }

        key = str(
            category.key
        ).strip().casefold()

        return title_map.get(
            key,
            category.title,
        )

    def _cleanup_category_title(
        self,
        category: CleanerCategoryCleanResult,
    ) -> str:
        """اسم قسم تقرير التنظيف حسب اللغة."""

        if not self.is_rtl:
            return category.title

        title_map = {
            "User Temporary Files": "ملفات المستخدم المؤقتة",
            "Windows Temporary Files": "ملفات ويندوز المؤقتة",
            "Browser Cache": "ذاكرة المتصفح المؤقتة",
            "Recycle Bin": "سلة المحذوفات",
            "Thumbnail Cache": "ذاكرة الصور المصغرة",
            "DirectX Shader Cache": "ذاكرة DirectX Shader",
            "Delivery Optimization Files": "ملفات تحسين التسليم",
            "Windows Update Cache": "ذاكرة تحديثات ويندوز",
            "Crash Dumps": "ملفات تقارير التعطل",
            "Windows Error Reports": "تقارير أخطاء ويندوز",
            "Log Files": "ملفات السجل",
        }

        return title_map.get(
            category.title,
            category.title,
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

    @staticmethod
    def _create_summary_value(
        layout: QHBoxLayout,
        title: str,
    ) -> QLabel:
        """إنشاء قيمة داخل ملخص Cleaner."""

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
        container_layout.setSpacing(3)

        title_label = QLabel(title)
        title_label.setObjectName(
            "cleanerSummaryTitle"
        )

        value_label = QLabel("--")
        value_label.setObjectName(
            "cleanerSummaryValue"
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

    @staticmethod
    def _format_size(
        size_bytes: int,
    ) -> str:
        """تنسيق الحجم."""

        return (
            CleanerCategoryCard
            ._format_size(size_bytes)
        )