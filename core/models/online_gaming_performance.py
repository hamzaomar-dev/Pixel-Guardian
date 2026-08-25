from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import StrEnum

from core.models.hardware_benchmark import (
    DetectedHardware,
    HardwareKind,
)


class GamingResolution(StrEnum):
    """الدقات المدعومة عند طلب نتيجة لعبة."""

    FULL_HD = "1080p"
    QUAD_HD = "1440p"
    ULTRA_HD = "4K"


class GamingPreset(StrEnum):
    """إعدادات الرسومات المطلوبة."""

    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"
    ULTRA = "Ultra"


class GamingLookupStatus(StrEnum):
    """حالة طلب بيانات الأداء."""

    SUCCESS = "success"
    NOT_FOUND = "not_found"
    OFFLINE = "offline"
    UNAUTHORIZED = "unauthorized"
    RATE_LIMITED = "rate_limited"
    ERROR = "error"


class GamingResultSource(StrEnum):
    """نوع مصدر نتيجة FPS."""

    BENCHMARK = "benchmark"
    PREDICTION = "prediction"
    UNKNOWN = "unknown"


@dataclass(frozen=True, slots=True)
class GamingPerformanceRequest:
    """طلب أداء تركيبة جهاز داخل لعبة محددة."""

    cpu: DetectedHardware
    gpu: DetectedHardware

    game: str

    resolution: GamingResolution = (
        GamingResolution.FULL_HD
    )

    preset: GamingPreset = (
        GamingPreset.HIGH
    )

    def __post_init__(
        self,
    ) -> None:
        """التحقق من صحة القطع واللعبة."""

        if self.cpu.kind != HardwareKind.CPU:
            raise ValueError(
                "The cpu field must contain CPU hardware."
            )

        if self.gpu.kind != HardwareKind.GPU:
            raise ValueError(
                "The gpu field must contain GPU hardware."
            )

        if not self.game.strip():
            raise ValueError(
                "The game name cannot be empty."
            )

    @property
    def cpu_query_name(self) -> str:
        """اسم المعالج المستخدم بطلب الإنترنت."""

        return (
            self.cpu.normalized_name
            or self.cpu.raw_name
        ).strip()

    @property
    def gpu_query_name(self) -> str:
        """اسم كرت الشاشة المستخدم بطلب الإنترنت."""

        return (
            self.gpu.normalized_name
            or self.gpu.raw_name
        ).strip()

    def to_api_payload(
        self,
    ) -> dict[str, str]:
        """تحويل الطلب إلى JSON جاهز للإرسال."""

        return {
            "cpu": self.cpu_query_name,
            "gpu": self.gpu_query_name,
            "game": self.game.strip(),
            "resolution": self.resolution.value,
            "preset": self.preset.value,
        }


@dataclass(frozen=True, slots=True)
class OnlineGamingPerformanceResult:
    """نتيجة أداء فعلية أو متوقعة للعبة."""

    request: GamingPerformanceRequest

    status: GamingLookupStatus

    average_fps: float | None = None

    minimum_fps: float | None = None
    maximum_fps: float | None = None

    one_percent_low_fps: float | None = None

    verdict: str = ""

    result_source: GamingResultSource = (
        GamingResultSource.UNKNOWN
    )

    provider_id: str = ""
    provider_name: str = ""

    source_url: str | None = None

    fetched_at: str = field(
        default_factory=lambda: datetime.now(
            timezone.utc
        ).isoformat()
    )

    message: str = ""

    @property
    def is_available(self) -> bool:
        """هل النتيجة قابلة للاستخدام؟"""

        return (
            self.status
            == GamingLookupStatus.SUCCESS
            and self.average_fps is not None
            and self.average_fps >= 0
        )

    @staticmethod
    def _safe_fps_value(
        value: float | None,
    ) -> float | None:
        """تنظيف قيمة FPS واحدة."""

        if value is None:
            return None

        return max(
            0.0,
            float(value),
        )

    @property
    def safe_average_fps(self) -> float | None:
        """تنظيف متوسط الإطارات."""

        return self._safe_fps_value(
            self.average_fps
        )

    @property
    def safe_minimum_fps(self) -> float | None:
        """تنظيف أقل قيمة FPS."""

        return self._safe_fps_value(
            self.minimum_fps
        )

    @property
    def safe_maximum_fps(self) -> float | None:
        """تنظيف أعلى قيمة FPS."""

        return self._safe_fps_value(
            self.maximum_fps
        )

    @property
    def safe_one_percent_low_fps(
        self,
    ) -> float | None:
        """تنظيف نتيجة 1% Low."""

        return self._safe_fps_value(
            self.one_percent_low_fps
        )

    @property
    def stability_percentage(
        self,
    ) -> int | None:
        """
        مقارنة 1% Low بمتوسط الإطارات.

        هذه ليست نسبة قوة الجهاز، وإنما مؤشر
        تقريبي على ثبات الإطارات داخل اللعبة.
        """

        average_fps = (
            self.safe_average_fps
        )

        low_fps = (
            self.safe_one_percent_low_fps
        )

        if (
            average_fps is None
            or low_fps is None
            or average_fps <= 0
        ):
            return None

        return round(
            min(
                100.0,
                (
                    low_fps
                    / average_fps
                )
                * 100.0,
            )
        )

    @property
    def fps_range_label(self) -> str:
        """عرض نطاق FPS بدون اعتباره 1% Low."""

        minimum = self.safe_minimum_fps
        maximum = self.safe_maximum_fps

        if (
            minimum is None
            or maximum is None
        ):
            return "Unavailable"

        return (
            f"{minimum:.0f} - "
            f"{maximum:.0f} FPS"
        )

    @property
    def performance_label(self) -> str:
        """وصف بسيط لنتيجة اللعبة."""

        fps = self.safe_average_fps

        if fps is None:
            return "Unavailable"

        if fps >= 120:
            return "High Refresh Rate"

        if fps >= 60:
            return "Smooth"

        if fps >= 45:
            return "Playable"

        if fps >= 30:
            return "Limited"

        return "Poor"


@dataclass(frozen=True, slots=True)
class OnlineGamingPerformanceReport:
    """مجموعة نتائج ألعاب لنفس الجهاز."""

    results: tuple[
        OnlineGamingPerformanceResult,
        ...
    ]

    generated_at: str = field(
        default_factory=lambda: datetime.now(
            timezone.utc
        ).isoformat()
    )

    warnings: tuple[str, ...] = ()

    @property
    def total_games(self) -> int:
        return len(
            self.results
        )

    @property
    def available_games(self) -> int:
        return sum(
            1
            for result in self.results
            if result.is_available
        )

    @property
    def coverage_percentage(self) -> int:
        """نسبة الألعاب التي حصلنا على بيانات لها."""

        if self.total_games == 0:
            return 0

        return round(
            (
                self.available_games
                / self.total_games
            )
            * 100
        )

    @property
    def average_fps(self) -> float | None:
        """متوسط نتائج الألعاب المتوفرة."""

        available_values = tuple(
            result.safe_average_fps
            for result in self.results
            if (
                result.is_available
                and result.safe_average_fps
                is not None
            )
        )

        if not available_values:
            return None

        return round(
            sum(available_values)
            / len(available_values),
            2,
        )