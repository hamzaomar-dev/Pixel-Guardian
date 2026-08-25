from __future__ import annotations

from PySide6.QtCore import (
    Qt,
    Signal,
)
from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
)

from core.models.online_gaming_performance import (
    GamingPreset,
    GamingResolution,
    OnlineGamingPerformanceResult,
)
from core.services.application_settings_service import (
    ApplicationSettingsService,
)
from core.services.localization_service import (
    LocalizationService,
)


class GamingPowerPanel(QFrame):
    """
    واجهة تقدير أداء الجهاز داخل الألعاب.

    تستخدم FPSHQ لجلب متوسط ونطاق FPS المتوقع
    حسب اللعبة وكرت الشاشة والدقة والإعدادات.
    """

    analyze_requested = Signal(
        str,
        str,
        str,
    )

    def __init__(
        self,
        parent=None,
    ) -> None:
        super().__init__(
            parent
        )

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

        self._hardware_available = False
        self._provider_connected = False

        self._current_game_name = ""
        self._current_resolution = ""
        self._current_preset = ""

        self._setup_ui()
        self.set_source_status(
            connected=False
        )

    def _setup_ui(
        self,
    ) -> None:
        """إنشاء عناصر واجهة Gaming Power."""

        main_layout = QVBoxLayout(
            self
        )

        main_layout.setContentsMargins(
            24,
            22,
            24,
            22,
        )

        main_layout.setSpacing(
            18
        )

        self._create_header(
            main_layout
        )

        self._create_hardware_section(
            main_layout
        )

        self._create_controls_section(
            main_layout
        )

        self._create_results_section(
            main_layout
        )

        self.status_label = QLabel(
            self._text(
                "Detecting gaming hardware...",
                "جارٍ اكتشاف عتاد الألعاب...",
            )
        )

        self.status_label.setObjectName(
            "cleanerStatusLabel"
        )

        self.status_label.setWordWrap(
            True
        )

        self.status_label.setAlignment(
            Qt.AlignmentFlag.AlignLeading
            | Qt.AlignmentFlag.AlignVCenter
        )

        main_layout.addWidget(
            self.status_label
        )

        main_layout.addStretch()

    def _create_header(
        self,
        parent_layout: QVBoxLayout,
    ) -> None:
        """إنشاء عنوان القسم."""

        title = QLabel(
            self._text(
                "Gaming Power",
                "قوة الألعاب",
            )
        )

        title.setObjectName(
            "cardTitle"
        )

        title.setAlignment(
            Qt.AlignmentFlag.AlignLeading
            | Qt.AlignmentFlag.AlignVCenter
        )

        subtitle = QLabel(
            self._text(
                (
                    "Prepare an online FPS estimate using the "
                    "detected processor and graphics card."
                ),
                (
                    "جهّز تقديرًا لمعدل الإطارات عبر الإنترنت "
                    "باستخدام المعالج وكرت الشاشة المكتشفين."
                ),
            )
        )

        subtitle.setObjectName(
            "pageSubtitle"
        )

        subtitle.setWordWrap(
            True
        )

        subtitle.setAlignment(
            Qt.AlignmentFlag.AlignLeading
            | Qt.AlignmentFlag.AlignVCenter
        )

        provider_note = QLabel(
            self._text(
                (
                    "Online FPS estimates are provided by FPSHQ. "
                    "No API key is required."
                ),
                (
                    "يتم جلب تقديرات معدل الإطارات من FPSHQ "
                    "ولا يلزم مفتاح API."
                ),
            )
        )

        provider_note.setObjectName(
            "pageSubtitle"
        )

        provider_note.setWordWrap(
            True
        )

        provider_note.setAlignment(
            Qt.AlignmentFlag.AlignLeading
            | Qt.AlignmentFlag.AlignVCenter
        )

        parent_layout.addWidget(
            title
        )

        parent_layout.addWidget(
            subtitle
        )

        parent_layout.addWidget(
            provider_note
        )

    def _create_hardware_section(
        self,
        parent_layout: QVBoxLayout,
    ) -> None:
        """عرض المعالج وكرت الشاشة المكتشفين."""

        hardware_card = QFrame()
        hardware_card.setObjectName(
            "cleanerSummaryCard"
        )

        hardware_layout = QGridLayout(
            hardware_card
        )

        hardware_layout.setContentsMargins(
            20,
            18,
            20,
            18,
        )

        hardware_layout.setHorizontalSpacing(
            30
        )

        hardware_layout.setVerticalSpacing(
            8
        )

        cpu_title = QLabel(
            self._text(
                "Detected Processor",
                "المعالج المكتشف",
            )
        )

        cpu_title.setObjectName(
            "cleanerSummaryTitle"
        )

        self.cpu_value_label = QLabel(
            self._text(
                "Detecting...",
                "جارٍ الاكتشاف...",
            )
        )

        self.cpu_value_label.setObjectName(
            "cleanerSummaryValue"
        )

        self.cpu_value_label.setWordWrap(
            True
        )

        gpu_title = QLabel(
            self._text(
                "Detected Graphics Card",
                "كرت الشاشة المكتشف",
            )
        )

        gpu_title.setObjectName(
            "cleanerSummaryTitle"
        )

        self.gpu_value_label = QLabel(
            self._text(
                "Detecting...",
                "جارٍ الاكتشاف...",
            )
        )

        self.gpu_value_label.setObjectName(
            "cleanerSummaryValue"
        )

        self.gpu_value_label.setWordWrap(
            True
        )

        hardware_layout.addWidget(
            cpu_title,
            0,
            0,
        )

        hardware_layout.addWidget(
            gpu_title,
            0,
            1,
        )

        hardware_layout.addWidget(
            self.cpu_value_label,
            1,
            0,
        )

        hardware_layout.addWidget(
            self.gpu_value_label,
            1,
            1,
        )

        hardware_layout.setColumnStretch(
            0,
            1,
        )

        hardware_layout.setColumnStretch(
            1,
            1,
        )

        parent_layout.addWidget(
            hardware_card
        )

    def _create_controls_section(
        self,
        parent_layout: QVBoxLayout,
    ) -> None:
        """إنشاء خيارات اللعبة والدقة والجودة."""

        controls_card = QFrame()
        controls_card.setObjectName(
            "cleanerSummaryCard"
        )

        controls_layout = QGridLayout(
            controls_card
        )

        controls_layout.setContentsMargins(
            20,
            18,
            20,
            18,
        )

        controls_layout.setHorizontalSpacing(
            14
        )

        controls_layout.setVerticalSpacing(
            8
        )

        game_label = QLabel(
            self._text(
                "Game",
                "اللعبة",
            )
        )

        game_label.setObjectName(
            "cleanerSummaryTitle"
        )

        resolution_label = QLabel(
            self._text(
                "Resolution",
                "الدقة",
            )
        )

        resolution_label.setObjectName(
            "cleanerSummaryTitle"
        )

        preset_label = QLabel(
            self._text(
                "Graphics Preset",
                "إعدادات الرسومات",
            )
        )

        preset_label.setObjectName(
            "cleanerSummaryTitle"
        )

        self.game_input = QLineEdit()
        self.game_input.setObjectName(
            "gamingPowerGameInput"
        )

        self.game_input.setPlaceholderText(
            self._text(
                "Example: Fortnite",
                "مثال: Fortnite",
            )
        )

        self.game_input.setMinimumHeight(
            42
        )

        self.resolution_combo = QComboBox()
        self.resolution_combo.setObjectName(
            "gamingPowerCombo"
        )

        self.resolution_combo.setMinimumHeight(
            42
        )

        for resolution in GamingResolution:
            self.resolution_combo.addItem(
                self._resolution_display_text(
                    resolution.value
                ),
                resolution.value,
            )

        self.preset_combo = QComboBox()
        self.preset_combo.setObjectName(
            "gamingPowerCombo"
        )

        self.preset_combo.setMinimumHeight(
            42
        )

        for preset in GamingPreset:
            self.preset_combo.addItem(
                self._preset_display_text(
                    preset.value
                ),
                preset.value,
            )

        high_index = (
            self.preset_combo.findData(
                GamingPreset.HIGH.value
            )
        )

        if high_index >= 0:
            self.preset_combo.setCurrentIndex(
                high_index
            )

        self.analyze_button = QPushButton(
            self._text(
                "Check Performance",
                "فحص الأداء",
            )
        )

        self.analyze_button.setObjectName(
            "refreshButton"
        )

        self.analyze_button.setMinimumHeight(
            42
        )

        self.analyze_button.setMinimumWidth(
            175
        )

        self.analyze_button.setCursor(
            Qt.CursorShape.PointingHandCursor
        )

        self.analyze_button.clicked.connect(
            self._emit_analyze_request
        )

        controls_layout.addWidget(
            game_label,
            0,
            0,
        )

        controls_layout.addWidget(
            resolution_label,
            0,
            1,
        )

        controls_layout.addWidget(
            preset_label,
            0,
            2,
        )

        controls_layout.addWidget(
            self.game_input,
            1,
            0,
        )

        controls_layout.addWidget(
            self.resolution_combo,
            1,
            1,
        )

        controls_layout.addWidget(
            self.preset_combo,
            1,
            2,
        )

        controls_layout.addWidget(
            self.analyze_button,
            1,
            3,
        )

        controls_layout.setColumnStretch(
            0,
            3,
        )

        controls_layout.setColumnStretch(
            1,
            1,
        )

        controls_layout.setColumnStretch(
            2,
            1,
        )

        parent_layout.addWidget(
            controls_card
        )

    def _create_results_section(
        self,
        parent_layout: QVBoxLayout,
    ) -> None:
        """إنشاء بطاقات نتائج الأداء."""

        results_card = QFrame()
        results_card.setObjectName(
            "cleanerSummaryCard"
        )

        results_layout = QHBoxLayout(
            results_card
        )

        results_layout.setContentsMargins(
            20,
            18,
            20,
            18,
        )

        results_layout.setSpacing(
            20
        )

        self.average_fps_value = (
            self._create_metric(
                results_layout,
                title=self._text(
                    "Average FPS",
                    "متوسط الإطارات",
                ),
                value="—",
            )
        )

        self.minimum_fps_value = (
            self._create_metric(
                results_layout,
                title=self._text(
                    "Minimum FPS",
                    "أقل إطارات",
                ),
                value="—",
            )
        )

        self.maximum_fps_value = (
            self._create_metric(
                results_layout,
                title=self._text(
                    "Maximum FPS",
                    "أعلى إطارات",
                ),
                value="—",
            )
        )

        self.rating_value = (
            self._create_metric(
                results_layout,
                title=self._text(
                    "Performance",
                    "الأداء",
                ),
                value=self._text(
                    "Unavailable",
                    "غير متوفر",
                ),
            )
        )

        self.source_value = (
            self._create_metric(
                results_layout,
                title=self._text(
                    "Data Source",
                    "مصدر البيانات",
                ),
                value=self._text(
                    "Not Connected",
                    "غير متصل",
                ),
            )
        )

        results_layout.addStretch()

        parent_layout.addWidget(
            results_card
        )

    @staticmethod
    def _create_metric(
        layout: QHBoxLayout,
        title: str,
        value: str,
    ) -> QLabel:
        """إنشاء قيمة واحدة داخل بطاقة النتائج."""

        container = QFrame()

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
            4
        )

        title_label = QLabel(
            title
        )

        title_label.setObjectName(
            "cleanerSummaryTitle"
        )

        value_label = QLabel(
            value
        )

        value_label.setObjectName(
            "cleanerSummaryValue"
        )

        value_label.setWordWrap(
            True
        )

        container_layout.addWidget(
            title_label
        )

        container_layout.addWidget(
            value_label
        )

        layout.addWidget(
            container,
            1,
        )

        return value_label

    def set_detecting_hardware(
        self,
    ) -> None:
        """عرض حالة اكتشاف قطع الجهاز."""

        self._hardware_available = False

        detecting_text = self._text(
            "Detecting...",
            "جارٍ الاكتشاف...",
        )

        self.cpu_value_label.setText(
            detecting_text
        )

        self.gpu_value_label.setText(
            detecting_text
        )

        self.status_label.setText(
            self._text(
                (
                    "Detecting the processor "
                    "and graphics card..."
                ),
                (
                    "جارٍ اكتشاف المعالج "
                    "وكرت الشاشة..."
                ),
            )
        )

        self._refresh_button_state()

    def set_hardware(
        self,
        cpu_name: str,
        gpu_name: str,
    ) -> None:
        """عرض القطع المكتشفة."""

        clean_cpu_name = (
            str(cpu_name or "").strip()
        )

        clean_gpu_name = (
            str(gpu_name or "").strip()
        )

        unavailable_text = self._text(
            "Unavailable",
            "غير متوفر",
        )

        self.cpu_value_label.setText(
            clean_cpu_name
            or unavailable_text
        )

        self.gpu_value_label.setText(
            clean_gpu_name
            or unavailable_text
        )

        self._hardware_available = bool(
            clean_cpu_name
            and clean_gpu_name
        )

        if self._hardware_available:
            if self._provider_connected:
                self.status_label.setText(
                    self._text(
                        (
                            "Gaming hardware detected. "
                            "FPSHQ is ready."
                        ),
                        (
                            "تم اكتشاف عتاد الألعاب "
                            "وFPSHQ جاهز."
                        ),
                    )
                )
            else:
                self.status_label.setText(
                    self._text(
                        (
                            "Gaming hardware detected. "
                            "The online FPS source is not connected."
                        ),
                        (
                            "تم اكتشاف عتاد الألعاب. "
                            "مصدر الإطارات عبر الإنترنت غير متصل."
                        ),
                    )
                )

        else:
            self.status_label.setText(
                self._text(
                    (
                        "Processor or graphics card information "
                        "is unavailable."
                    ),
                    (
                        "معلومات المعالج أو كرت الشاشة "
                        "غير متوفرة."
                    ),
                )
            )

        self._refresh_button_state()

    def set_hardware_error(
        self,
        message: str,
    ) -> None:
        """عرض خطأ اكتشاف قطع الجهاز."""

        self._hardware_available = False

        unavailable_text = self._text(
            "Unavailable",
            "غير متوفر",
        )

        self.cpu_value_label.setText(
            unavailable_text
        )

        self.gpu_value_label.setText(
            unavailable_text
        )

        self.source_value.setText(
            "FPSHQ"
        )

        self.status_label.setText(
            self._friendly_error_message(
                message
            )
        )

        self._refresh_button_state()

    def set_source_status(
        self,
        connected: bool,
        provider_name: str = "",
    ) -> None:
        """تحديث حالة مصدر FPS."""

        self._provider_connected = bool(
            connected
        )

        if self._provider_connected:
            clean_provider_name = (
                provider_name.strip()
                or "FPSHQ"
            )

            self.source_value.setText(
                clean_provider_name
            )

            if self._hardware_available:
                self.status_label.setText(
                    self._text(
                        (
                            "FPSHQ gaming performance "
                            "source is connected."
                        ),
                        (
                            "تم الاتصال بمصدر FPSHQ "
                            "لبيانات أداء الألعاب."
                        ),
                    )
                )

        else:
            self.source_value.setText(
                self._text(
                    "Not Connected",
                    "غير متصل",
                )
            )

            if self._hardware_available:
                self.status_label.setText(
                    self._text(
                        (
                            "Gaming hardware detected. "
                            "The online FPS source is not connected yet."
                        ),
                        (
                            "تم اكتشاف عتاد الألعاب. "
                            "مصدر الإطارات عبر الإنترنت غير متصل بعد."
                        ),
                    )
                )

        self._refresh_button_state()

    def show_pending_request(
        self,
        game_name: str,
        resolution: str,
        preset: str,
    ) -> None:
        """عرض أن الطلب جاهز وينتظر اتصال الـAPI."""

        self.average_fps_value.setText(
            "—"
        )

        self.minimum_fps_value.setText(
            "—"
        )

        self.maximum_fps_value.setText(
            "—"
        )

        self.rating_value.setText(
            self._text(
                "Request Ready",
                "الطلب جاهز",
            )
        )

        self.source_value.setText(
            self._text(
                "FPSHQ",
                "FPSHQ",
            )
        )

        if self.is_rtl:
            status_text = (
                f"تم تجهيز طلب اللعبة {game_name} "
                f"بدقة {self._resolution_display_text(resolution)} "
                f"وإعدادات {self._preset_display_text(preset)}. "
                "سيتم إرسال الطلب إلى FPSHQ "
                "عند بدء الفحص."
            )
        else:
            status_text = (
                f"Request prepared for {game_name} "
                f"at {resolution} / {preset}. "
                "The request will be sent to FPSHQ "
                "when the check starts."
            )

        self.status_label.setText(
            status_text
        )

    def set_loading(
        self,
    ) -> None:
        """عرض حالة جلب نتيجة FPSHQ."""

        self.analyze_button.setEnabled(
            False
        )

        self.analyze_button.setText(
            self._text(
                "Checking...",
                "جارٍ الفحص...",
            )
        )

        self.average_fps_value.setText(
            "..."
        )

        self.minimum_fps_value.setText(
            "..."
        )

        self.maximum_fps_value.setText(
            "..."
        )

        self.rating_value.setText(
            self._text(
                "Loading",
                "جارٍ التحميل",
            )
        )

        game_name = (
            self._current_game_name.strip()
        )

        if game_name:
            self.status_label.setText(
                self._text(
                    (
                        f"Checking {game_name} "
                        "with FPSHQ..."
                    ),
                    (
                        f"جارٍ فحص {game_name} "
                        "عبر FPSHQ..."
                    ),
                )
            )
        else:
            self.status_label.setText(
                self._text(
                    (
                        "Retrieving gaming "
                        "performance data from FPSHQ..."
                    ),
                    (
                        "جارٍ جلب بيانات أداء "
                        "الألعاب من FPSHQ..."
                    ),
                )
            )

    def set_result(
        self,
        result: OnlineGamingPerformanceResult,
    ) -> None:
        """عرض نتيجة FPSHQ."""

        self.analyze_button.setText(
            self._text(
                "Check Performance",
                "فحص الأداء",
            )
        )

        if not result.is_available:
            self.set_error(
                result.message
                or self._text(
                    (
                        "Gaming performance data "
                        "is unavailable."
                    ),
                    (
                        "بيانات أداء الألعاب "
                        "غير متوفرة."
                    ),
                )
            )
            return

        average_fps = (
            result.safe_average_fps
        )

        minimum_fps = (
            result.safe_minimum_fps
        )

        maximum_fps = (
            result.safe_maximum_fps
        )

        self.average_fps_value.setText(
            (
                f"{average_fps:.1f} FPS"
                if average_fps is not None
                else "—"
            )
        )

        self.minimum_fps_value.setText(
            (
                f"{minimum_fps:.1f} FPS"
                if minimum_fps is not None
                else "—"
            )
        )

        self.maximum_fps_value.setText(
            (
                f"{maximum_fps:.1f} FPS"
                if maximum_fps is not None
                else "—"
            )
        )

        performance_text = (
            result.verdict.strip()
            if result.verdict.strip()
            else result.performance_label
        )

        self.rating_value.setText(
            self._translate_performance_label(
                performance_text
            )
        )

        provider_name = (
            result.provider_name.strip()
            or self._text(
                "Online Provider",
                "المزود عبر الإنترنت",
            )
        )

        source_type = self._result_source_display_text(
            result.result_source.value
        )

        self.source_value.setText(
            (
                f"{provider_name} • {source_type}"
                if source_type
                else provider_name
            )
        )

        game_name = (
            self._current_game_name
            or result.request.game.strip()
        )

        resolution_text = self._resolution_display_text(
            result.request.resolution.value
        )

        preset_text = self._preset_display_text(
            result.request.preset.value
        )

        average_text = (
            f"{average_fps:.1f}"
            if average_fps is not None
            else "—"
        )

        if (
            minimum_fps is not None
            and maximum_fps is not None
        ):
            range_text = (
                f"{minimum_fps:.1f} - "
                f"{maximum_fps:.1f} FPS"
            )
        else:
            range_text = self._text(
                "Range unavailable",
                "النطاق غير متوفر",
            )

        if self.is_rtl:
            status_text = (
                f"تم تحميل نتيجة {game_name}: "
                f"المتوسط {average_text} FPS، "
                f"النطاق {range_text}، "
                f"بدقة {resolution_text} "
                f"وإعدادات {preset_text}."
            )
        else:
            status_text = (
                f"{game_name}: {average_text} FPS average, "
                f"{range_text}, "
                f"{resolution_text} / {preset_text}."
            )

        self.status_label.setText(
            status_text
        )

        self._refresh_button_state()

    def set_error(
        self,
        message: str,
    ) -> None:
        """عرض خطأ جلب نتيجة FPSHQ."""

        self.analyze_button.setText(
            self._text(
                "Check Performance",
                "فحص الأداء",
            )
        )

        self.average_fps_value.setText(
            "—"
        )

        self.minimum_fps_value.setText(
            "—"
        )

        self.maximum_fps_value.setText(
            "—"
        )

        self.rating_value.setText(
            self._text(
                "Unavailable",
                "غير متوفر",
            )
        )

        self.status_label.setText(
            self._translate_dynamic_text(
                message
            )
        )

        self._refresh_button_state()

    def _refresh_button_state(
        self,
    ) -> None:
        """
        السماح بالفحص عند توفر العتاد واتصال FPSHQ.
        """

        self.analyze_button.setEnabled(
            self._hardware_available
            and self._provider_connected
        )

    def _emit_analyze_request(
        self,
    ) -> None:
        """إرسال خيارات الفحص إلى Game Lab."""

        game_name = (
            self.game_input
            .text()
            .strip()
        )

        if not game_name:
            self.status_label.setText(
                self._text(
                    (
                        "Enter a game name before "
                        "checking performance."
                    ),
                    (
                        "أدخل اسم لعبة قبل "
                        "فحص الأداء."
                    ),
                )
            )
            return

        resolution = str(
            self.resolution_combo
            .currentData()
            or ""
        )

        preset = str(
            self.preset_combo
            .currentData()
            or ""
        )

        self._current_game_name = game_name
        self._current_resolution = resolution
        self._current_preset = preset

        self.analyze_requested.emit(
            game_name,
            resolution,
            preset,
        )

    def _resolution_display_text(
        self,
        value: str,
    ) -> str:
        """عرض اسم الدقة حسب لغة البرنامج."""

        text = str(value).strip()

        if not self.is_rtl:
            return text

        translations = {
            "native": "الدقة الأصلية",
            "automatic": "تلقائي",
            "auto": "تلقائي",
        }

        return translations.get(
            text.casefold(),
            text,
        )

    def _preset_display_text(
        self,
        value: str,
    ) -> str:
        """عرض مستوى الرسومات حسب لغة البرنامج."""

        text = str(value).strip()

        if not self.is_rtl:
            return text

        translations = {
            "very low": "منخفض جدًا",
            "low": "منخفض",
            "medium": "متوسط",
            "high": "مرتفع",
            "very high": "مرتفع جدًا",
            "ultra": "فائق",
            "epic": "ملحمي",
            "maximum": "أقصى",
            "max": "أقصى",
            "custom": "مخصص",
            "automatic": "تلقائي",
            "auto": "تلقائي",
        }

        return translations.get(
            text.casefold(),
            text,
        )

    def _result_source_display_text(
        self,
        value: str,
    ) -> str:
        """عرض نوع نتيجة FPSHQ حسب لغة البرنامج."""

        text = str(value or "").strip().casefold()

        translations = {
            "benchmark": (
                "Benchmark",
                "اختبار فعلي",
            ),
            "prediction": (
                "Prediction",
                "توقع",
            ),
            "unknown": (
                "Unknown",
                "غير معروف",
            ),
        }

        english, arabic = translations.get(
            text,
            (
                str(value or "").strip(),
                str(value or "").strip(),
            ),
        )

        return self._text(
            english,
            arabic,
        )

    def _translate_performance_label(
        self,
        value,
    ) -> str:
        """ترجمة تصنيف الأداء القادم من مزود FPS."""

        text = str(value or "").strip()

        if not text:
            return self._text(
                "Unavailable",
                "غير متوفر",
            )

        if not self.is_rtl:
            return text

        translations = {
            "high refresh rate": "معدل تحديث مرتفع",
            "smooth": "سلس",
            "excellent": "ممتاز",
            "very good": "جيد جدًا",
            "good": "جيد",
            "playable": "قابل للعب",
            "fair": "مقبول",
            "limited": "محدود",
            "poor": "ضعيف",
            "unplayable": "غير قابل للعب",
            "unavailable": "غير متوفر",
            "unknown": "غير معروف",
        }

        return translations.get(
            text.casefold(),
            text,
        )

    def _friendly_error_message(
        self,
        value,
    ) -> str:
        """تحويل أخطاء FPSHQ إلى رسالة مفهومة."""

        text = str(value or "").strip()
        normalized = text.casefold()

        if (
            "selected game was not found" in normalized
            or (
                "game" in normalized
                and "not found" in normalized
            )
        ):
            return self._text(
                (
                    "Game not found in FPSHQ. "
                    "Try the full official title, "
                    "for example: Grand Theft Auto V."
                ),
                (
                    "لم يتم العثور على اللعبة في FPSHQ. "
                    "جرّب الاسم الرسمي الكامل، مثل: "
                    "Grand Theft Auto V."
                ),
            )

        if (
            "graphics card" in normalized
            and "not found" in normalized
        ):
            return self._text(
                (
                    "The graphics card was not found "
                    "in FPSHQ. Try again later or use "
                    "a shorter GPU model name."
                ),
                (
                    "لم يتم العثور على كرت الشاشة "
                    "في FPSHQ. جرّب لاحقًا أو استخدم "
                    "اسم موديل أقصر للكرت."
                ),
            )

        if (
            "internet connection" in normalized
            or "could not connect" in normalized
            or "offline" in normalized
        ):
            return self._text(
                (
                    "Could not connect to FPSHQ. "
                    "Check the internet connection "
                    "and try again."
                ),
                (
                    "تعذر الاتصال بـFPSHQ. "
                    "تحقق من اتصال الإنترنت "
                    "ثم أعد المحاولة."
                ),
            )

        if (
            "timed out" in normalized
            or "did not respond in time" in normalized
        ):
            return self._text(
                (
                    "FPSHQ took too long to respond. "
                    "Please try again."
                ),
                (
                    "تأخر FPSHQ في الاستجابة. "
                    "أعد المحاولة."
                ),
            )

        if (
            "rate" in normalized
            and "limit" in normalized
        ):
            return self._text(
                (
                    "FPSHQ temporarily limited the requests. "
                    "Wait a little and try again."
                ),
                (
                    "فرض FPSHQ حدًا مؤقتًا على الطلبات. "
                    "انتظر قليلًا ثم أعد المحاولة."
                ),
            )

        if (
            "invalid json" in normalized
            or "invalid response" in normalized
        ):
            return self._text(
                (
                    "FPSHQ returned an unexpected response. "
                    "Please try again later."
                ),
                (
                    "أرسل FPSHQ استجابة غير متوقعة. "
                    "أعد المحاولة لاحقًا."
                ),
            )

        return self._translate_dynamic_text(
            text
            or self._text(
                "Gaming performance data is unavailable.",
                "بيانات أداء الألعاب غير متوفرة.",
            )
        )

    def _translate_dynamic_text(
        self,
        value,
    ) -> str:
        """ترجمة رسائل الأخطاء والحالات الشائعة."""

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

        replacements = (
            (
                "Gaming hardware could not be detected:",
                "تعذر اكتشاف عتاد الألعاب:",
            ),
            (
                "Gaming performance data is unavailable.",
                "بيانات أداء الألعاب غير متوفرة.",
            ),
            (
                "Processor or graphics card information is unavailable.",
                "معلومات المعالج أو كرت الشاشة غير متوفرة.",
            ),
            (
                "Online FPS source is not connected.",
                "مصدر الإطارات عبر الإنترنت غير متصل.",
            ),
            (
                "Unknown error",
                "خطأ غير معروف",
            ),
            (
                "Unavailable",
                "غير متوفر",
            ),
            (
                "Not Connected",
                "غير متصل",
            ),
        )

        translated = text

        for english, arabic in replacements:
            translated = translated.replace(
                english,
                arabic,
            )

        return translated

    def _text(
        self,
        english: str,
        arabic: str,
    ) -> str:
        """اختيار النص حسب لغة البرنامج."""

        if self.is_rtl:
            return arabic

        return english
