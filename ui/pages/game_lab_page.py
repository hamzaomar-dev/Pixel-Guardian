from __future__ import annotations
from pathlib import Path
from PySide6.QtCore import QObject, QThread, Qt, Signal, Slot
from PySide6.QtGui import QShowEvent
from PySide6.QtWidgets import QApplication, QFrame, QHBoxLayout, QHeaderView, QLabel, QMessageBox, QPushButton, QTabWidget, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget
from core.models.game_library import GameLibraryInventory, InstalledGame
from core.models.game_readiness import GameReadinessReport
from core.models.online_gaming_performance import (
    GamingPreset,
    GamingResolution,
    OnlineGamingPerformanceResult,
)
from core.services.game_action_service import GameActionError, GameActionService
from core.services.game_library_service import GameLibraryService
from core.services.fpshq_performance_provider import FpsHqPerformanceProvider
from core.services.gaming_performance_cache_service import GamingPerformanceCacheService
from core.services.gaming_performance_request_service import GamingPerformanceRequestService
from core.services.game_readiness_service import GameReadinessService
from core.services.application_settings_service import ApplicationSettingsService
from core.services.localization_service import LocalizationService
from core.services.online_gaming_performance_service import OnlineGamingPerformanceService
from infrastructure.logging.logger import get_logger
from ui.widgets.game_readiness_panel import GameReadinessPanel
from ui.widgets.gaming_power_panel import GamingPowerPanel

class GameLibraryWorker(QObject):
    """تشغيل فحص الألعاب خارج UI Thread."""
    finished = Signal(object)
    failed = Signal(str)

    @Slot()
    def run(self) -> None:
        """تشغيل فحص Steam وEpic."""
        try:
            inventory = GameLibraryService().scan_installed_games()
        except Exception as error:
            self.failed.emit(str(error))
            return
        self.finished.emit(inventory)

class GameReadinessWorker(QObject):
    """تشغيل فحص جاهزية الألعاب خارج UI Thread."""
    finished = Signal(object)
    failed = Signal(str)

    @Slot()
    def run(self) -> None:
        """فحص إعدادات Windows المتعلقة بالألعاب."""
        try:
            report = GameReadinessService().scan_game_readiness()
        except Exception as error:
            self.failed.emit(str(error))
            return
        self.finished.emit(report)

class GamingHardwareWorker(QObject):
    """قراءة CPU وGPU لتبويب Gaming Power."""
    finished = Signal(str, str)
    failed = Signal(str)

    @Slot()
    def run(self) -> None:
        """قراءة قطع الجهاز خارج UI Thread."""
        try:
            request = GamingPerformanceRequestService().build('Pixel Guardian Hardware Detection')
        except Exception as error:
            self.failed.emit(str(error))
            return
        self.finished.emit(request.cpu_query_name, request.gpu_query_name)

class GamingPerformanceWorker(QObject):
    """جلب نتيجة FPS من FPSHQ خارج UI Thread."""

    finished = Signal(object)
    failed = Signal(str)

    def __init__(
        self,
        game_name: str,
        resolution: str,
        preset: str,
    ) -> None:
        super().__init__()

        self.game_name = game_name
        self.resolution = resolution
        self.preset = preset

    @Slot()
    def run(self) -> None:
        """تجهيز الطلب وجلب نتيجة الأداء."""

        try:
            request = GamingPerformanceRequestService().build(
                game=self.game_name,
                resolution=GamingResolution(
                    self.resolution
                ),
                preset=GamingPreset(
                    self.preset
                ),
            )

            cache_service = (
                GamingPerformanceCacheService()
            )

            try:
                cached_result = cache_service.get(
                    request
                )
            except Exception:
                cached_result = None

            if cached_result is not None:
                self.finished.emit(
                    cached_result
                )
                return

            service = OnlineGamingPerformanceService(
                provider=FpsHqPerformanceProvider()
            )

            result = service.lookup(
                request
            )

            if result.is_available:
                try:
                    cache_service.put(
                        result
                    )
                except Exception:
                    pass

        except Exception as error:
            self.failed.emit(
                str(error)
            )
            return

        self.finished.emit(
            result
        )


class GameLabPage(QWidget):
    """صفحة مكتبة الألعاب وجاهزية Windows وأداء الألعاب."""

    def __init__(self) -> None:
        super().__init__()
        application = QApplication.instance()
        if application is None:
            raise RuntimeError('QApplication has not been initialized.')
        self.application = application
        self.settings_service = getattr(application, 'settings_service', None) or ApplicationSettingsService()
        self.localization = getattr(application, 'localization_service', None) or LocalizationService(settings_service=self.settings_service)
        self.is_rtl = self.localization.is_rtl
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft if self.is_rtl else Qt.LayoutDirection.LeftToRight)
        self.setObjectName('page')
        self.logger = get_logger()
        self.inventory: GameLibraryInventory | None = None
        self.readiness_report: GameReadinessReport | None = None
        self.game_action_service = GameActionService()
        self._scan_thread: QThread | None = None
        self._scan_worker: GameLibraryWorker | None = None
        self._readiness_thread: QThread | None = None
        self._readiness_worker: GameReadinessWorker | None = None
        self._gaming_hardware_thread: QThread | None = None
        self._gaming_hardware_worker: GamingHardwareWorker | None = None
        self._gaming_performance_thread: QThread | None = None
        self._gaming_performance_worker: GamingPerformanceWorker | None = None
        self._scanned_once = False
        self._readiness_scanned_once = False
        self._gaming_hardware_loaded_once = False
        self._setup_ui()

    def _setup_ui(self) -> None:
        """إنشاء واجهة Game Lab."""
        page_layout = QVBoxLayout(self)
        page_layout.setContentsMargins(40, 35, 40, 35)
        page_layout.setSpacing(18)
        header_layout = QHBoxLayout()
        header_layout.setSpacing(12)
        title_layout = QVBoxLayout()
        title_layout.setSpacing(5)
        title = QLabel(self._text('Game Lab', 'مختبر الألعاب'))
        title.setObjectName('pageTitle')
        subtitle = QLabel(self._text('Manage detected games, review Windows gaming readiness, and prepare FPS estimates.', 'أدر الألعاب المكتشفة، وراجع جاهزية ويندوز للألعاب، وجهّز تقديرات معدل الإطارات.'))
        subtitle.setObjectName('pageSubtitle')
        title_layout.addWidget(title)
        title_layout.addWidget(subtitle)
        header_layout.addLayout(title_layout, 1)
        self.tabs = QTabWidget()
        self.tabs.setObjectName('gameLabTabs')
        self.tabs.setDocumentMode(True)
        library_tab = QWidget()
        library_tab.setObjectName('gameLibraryTab')
        readiness_tab = QWidget()
        readiness_tab.setObjectName('gameReadinessTab')
        gaming_power_tab = QWidget()
        gaming_power_tab.setObjectName('gamingPowerTab')
        self._setup_library_tab(library_tab)
        self._setup_readiness_tab(readiness_tab)
        self._setup_gaming_power_tab(gaming_power_tab)
        self.tabs.addTab(library_tab, self._text('Game Library', 'مكتبة الألعاب'))
        self.tabs.addTab(readiness_tab, self._text('Gaming Readiness', 'جاهزية الألعاب'))
        self.tabs.addTab(gaming_power_tab, self._text('Gaming Power', 'قوة الألعاب'))
        page_layout.addLayout(header_layout)
        page_layout.addWidget(self.tabs, 1)

    def _setup_library_tab(self, tab: QWidget) -> None:
        """إنشاء تبويب مكتبة الألعاب."""
        tab_layout = QVBoxLayout(tab)
        tab_layout.setContentsMargins(0, 18, 0, 0)
        tab_layout.setSpacing(16)
        toolbar_layout = QHBoxLayout()
        toolbar_layout.setSpacing(12)
        library_title = QLabel(self._text('Installed Games', 'الألعاب المثبتة'))
        library_title.setObjectName('cardTitle')
        toolbar_layout.addWidget(library_title)
        toolbar_layout.addStretch()
        self.scan_button = QPushButton(self._text('Scan Games', 'فحص الألعاب'))
        self.scan_button.setObjectName('refreshButton')
        self.scan_button.setMinimumHeight(42)
        self.scan_button.setMinimumWidth(130)
        self.scan_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.scan_button.clicked.connect(lambda _checked=False: self._start_scan())
        toolbar_layout.addWidget(self.scan_button)
        self.error_label = QLabel()
        self.error_label.setObjectName('cleanerErrorLabel')
        self.error_label.setWordWrap(True)
        self.error_label.setVisible(False)
        summary_card = QFrame()
        summary_card.setObjectName('cleanerSummaryCard')
        summary_layout = QHBoxLayout(summary_card)
        summary_layout.setContentsMargins(22, 18, 22, 18)
        summary_layout.setSpacing(40)
        self.total_games_label = self._create_summary_value(summary_layout, self._text('Total Games', 'إجمالي الألعاب'))
        self.steam_games_label = self._create_summary_value(summary_layout, self._text('Steam', 'ستيم'))
        self.epic_games_label = self._create_summary_value(summary_layout, self._text('Epic Games', 'إيبك جيمز'))
        self.total_size_label = self._create_summary_value(summary_layout, self._text('Reported Size', 'الحجم المسجّل'))
        summary_layout.addStretch()
        self.games_table = QTableWidget()
        self.games_table.setObjectName('gameLibraryTable')
        self.games_table.setColumnCount(5)
        self.games_table.setHorizontalHeaderLabels([self._text('Platform', 'المنصة'), self._text('Game', 'اللعبة'), self._text('Install Path', 'مسار التثبيت'), self._text('Reported Size', 'الحجم المسجّل'), self._text('Status', 'الحالة')])
        self.games_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.games_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.games_table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.games_table.setAlternatingRowColors(True)
        self.games_table.setShowGrid(False)
        self.games_table.verticalHeader().setVisible(False)
        self.games_table.setSortingEnabled(True)
        self.games_table.itemSelectionChanged.connect(self._update_action_buttons)
        header = self.games_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        actions_layout = QHBoxLayout()
        actions_layout.setSpacing(12)
        actions_layout.addStretch()
        self.open_folder_button = QPushButton(self._text('Open Folder', 'فتح المجلد'))
        self.open_folder_button.setObjectName('secondaryButton')
        self.open_folder_button.setMinimumHeight(42)
        self.open_folder_button.setMinimumWidth(130)
        self.open_folder_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.open_folder_button.setEnabled(False)
        self.open_folder_button.clicked.connect(self._open_selected_game_folder)
        self.launch_button = QPushButton(self._text('Launch Game', 'تشغيل اللعبة'))
        self.launch_button.setObjectName('refreshButton')
        self.launch_button.setMinimumHeight(42)
        self.launch_button.setMinimumWidth(130)
        self.launch_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.launch_button.setEnabled(False)
        self.launch_button.clicked.connect(self._launch_selected_game)
        actions_layout.addWidget(self.open_folder_button)
        actions_layout.addWidget(self.launch_button)
        self.status_label = QLabel(self._text('Open Game Lab to scan installed games.', 'افتح مختبر الألعاب لفحص الألعاب المثبتة.'))
        self.status_label.setObjectName('cleanerStatusLabel')
        self.status_label.setWordWrap(True)
        tab_layout.addLayout(toolbar_layout)
        tab_layout.addWidget(self.error_label)
        tab_layout.addWidget(summary_card)
        tab_layout.addWidget(self.games_table, 1)
        tab_layout.addLayout(actions_layout)
        tab_layout.addWidget(self.status_label)

    def _setup_readiness_tab(self, tab: QWidget) -> None:
        """إنشاء تبويب جاهزية الألعاب."""
        tab_layout = QVBoxLayout(tab)
        tab_layout.setContentsMargins(0, 18, 0, 0)
        tab_layout.setSpacing(16)
        toolbar_layout = QHBoxLayout()
        toolbar_layout.setSpacing(12)
        title_layout = QVBoxLayout()
        title_layout.setSpacing(4)
        readiness_title = QLabel(self._text('Windows Gaming Readiness', 'جاهزية ويندوز للألعاب'))
        readiness_title.setObjectName('cardTitle')
        readiness_description = QLabel(self._text('This scan only reads Windows settings. It does not change any setting.', 'هذا الفحص يقرأ إعدادات ويندوز فقط ولا يغيّر أي إعداد.'))
        readiness_description.setObjectName('pageSubtitle')
        readiness_description.setWordWrap(True)
        title_layout.addWidget(readiness_title)
        title_layout.addWidget(readiness_description)
        self.readiness_scan_button = QPushButton(self._text('Scan Readiness', 'فحص الجاهزية'))
        self.readiness_scan_button.setObjectName('refreshButton')
        self.readiness_scan_button.setMinimumHeight(42)
        self.readiness_scan_button.setMinimumWidth(150)
        self.readiness_scan_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.readiness_scan_button.clicked.connect(lambda _checked=False: self._start_readiness_scan())
        toolbar_layout.addLayout(title_layout, 1)
        toolbar_layout.addWidget(self.readiness_scan_button)
        self.readiness_panel = GameReadinessPanel()
        self.readiness_status_label = QLabel(self._text('Gaming readiness has not been scanned.', 'لم يتم فحص جاهزية الألعاب بعد.'))
        self.readiness_status_label.setObjectName('cleanerStatusLabel')
        self.readiness_status_label.setWordWrap(True)
        tab_layout.addLayout(toolbar_layout)
        tab_layout.addWidget(self.readiness_panel, 1)
        tab_layout.addWidget(self.readiness_status_label)

    def _setup_gaming_power_tab(self, tab: QWidget) -> None:
        """إنشاء تبويب تقدير أداء الألعاب."""
        tab_layout = QVBoxLayout(tab)
        tab_layout.setContentsMargins(0, 18, 0, 0)
        tab_layout.setSpacing(16)
        self.gaming_power_panel = GamingPowerPanel()
        self.gaming_power_panel.analyze_requested.connect(self._handle_gaming_power_request)
        self.gaming_power_panel.set_source_status(connected=True)
        tab_layout.addWidget(self.gaming_power_panel, 1)

    def showEvent(self, event: QShowEvent) -> None:
        """تشغيل الفحوصات عند فتح الصفحة أول مرة."""
        super().showEvent(event)
        if self.settings_service.get_bool('scanning/auto_scan_game_library') and (not self._scanned_once) and (not self._is_scanning()):
            self._start_scan()
        if self.settings_service.get_bool('scanning/auto_scan_game_readiness') and (not self._readiness_scanned_once) and (not self._is_readiness_scanning()):
            self._start_readiness_scan()
        if not self._gaming_hardware_loaded_once and (not self._is_gaming_hardware_scanning()):
            self._start_gaming_hardware_detection()

    def _start_scan(self) -> None:
        """بدء فحص الألعاب داخل Thread."""
        if self._is_scanning():
            return
        self.error_label.setVisible(False)
        self.games_table.clearSelection()
        self._set_action_buttons_enabled(False)
        self.scan_button.setEnabled(False)
        self.scan_button.setText(self._text('Scanning...', 'جارٍ الفحص...'))
        self.status_label.setText(self._text('Scanning Steam and Epic Games...', 'جارٍ فحص ألعاب ستيم وإيبك جيمز...'))
        self._scan_thread = QThread(self)
        self._scan_worker = GameLibraryWorker()
        self._scan_worker.moveToThread(self._scan_thread)
        self._scan_thread.started.connect(self._scan_worker.run)
        self._scan_worker.finished.connect(self._handle_scan_result)
        self._scan_worker.finished.connect(self._scan_thread.quit)
        self._scan_worker.failed.connect(self._handle_scan_error)
        self._scan_worker.failed.connect(self._scan_thread.quit)
        self._scan_worker.finished.connect(self._scan_worker.deleteLater)
        self._scan_worker.failed.connect(self._scan_worker.deleteLater)
        self._scan_thread.finished.connect(self._finish_scan)
        self._scan_thread.finished.connect(self._scan_thread.deleteLater)
        self._scan_thread.start()

    def _start_readiness_scan(self) -> None:
        """بدء فحص جاهزية الألعاب."""
        if self._is_readiness_scanning():
            return
        self.readiness_panel.set_loading()
        self.readiness_scan_button.setEnabled(False)
        self.readiness_scan_button.setText(self._text('Scanning...', 'جارٍ الفحص...'))
        self.readiness_status_label.setText(self._text('Reading Windows gaming settings...', 'جارٍ قراءة إعدادات ويندوز الخاصة بالألعاب...'))
        self._readiness_thread = QThread(self)
        self._readiness_worker = GameReadinessWorker()
        self._readiness_worker.moveToThread(self._readiness_thread)
        self._readiness_thread.started.connect(self._readiness_worker.run)
        self._readiness_worker.finished.connect(self._handle_readiness_result)
        self._readiness_worker.finished.connect(self._readiness_thread.quit)
        self._readiness_worker.failed.connect(self._handle_readiness_error)
        self._readiness_worker.failed.connect(self._readiness_thread.quit)
        self._readiness_worker.finished.connect(self._readiness_worker.deleteLater)
        self._readiness_worker.failed.connect(self._readiness_worker.deleteLater)
        self._readiness_thread.finished.connect(self._finish_readiness_scan)
        self._readiness_thread.finished.connect(self._readiness_thread.deleteLater)
        self._readiness_thread.start()

    def _start_gaming_hardware_detection(self) -> None:
        """قراءة CPU وGPU لتبويب Gaming Power."""
        if self._is_gaming_hardware_scanning():
            return
        self.gaming_power_panel.set_detecting_hardware()
        self._gaming_hardware_thread = QThread(self)
        self._gaming_hardware_worker = GamingHardwareWorker()
        self._gaming_hardware_worker.moveToThread(self._gaming_hardware_thread)
        self._gaming_hardware_thread.started.connect(self._gaming_hardware_worker.run)
        self._gaming_hardware_worker.finished.connect(self._handle_gaming_hardware_result)
        self._gaming_hardware_worker.finished.connect(self._gaming_hardware_thread.quit)
        self._gaming_hardware_worker.failed.connect(self._handle_gaming_hardware_error)
        self._gaming_hardware_worker.failed.connect(self._gaming_hardware_thread.quit)
        self._gaming_hardware_worker.finished.connect(self._gaming_hardware_worker.deleteLater)
        self._gaming_hardware_worker.failed.connect(self._gaming_hardware_worker.deleteLater)
        self._gaming_hardware_thread.finished.connect(self._finish_gaming_hardware_detection)
        self._gaming_hardware_thread.finished.connect(self._gaming_hardware_thread.deleteLater)
        self._gaming_hardware_thread.start()

    def _handle_scan_result(self, inventory: GameLibraryInventory) -> None:
        """عرض نتيجة فحص الألعاب."""
        self.inventory = inventory
        self._scanned_once = True
        self._update_summary()
        self._render_games()
        warning_count = len(inventory.warnings)
        status_text = f"{self._text('Game scan completed: ', 'اكتمل فحص الألعاب: ')}{inventory.total_games}{self._text(' game(s) detected.', ' لعبة مكتشفة.')}"
        if warning_count:
            status_text += f" {warning_count}{self._text(' warning(s) were recorded.', ' تحذير مسجّل.')}"
        self.status_label.setText(status_text)
        self.logger.info('Game Lab scan completed. Total: %s, Steam: %s, Epic: %s, warnings: %s', inventory.total_games, inventory.steam_games, inventory.epic_games, warning_count)

    def _handle_readiness_result(self, report: GameReadinessReport) -> None:
        """عرض تقرير جاهزية الألعاب."""
        self.readiness_report = report
        self._readiness_scanned_once = True
        self.readiness_panel.set_report(report)
        status_text = f"{self._text('Gaming readiness scan completed: ', 'اكتمل فحص جاهزية الألعاب: ')}{report.readiness_percentage}% ({self._translate_readiness_label(report.readiness_label)})."
        if report.warnings:
            status_text += f" {len(report.warnings)}{self._text(' warning(s) were recorded.', ' تحذير مسجّل.')}"
        self.readiness_status_label.setText(status_text)
        self.logger.info('Gaming readiness scan completed. Score: %s, label: %s, recommended: %s, attention: %s, unavailable: %s', report.readiness_percentage, self._translate_readiness_label(report.readiness_label), report.recommended_settings, report.attention_settings, report.unavailable_settings)

    def _handle_gaming_hardware_result(self, cpu_name: str, gpu_name: str) -> None:
        """عرض CPU وGPU داخل Gaming Power."""
        self._gaming_hardware_loaded_once = True
        self.gaming_power_panel.set_hardware(cpu_name=cpu_name, gpu_name=gpu_name)
        self.gaming_power_panel.set_source_status(connected=True)
        self.logger.info('Gaming Power hardware detected. CPU: %s, GPU: %s', cpu_name, gpu_name)

    def _handle_gaming_hardware_error(self, message: str) -> None:
        """عرض خطأ قراءة قطع Gaming Power."""
        self.gaming_power_panel.set_hardware_error(f"{self._text('Gaming hardware could not be detected: ', 'تعذر اكتشاف قطع الجهاز الخاصة بالألعاب: ')}{message}")
        self.logger.error('Gaming Power hardware detection failed: %s', message)

    def _handle_gaming_power_request(
        self,
        game_name: str,
        resolution: str,
        preset: str,
    ) -> None:
        """بدء جلب نتيجة FPS من FPSHQ."""

        if self._is_gaming_performance_lookup_running():
            return

        self.gaming_power_panel.set_loading()

        self._gaming_performance_thread = QThread(
            self
        )

        self._gaming_performance_worker = (
            GamingPerformanceWorker(
                game_name=game_name,
                resolution=resolution,
                preset=preset,
            )
        )

        self._gaming_performance_worker.moveToThread(
            self._gaming_performance_thread
        )

        self._gaming_performance_thread.started.connect(
            self._gaming_performance_worker.run
        )

        self._gaming_performance_worker.finished.connect(
            self._handle_gaming_performance_result
        )
        self._gaming_performance_worker.finished.connect(
            self._gaming_performance_thread.quit
        )

        self._gaming_performance_worker.failed.connect(
            self._handle_gaming_performance_error
        )
        self._gaming_performance_worker.failed.connect(
            self._gaming_performance_thread.quit
        )

        self._gaming_performance_worker.finished.connect(
            self._gaming_performance_worker.deleteLater
        )
        self._gaming_performance_worker.failed.connect(
            self._gaming_performance_worker.deleteLater
        )

        self._gaming_performance_thread.finished.connect(
            self._finish_gaming_performance_lookup
        )
        self._gaming_performance_thread.finished.connect(
            self._gaming_performance_thread.deleteLater
        )

        self.logger.info(
            "FPSHQ lookup started. Game: %s, "
            "resolution: %s, preset: %s.",
            game_name,
            resolution,
            preset,
        )

        self._gaming_performance_thread.start()

    def _handle_gaming_performance_result(
        self,
        result: OnlineGamingPerformanceResult,
    ) -> None:
        """عرض نتيجة FPSHQ داخل Gaming Power."""

        self.gaming_power_panel.set_result(
            result
        )

        self.logger.info(
            "FPSHQ lookup completed. Status: %s, "
            "average FPS: %s, minimum FPS: %s, "
            "maximum FPS: %s.",
            result.status.value,
            result.safe_average_fps,
            result.safe_minimum_fps,
            result.safe_maximum_fps,
        )

    def _handle_gaming_performance_error(
        self,
        message: str,
    ) -> None:
        """عرض خطأ تجهيز أو تشغيل طلب FPSHQ."""

        error_message = (
            self._text(
                "Gaming performance lookup failed: ",
                "فشل جلب تقدير أداء اللعبة: ",
            )
            + message
        )

        self.gaming_power_panel.set_error(
            error_message
        )

        self.logger.error(
            "FPSHQ lookup failed: %s",
            message,
        )

    def _handle_scan_error(self, message: str) -> None:
        """عرض خطأ فحص الألعاب."""
        self.inventory = None
        self._set_action_buttons_enabled(False)
        self.error_label.setText(f"{self._text('Game Lab scan failed: ', 'فشل فحص مختبر الألعاب: ')}{message}")
        self.error_label.setVisible(True)
        self.status_label.setText(self._text('Installed games could not be scanned.', 'تعذر فحص الألعاب المثبتة.'))
        self.logger.error('Game Lab scan failed: %s', message)

    def _handle_readiness_error(self, message: str) -> None:
        """عرض خطأ فحص جاهزية الألعاب."""
        self.readiness_report = None
        self.readiness_panel.set_error(f"{self._text('Gaming readiness scan failed: ', 'فشل فحص جاهزية الألعاب: ')}{message}")
        self.readiness_status_label.setText(self._text('Windows gaming settings could not be scanned.', 'تعذر فحص إعدادات ويندوز الخاصة بالألعاب.'))
        self.logger.error('Gaming readiness scan failed: %s', message)

    def _finish_scan(self) -> None:
        """تنظيف Thread الخاص بفحص الألعاب."""
        self._scan_worker = None
        self._scan_thread = None
        self.scan_button.setEnabled(True)
        self.scan_button.setText(self._text('Scan Again', 'إعادة الفحص'))
        self._update_action_buttons()

    def _finish_readiness_scan(self) -> None:
        """تنظيف Thread الخاص بفحص الجاهزية."""
        self._readiness_worker = None
        self._readiness_thread = None
        self.readiness_scan_button.setEnabled(True)
        self.readiness_scan_button.setText(self._text('Scan Again', 'إعادة الفحص'))

    def _finish_gaming_hardware_detection(self) -> None:
        """تنظيف Thread الخاص بقراءة قطع الألعاب."""
        self._gaming_hardware_worker = None
        self._gaming_hardware_thread = None

    def _finish_gaming_performance_lookup(self) -> None:
        """تنظيف Thread الخاص بطلب FPSHQ."""

        self._gaming_performance_worker = None
        self._gaming_performance_thread = None

    def _update_summary(self) -> None:
        """تحديث أرقام مكتبة الألعاب."""
        if self.inventory is None:
            self.total_games_label.setText('--')
            self.steam_games_label.setText('--')
            self.epic_games_label.setText('--')
            self.total_size_label.setText('--')
            return
        self.total_games_label.setText(f'{self.inventory.total_games:,}')
        self.steam_games_label.setText(f'{self.inventory.steam_games:,}')
        self.epic_games_label.setText(f'{self.inventory.epic_games:,}')
        self.total_size_label.setText(self._format_size(self.inventory.total_size_bytes))

    def _render_games(self) -> None:
        """عرض الألعاب داخل الجدول."""
        self.games_table.setSortingEnabled(False)
        self.games_table.setRowCount(0)
        if self.inventory is None:
            self.games_table.setSortingEnabled(True)
            return
        self.games_table.setRowCount(len(self.inventory.games))
        for row, game in enumerate(self.inventory.games):
            path_exists = self._path_exists(game.install_path)
            platform_item = QTableWidgetItem(game.platform)
            title_item = QTableWidgetItem(game.title)
            title_item.setData(Qt.ItemDataRole.UserRole, game)
            path_item = QTableWidgetItem(game.install_path)
            path_item.setToolTip(game.install_path)
            size_item = QTableWidgetItem(self._format_size(game.size_bytes) if game.size_bytes > 0 else self._text('Unknown', 'غير معروف'))
            size_item.setData(Qt.ItemDataRole.UserRole, game.size_bytes)
            status_item = QTableWidgetItem(self._text('Installed', 'مثبتة') if path_exists else self._text('Path Missing', 'مسار التثبيت مفقود'))
            self.games_table.setItem(row, 0, platform_item)
            self.games_table.setItem(row, 1, title_item)
            self.games_table.setItem(row, 2, path_item)
            self.games_table.setItem(row, 3, size_item)
            self.games_table.setItem(row, 4, status_item)
        self.games_table.resizeRowsToContents()
        self.games_table.setSortingEnabled(True)
        self._set_action_buttons_enabled(False)

    def _open_selected_game_folder(self) -> None:
        """فتح مجلد اللعبة المحددة."""
        game = self._selected_game()
        if game is None:
            return
        try:
            self.game_action_service.open_install_folder(game)
        except GameActionError as error:
            self._show_action_error(title=self._text('Open Game Folder', 'فتح مجلد اللعبة'), message=str(error))
            return
        self.status_label.setText(f"{self._text('Opened installation folder: ', 'تم فتح مجلد تثبيت اللعبة: ')}{game.title}")
        self.logger.info('Game installation folder opened: %s', game.title)

    def _launch_selected_game(self) -> None:
        """تشغيل اللعبة المحددة."""
        game = self._selected_game()
        if game is None:
            return
        try:
            self.game_action_service.launch_game(game)
        except GameActionError as error:
            self._show_action_error(title=self._text('Launch Game', 'تشغيل اللعبة'), message=str(error))
            return
        self.status_label.setText(f"{self._text('Launch request sent: ', 'تم إرسال طلب تشغيل اللعبة: ')}{game.title}")
        self.logger.info('Game launch requested: %s [%s]', game.title, game.platform)

    def _selected_game(self) -> InstalledGame | None:
        """إرجاع اللعبة المحددة."""
        selected_row = self.games_table.currentRow()
        if selected_row < 0:
            return None
        title_item = self.games_table.item(selected_row, 1)
        if title_item is None:
            return None
        game = title_item.data(Qt.ItemDataRole.UserRole)
        if isinstance(game, InstalledGame):
            return game
        return None

    def _update_action_buttons(self) -> None:
        """تفعيل أزرار اللعبة عند تحديد صف."""
        if self._is_scanning():
            self._set_action_buttons_enabled(False)
            return
        game = self._selected_game()
        self._set_action_buttons_enabled(game is not None)

    def _set_action_buttons_enabled(self, enabled: bool) -> None:
        """تفعيل أو تعطيل أزرار اللعبة."""
        self.open_folder_button.setEnabled(enabled)
        self.launch_button.setEnabled(enabled)

    def _show_action_error(self, title: str, message: str) -> None:
        """عرض خطأ متعلق بلعبة."""
        QMessageBox.warning(self, title, message)
        self.status_label.setText(message)
        self.logger.warning('%s failed: %s', title, message)

    def _is_scanning(self) -> bool:
        """هل فحص الألعاب يعمل؟"""
        return self._scan_thread is not None and self._scan_thread.isRunning()

    def _is_readiness_scanning(self) -> bool:
        """هل فحص الجاهزية يعمل؟"""
        return self._readiness_thread is not None and self._readiness_thread.isRunning()

    def _is_gaming_hardware_scanning(self) -> bool:
        """هل قراءة CPU وGPU تعمل؟"""
        return self._gaming_hardware_thread is not None and self._gaming_hardware_thread.isRunning()

    def _is_gaming_performance_lookup_running(
        self,
    ) -> bool:
        """هل طلب FPSHQ يعمل حاليًا؟"""

        return (
            self._gaming_performance_thread
            is not None
            and self._gaming_performance_thread.isRunning()
        )

    @staticmethod
    def _path_exists(install_path: str) -> bool:
        """فحص وجود مجلد اللعبة."""
        try:
            return Path(install_path).is_dir()
        except OSError:
            return False

    @staticmethod
    def _create_summary_value(layout: QHBoxLayout, title: str) -> QLabel:
        """إنشاء قيمة داخل بطاقة الملخص."""
        container = QWidget()
        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.setSpacing(3)
        title_label = QLabel(title)
        title_label.setObjectName('cleanerSummaryTitle')
        value_label = QLabel('--')
        value_label.setObjectName('cleanerSummaryValue')
        container_layout.addWidget(title_label)
        container_layout.addWidget(value_label)
        layout.addWidget(container)
        return value_label

    def _translate_readiness_label(self, value: str) -> str:
        translations = {'excellent': 'ممتاز', 'very good': 'جيد جدًا', 'good': 'جيد', 'ready': 'جاهز', 'recommended': 'موصى به', 'needs attention': 'يحتاج إلى انتباه', 'not ready': 'غير جاهز', 'poor': 'ضعيف', 'unknown': 'غير معروف'}
        cleaned_value = str(value or '').strip()
        if not self.is_rtl:
            return cleaned_value
        return translations.get(cleaned_value.casefold(), cleaned_value)

    def _text(self, english: str, arabic: str) -> str:
        if self.is_rtl:
            return arabic
        return english

    @staticmethod
    def _format_size(size_bytes: int) -> str:
        """تنسيق الحجم تلقائيًا."""
        value = max(0.0, float(size_bytes))
        units = ('B', 'KB', 'MB', 'GB', 'TB')
        unit_index = 0
        while value >= 1024 and unit_index < len(units) - 1:
            value /= 1024
            unit_index += 1
        if unit_index == 0:
            return f'{value:.0f} {units[unit_index]}'
        return f'{value:.2f} {units[unit_index]}'