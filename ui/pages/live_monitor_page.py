from __future__ import annotations

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QHideEvent, QShowEvent
from PySide6.QtWidgets import (
    QApplication,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QProgressBar,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from core.models.live_metrics import LiveMetrics
from core.services.application_settings_service import (
    ApplicationSettingsService,
)
from core.services.live_monitor_service import (
    LiveMonitorService,
)
from core.services.localization_service import (
    LocalizationService,
)
from infrastructure.logging.logger import get_logger


class LiveMetricCard(QFrame):
    """بطاقة لعرض قيمة لحظية واحدة."""

    def __init__(
        self,
        title: str,
        waiting_text: str,
        show_progress: bool = True,
    ) -> None:
        super().__init__()

        self.setObjectName("liveMetricCard")
        self.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Fixed,
        )
        self.setMinimumHeight(170)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(22, 20, 22, 20)
        layout.setSpacing(10)

        self.title_label = QLabel(title)
        self.title_label.setObjectName(
            "liveMetricTitle"
        )
        self.title_label.setAlignment(
            Qt.AlignmentFlag.AlignLeading
            | Qt.AlignmentFlag.AlignVCenter
        )

        self.primary_label = QLabel("--")
        self.primary_label.setObjectName(
            "liveMetricPrimary"
        )
        self.primary_label.setAlignment(
            Qt.AlignmentFlag.AlignLeading
            | Qt.AlignmentFlag.AlignVCenter
        )

        self.secondary_label = QLabel(
            waiting_text
        )
        self.secondary_label.setObjectName(
            "liveMetricSecondary"
        )
        self.secondary_label.setWordWrap(True)
        self.secondary_label.setAlignment(
            Qt.AlignmentFlag.AlignLeading
            | Qt.AlignmentFlag.AlignVCenter
        )

        self.progress_bar = QProgressBar()
        self.progress_bar.setObjectName(
            "liveMetricProgress"
        )
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setMinimumHeight(16)
        self.progress_bar.setVisible(show_progress)

        layout.addWidget(self.title_label)
        layout.addWidget(self.primary_label)
        layout.addWidget(self.secondary_label)
        layout.addStretch()

        if show_progress:
            layout.addWidget(self.progress_bar)

    def set_values(
        self,
        primary: str,
        secondary: str,
        percentage: float | None = None,
    ) -> None:
        """تحديث قيم البطاقة."""

        self.primary_label.setText(primary)
        self.secondary_label.setText(secondary)

        if percentage is None:
            self.progress_bar.setVisible(False)
            return

        safe_percentage = max(
            0.0,
            min(100.0, float(percentage)),
        )

        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(
            int(round(safe_percentage))
        )
        self.progress_bar.setFormat(
            f"{safe_percentage:.1f}%"
        )


class LiveMonitorPage(QWidget):
    """صفحة مراقبة موارد الجهاز بشكل لحظي."""

    DEFAULT_UPDATE_INTERVAL_MS = 1000

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
        self.monitor_service = LiveMonitorService()

        self.core_progress_bars: list[
            QProgressBar
        ] = []

        self.is_paused = False

        update_interval_ms = (
            self.settings_service.get_int(
                "monitoring/refresh_interval_ms"
            )
        )

        if update_interval_ms <= 0:
            update_interval_ms = (
                self.DEFAULT_UPDATE_INTERVAL_MS
            )

        self.update_timer = QTimer(self)
        self.update_timer.setInterval(
            update_interval_ms
        )
        self.update_timer.timeout.connect(
            self._update_metrics
        )

        self._setup_ui()
        self._apply_page_style()

    def _setup_ui(self) -> None:
        """إنشاء عناصر صفحة Live Monitor."""

        page_layout = QVBoxLayout(self)
        page_layout.setContentsMargins(
            40,
            35,
            40,
            35,
        )
        page_layout.setSpacing(18)

        header_layout = QHBoxLayout()
        header_layout.setSpacing(15)

        title_container = QVBoxLayout()
        title_container.setSpacing(5)

        self.title_label = QLabel(
            self._text(
                "Live Monitor",
                "المراقبة المباشرة",
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
                    "Real-time CPU, memory, storage, "
                    "network and process monitoring."
                ),
                (
                    "مراقبة مباشرة للمعالج والذاكرة "
                    "والتخزين والشبكة والعمليات."
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

        title_container.addWidget(
            self.title_label
        )
        title_container.addWidget(
            self.subtitle_label
        )

        self.live_status_label = QLabel(
            self._text(
                "LIVE",
                "مباشر",
            )
        )
        self.live_status_label.setObjectName(
            "liveStatusBadge"
        )
        self.live_status_label.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )
        self.live_status_label.setFixedSize(
            70,
            34,
        )

        self.pause_button = QPushButton(
            self._text(
                "Pause",
                "إيقاف مؤقت",
            )
        )
        self.pause_button.setObjectName(
            "monitorControlButton"
        )
        self.pause_button.setMinimumSize(
            110,
            40,
        )
        self.pause_button.setCursor(
            Qt.CursorShape.PointingHandCursor
        )
        self.pause_button.clicked.connect(
            self._toggle_pause
        )

        header_layout.addLayout(
            title_container,
            1,
        )
        header_layout.addWidget(
            self.live_status_label,
            0,
            Qt.AlignmentFlag.AlignVCenter,
        )
        header_layout.addWidget(
            self.pause_button,
            0,
            Qt.AlignmentFlag.AlignVCenter,
        )

        self.error_label = QLabel()
        self.error_label.setObjectName(
            "monitorErrorLabel"
        )
        self.error_label.setWordWrap(True)
        self.error_label.setVisible(False)

        scroll_area = QScrollArea()
        scroll_area.setObjectName(
            "liveMonitorScrollArea"
        )
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(
            QFrame.Shape.NoFrame
        )
        scroll_area.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )

        scroll_content = QWidget()
        scroll_content.setObjectName(
            "liveMonitorScrollContent"
        )

        content_layout = QVBoxLayout(
            scroll_content
        )
        content_layout.setContentsMargins(
            0,
            0,
            10,
            0,
        )
        content_layout.setSpacing(18)

        cards_grid = QGridLayout()
        cards_grid.setContentsMargins(
            0,
            0,
            0,
            0,
        )
        cards_grid.setHorizontalSpacing(18)
        cards_grid.setVerticalSpacing(18)
        cards_grid.setColumnStretch(0, 1)
        cards_grid.setColumnStretch(1, 1)

        waiting_text = self._text(
            "Waiting for data...",
            "بانتظار البيانات...",
        )

        self.cpu_card = LiveMetricCard(
            self._text(
                "CPU Usage",
                "استخدام المعالج",
            ),
            waiting_text,
        )

        self.memory_card = LiveMetricCard(
            self._text(
                "Memory Usage",
                "استخدام الذاكرة",
            ),
            waiting_text,
        )

        self.system_drive_card = LiveMetricCard(
            self._text(
                "System Drive",
                "قرص النظام",
            ),
            waiting_text,
        )

        self.process_card = LiveMetricCard(
            self._text(
                "Running Processes",
                "العمليات قيد التشغيل",
            ),
            waiting_text,
            show_progress=False,
        )

        self.disk_io_card = LiveMetricCard(
            self._text(
                "Disk Activity",
                "نشاط القرص",
            ),
            waiting_text,
            show_progress=False,
        )

        self.network_card = LiveMetricCard(
            self._text(
                "Network Activity",
                "نشاط الشبكة",
            ),
            waiting_text,
            show_progress=False,
        )

        cards_grid.addWidget(
            self.cpu_card,
            0,
            0,
        )
        cards_grid.addWidget(
            self.memory_card,
            0,
            1,
        )
        cards_grid.addWidget(
            self.system_drive_card,
            1,
            0,
        )
        cards_grid.addWidget(
            self.process_card,
            1,
            1,
        )
        cards_grid.addWidget(
            self.disk_io_card,
            2,
            0,
        )
        cards_grid.addWidget(
            self.network_card,
            2,
            1,
        )

        core_card = QFrame()
        core_card.setObjectName(
            "coreUsageCard"
        )

        core_card_layout = QVBoxLayout(
            core_card
        )
        core_card_layout.setContentsMargins(
            22,
            20,
            22,
            22,
        )
        core_card_layout.setSpacing(15)

        self.core_title_label = QLabel(
            self._text(
                "CPU Core Usage",
                "استخدام أنوية المعالج",
            )
        )
        self.core_title_label.setObjectName(
            "coreUsageTitle"
        )
        self.core_title_label.setAlignment(
            Qt.AlignmentFlag.AlignLeading
            | Qt.AlignmentFlag.AlignVCenter
        )

        self.core_description_label = QLabel(
            self._text(
                (
                    "Current utilization of each "
                    "logical processor."
                ),
                (
                    "الاستخدام الحالي لكل نواة "
                    "منطقية في المعالج."
                ),
            )
        )
        self.core_description_label.setObjectName(
            "coreUsageDescription"
        )
        self.core_description_label.setWordWrap(
            True
        )
        self.core_description_label.setAlignment(
            Qt.AlignmentFlag.AlignLeading
            | Qt.AlignmentFlag.AlignVCenter
        )

        self.core_grid_layout = QGridLayout()
        self.core_grid_layout.setContentsMargins(
            0,
            5,
            0,
            0,
        )
        self.core_grid_layout.setHorizontalSpacing(
            14
        )
        self.core_grid_layout.setVerticalSpacing(
            12
        )
        self.core_grid_layout.setColumnStretch(
            1,
            1,
        )

        core_card_layout.addWidget(
            self.core_title_label
        )
        core_card_layout.addWidget(
            self.core_description_label
        )
        core_card_layout.addLayout(
            self.core_grid_layout
        )

        self.sample_time_label = QLabel(
            self._text(
                "Last update: Waiting for data...",
                "آخر تحديث: بانتظار البيانات...",
            )
        )
        self.sample_time_label.setObjectName(
            "sampleTimeLabel"
        )
        self.sample_time_label.setAlignment(
            (
                Qt.AlignmentFlag.AlignLeft
                if self.is_rtl
                else Qt.AlignmentFlag.AlignRight
            )
            | Qt.AlignmentFlag.AlignVCenter
        )

        content_layout.addLayout(
            cards_grid
        )
        content_layout.addWidget(
            core_card
        )
        content_layout.addWidget(
            self.sample_time_label
        )
        content_layout.addStretch()

        scroll_area.setWidget(
            scroll_content
        )

        page_layout.addLayout(
            header_layout
        )
        page_layout.addWidget(
            self.error_label
        )
        page_layout.addWidget(
            scroll_area,
            1,
        )

    def showEvent(
        self,
        event: QShowEvent,
    ) -> None:
        """تشغيل التحديث عند فتح الصفحة."""

        super().showEvent(event)

        if not self.is_paused:
            self._update_metrics()

            if not self.update_timer.isActive():
                self.update_timer.start()

            self._set_live_status(True)

    def hideEvent(
        self,
        event: QHideEvent,
    ) -> None:
        """إيقاف التحديث عند مغادرة الصفحة."""

        self.update_timer.stop()
        super().hideEvent(event)

    def _toggle_pause(self) -> None:
        """إيقاف أو استكمال المراقبة."""

        self.is_paused = not self.is_paused

        if self.is_paused:
            self.update_timer.stop()
            self.pause_button.setText(
                self._text(
                    "Resume",
                    "استكمال",
                )
            )
            self._set_live_status(False)
        else:
            self._update_metrics()
            self.update_timer.start()
            self.pause_button.setText(
                self._text(
                    "Pause",
                    "إيقاف مؤقت",
                )
            )
            self._set_live_status(True)

    def _update_metrics(self) -> None:
        """قراءة وعرض آخر قياسات الجهاز."""

        result = (
            self.monitor_service
            .get_live_metrics()
        )

        if not result.success or result.data is None:
            self.error_label.setText(
                self._text(
                    "Live monitoring error: ",
                    "خطأ في المراقبة المباشرة: ",
                )
                + f"{result.message}"
            )
            self.error_label.setVisible(True)
            self._set_live_status(False)
            return

        self.error_label.setVisible(False)

        metrics = result.data

        self._update_summary_cards(
            metrics
        )
        self._update_core_usage(
            metrics.cpu_per_core_percent
        )
        self._update_sample_time(
            metrics.sampled_at
        )

    def _update_summary_cards(
        self,
        metrics: LiveMetrics,
    ) -> None:
        """تحديث بطاقات القياسات الرئيسية."""

        frequency_text = self._format_frequency(
            metrics.cpu_frequency_mhz
        )

        self.cpu_card.set_values(
            primary=(
                f"{metrics.cpu_usage_percent:.1f}%"
            ),
            secondary=(
                self._text(
                    "Current frequency: ",
                    "التردد الحالي: ",
                )
                + frequency_text
            ),
            percentage=(
                metrics.cpu_usage_percent
            ),
        )

        self.memory_card.set_values(
            primary=(
                f"{metrics.memory_usage_percent:.1f}%"
            ),
            secondary=(
                self._text(
                    "Used: ",
                    "المستخدم: ",
                )
                + f"{metrics.memory_used_gb:.2f} GB\n"
                + self._text(
                    "Available: ",
                    "المتاح: ",
                )
                + f"{metrics.memory_available_gb:.2f} GB\n"
                + self._text(
                    "Total: ",
                    "الإجمالي: ",
                )
                + f"{metrics.memory_total_gb:.2f} GB"
            ),
            percentage=(
                metrics.memory_usage_percent
            ),
        )

        drive_percentage = (
            metrics.system_drive_usage_percent
        )

        drive_primary = (
            f"{drive_percentage:.1f}%"
            if drive_percentage is not None
            else self._unavailable()
        )

        self.system_drive_card.set_values(
            primary=drive_primary,
            secondary=(
                self._text(
                    "Drive: ",
                    "القرص: ",
                )
                + f"{metrics.system_drive}\n"
                + self._text(
                    "Used: ",
                    "المستخدم: ",
                )
                + self._format_gb(
                    metrics.system_drive_used_gb
                )
                + "\n"
                + self._text(
                    "Free: ",
                    "المتاح: ",
                )
                + self._format_gb(
                    metrics.system_drive_free_gb
                )
                + "\n"
                + self._text(
                    "Total: ",
                    "الإجمالي: ",
                )
                + self._format_gb(
                    metrics.system_drive_total_gb
                )
            ),
            percentage=drive_percentage,
        )

        self.process_card.set_values(
            primary=f"{metrics.process_count:,}",
            secondary=self._text(
                "Currently detected running processes.",
                "عدد العمليات التي تعمل حاليًا.",
            ),
        )

        self.disk_io_card.set_values(
            primary=(
                self._text(
                    "Read  ",
                    "قراءة  ",
                )
                + self._format_rate(
                    metrics.disk_read_bytes_per_second
                )
            ),
            secondary=(
                self._text(
                    "Write  ",
                    "كتابة  ",
                )
                + self._format_rate(
                    metrics.disk_write_bytes_per_second
                )
            ),
        )

        self.network_card.set_values(
            primary=(
                self._text(
                    "Download  ",
                    "تنزيل  ",
                )
                + self._format_rate(
                    metrics.network_download_bytes_per_second
                )
            ),
            secondary=(
                self._text(
                    "Upload  ",
                    "رفع  ",
                )
                + self._format_rate(
                    metrics.network_upload_bytes_per_second
                )
            ),
        )

    def _update_core_usage(
        self,
        core_values: tuple[float, ...],
    ) -> None:
        """عرض استخدام كل نواة منطقية."""

        if (
            len(self.core_progress_bars)
            != len(core_values)
        ):
            self._build_core_progress_bars(
                len(core_values)
            )

        for progress_bar, value in zip(
            self.core_progress_bars,
            core_values,
        ):
            safe_value = max(
                0.0,
                min(100.0, float(value)),
            )

            progress_bar.setValue(
                int(round(safe_value))
            )
            progress_bar.setFormat(
                f"{safe_value:.1f}%"
            )

    def _build_core_progress_bars(
        self,
        core_count: int,
    ) -> None:
        """إنشاء عدادات الأنوية حسب عددها."""

        while self.core_grid_layout.count():
            layout_item = (
                self.core_grid_layout
                .takeAt(0)
            )

            widget = layout_item.widget()

            if widget is not None:
                widget.deleteLater()

        self.core_progress_bars.clear()

        for core_index in range(core_count):
            core_label = QLabel(
                self._text(
                    f"Core {core_index + 1}",
                    f"النواة {core_index + 1}",
                )
            )
            core_label.setObjectName(
                "coreLabel"
            )
            core_label.setMinimumWidth(70)
            core_label.setAlignment(
                Qt.AlignmentFlag.AlignLeading
                | Qt.AlignmentFlag.AlignVCenter
            )

            progress_bar = QProgressBar()
            progress_bar.setObjectName(
                "coreProgressBar"
            )
            progress_bar.setRange(0, 100)
            progress_bar.setValue(0)
            progress_bar.setMinimumHeight(20)
            progress_bar.setTextVisible(True)

            self.core_grid_layout.addWidget(
                core_label,
                core_index,
                0,
            )
            self.core_grid_layout.addWidget(
                progress_bar,
                core_index,
                1,
            )

            self.core_progress_bars.append(
                progress_bar
            )

    def _update_sample_time(
        self,
        sampled_at: str,
    ) -> None:
        """عرض وقت آخر تحديث."""

        formatted_time = sampled_at.replace(
            "T",
            " ",
        )

        self.sample_time_label.setText(
            self._text(
                "Last update: ",
                "آخر تحديث: ",
            )
            + formatted_time
        )

    def _set_live_status(
        self,
        is_live: bool,
    ) -> None:
        """تحديث شارة حالة المراقبة."""

        self.live_status_label.setText(
            self._text(
                "LIVE" if is_live else "PAUSED",
                "مباشر" if is_live else "متوقف",
            )
        )

        self.live_status_label.setProperty(
            "monitorActive",
            is_live,
        )

        self.live_status_label.style().unpolish(
            self.live_status_label
        )
        self.live_status_label.style().polish(
            self.live_status_label
        )

    def _apply_page_style(self) -> None:
            """تنسيق صفحة Live Monitor."""

            self.setStyleSheet(
                """
                QScrollArea#liveMonitorScrollArea,
                QWidget#liveMonitorScrollContent {
                    background-color: transparent;
                    border: none;
                }

                QFrame#liveMetricCard,
                QFrame#coreUsageCard {
                    background-color: #131b2f;
                    border: 1px solid #253451;
                    border-radius: 16px;
                }

                QLabel#liveMetricTitle,
                QLabel#coreUsageTitle {
                    color: #66e3ff;
                    font-size: 18px;
                    font-weight: 700;
                }

                QLabel#liveMetricPrimary {
                    color: #ffffff;
                    font-size: 27px;
                    font-weight: 800;
                }

                QLabel#liveMetricSecondary,
                QLabel#coreUsageDescription {
                    color: #9da9bd;
                    font-size: 13px;
                }

                QLabel#coreLabel {
                    color: #c5cede;
                    font-size: 13px;
                    font-weight: 600;
                }

                QLabel#sampleTimeLabel {
                    color: #6f7f99;
                    font-size: 12px;
                }

                QLabel#monitorErrorLabel {
                    padding: 12px 15px;
                    color: #ffb4b4;
                    background-color: #351c29;
                    border: 1px solid #6d3041;
                    border-radius: 9px;
                    font-size: 13px;
                }

                QLabel#liveStatusBadge {
                    color: #06130d;
                    background-color: #79e6a5;
                    border-radius: 8px;
                    font-size: 12px;
                    font-weight: 800;
                }

                QLabel#liveStatusBadge[monitorActive="false"] {
                    color: #d2d8e4;
                    background-color: #37445a;
                }

                QPushButton#monitorControlButton {
                    color: #07101d;
                    background-color: #66e3ff;
                    border: none;
                    border-radius: 9px;
                    padding: 0 18px;
                    font-size: 14px;
                    font-weight: 700;
                }

                QPushButton#monitorControlButton:hover {
                    background-color: #8aeaff;
                }

                QPushButton#monitorControlButton:pressed {
                    background-color: #3fc8e7;
                }

                QProgressBar#liveMetricProgress,
                QProgressBar#coreProgressBar {
                    color: #ffffff;
                    background-color: #202c43;
                    border: none;
                    border-radius: 7px;
                    text-align: center;
                    font-size: 11px;
                    font-weight: 700;
                }

                QProgressBar#liveMetricProgress::chunk,
                QProgressBar#coreProgressBar::chunk {
                    background-color: #66e3ff;
                    border-radius: 7px;
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


    def _format_frequency(
        self,
        frequency_mhz: float | None,
    ) -> str:
        """تنسيق تردد المعالج."""

        if frequency_mhz is None:
            return self._unavailable()

        if frequency_mhz >= 1000:
            return (
                f"{frequency_mhz / 1000:.2f} GHz"
            )

        return f"{frequency_mhz:.0f} MHz"

    def _format_gb(
        self,
        value: float | None,
    ) -> str:
        """تنسيق السعة بالجيجابايت."""

        if value is None:
            return self._unavailable()

        return f"{value:.2f} GB"

    @staticmethod
    def _format_rate(
        bytes_per_second: float,
    ) -> str:
        """تنسيق سرعة النقل تلقائيًا."""

        value = max(
            0.0,
            float(bytes_per_second),
        )

        units = (
            "B/s",
            "KB/s",
            "MB/s",
            "GB/s",
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