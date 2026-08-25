from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import StrEnum


class HardwareKind(StrEnum):
    """أنواع القطع التي يمكن البحث عن أدائها."""

    CPU = "cpu"
    GPU = "gpu"


class BenchmarkLookupStatus(StrEnum):
    """حالة البحث عن نتيجة القطعة."""

    SUCCESS = "success"
    NOT_FOUND = "not_found"
    OFFLINE = "offline"
    ERROR = "error"


class BenchmarkMetricType(StrEnum):
    """نوع اختبار الأداء القادم من المصدر."""

    OVERALL = "overall"
    GAMING = "gaming"
    GRAPHICS = "graphics"
    COMPUTE = "compute"
    SINGLE_CORE = "single_core"
    MULTI_CORE = "multi_core"


@dataclass(frozen=True, slots=True)
class DetectedHardware:
    """قطعة اكتشفها Pixel Guardian من الجهاز الحالي."""

    kind: HardwareKind

    raw_name: str
    normalized_name: str

    vendor: str = "Unknown"

    physical_cores: int | None = None
    logical_cores: int | None = None

    dedicated_memory_bytes: int | None = None

    @property
    def dedicated_memory_gb(
        self,
    ) -> float | None:
        """حجم ذاكرة كرت الشاشة بالجيجابايت."""

        if (
            self.dedicated_memory_bytes is None
            or self.dedicated_memory_bytes <= 0
        ):
            return None

        return round(
            self.dedicated_memory_bytes
            / (1024 ** 3),
            2,
        )


@dataclass(frozen=True, slots=True)
class BenchmarkSource:
    """معلومات الموقع أو الخدمة التي أعطت النتيجة."""

    provider_id: str
    provider_name: str

    homepage: str | None = None
    description: str = ""


@dataclass(frozen=True, slots=True)
class OnlineBenchmarkResult:
    """نتيجة Benchmark لقطعة واحدة من مصدر أونلاين."""

    hardware: DetectedHardware

    status: BenchmarkLookupStatus

    source: BenchmarkSource | None = None

    metric_type: BenchmarkMetricType = (
        BenchmarkMetricType.OVERALL
    )

    test_name: str = ""

    # النتيجة الأصلية كما أعادها المصدر.
    raw_score: float | None = None
    score_unit: str = "points"

    # تستخدم فقط عندما يوفر المصدر Percentile
    # أو عندما نحسبها لاحقًا من مجموعة بيانات موثقة.
    percentile: float | None = None

    sample_count: int | None = None

    benchmark_version: str | None = None
    measured_at: str | None = None

    fetched_at: str = field(
        default_factory=lambda: datetime.now(
            timezone.utc
        ).isoformat()
    )

    source_url: str | None = None

    # لا نخترعها يدويًا؛ يحددها مزود البيانات
    # حسب جودة المطابقة وعدد النتائج المتاحة.
    confidence: float = 0.0

    message: str = ""

    @property
    def is_available(self) -> bool:
        """هل تم الحصول على نتيجة فعلية؟"""

        return (
            self.status
            == BenchmarkLookupStatus.SUCCESS
            and self.raw_score is not None
        )

    @property
    def safe_percentile(
        self,
    ) -> float | None:
        """حصر Percentile بين صفر ومئة."""

        if self.percentile is None:
            return None

        return max(
            0.0,
            min(
                100.0,
                float(self.percentile),
            ),
        )

    @property
    def safe_confidence(self) -> float:
        """حصر الثقة بين صفر وواحد."""

        return max(
            0.0,
            min(
                1.0,
                float(self.confidence),
            ),
        )

    @property
    def confidence_percentage(self) -> int:
        """الثقة كنسبة مئوية."""

        return round(
            self.safe_confidence
            * 100
        )

    @property
    def confidence_label(self) -> str:
        """وصف جودة النتيجة والمطابقة."""

        confidence = (
            self.safe_confidence
        )

        if not self.is_available:
            return "Unavailable"

        if confidence >= 0.90:
            return "High"

        if confidence >= 0.70:
            return "Good"

        if confidence >= 0.45:
            return "Estimated"

        return "Low"

    @property
    def display_score(self) -> str:
        """تنسيق النتيجة الأصلية للعرض."""

        if self.raw_score is None:
            return "Unavailable"

        formatted_score = (
            f"{self.raw_score:,.2f}"
        ).rstrip("0").rstrip(".")

        if self.score_unit:
            return (
                f"{formatted_score} "
                f"{self.score_unit}"
            )

        return formatted_score


@dataclass(frozen=True, slots=True)
class OnlineBenchmarkReport:
    """تقرير نتائج المعالج وكرت الشاشة الأونلاين."""

    results: tuple[
        OnlineBenchmarkResult,
        ...
    ]

    queried_at: str = field(
        default_factory=lambda: datetime.now(
            timezone.utc
        ).isoformat()
    )

    warnings: tuple[str, ...] = ()

    @property
    def total_results(self) -> int:
        """إجمالي القطع التي تم البحث عنها."""

        return len(
            self.results
        )

    @property
    def available_results(self) -> int:
        """عدد القطع التي حصلنا على نتائج لها."""

        return sum(
            1
            for result in self.results
            if result.is_available
        )

    @property
    def coverage_percentage(self) -> int:
        """نسبة اكتمال نتائج البحث."""

        if self.total_results == 0:
            return 0

        return round(
            (
                self.available_results
                / self.total_results
            )
            * 100
        )

    @property
    def is_complete(self) -> bool:
        """هل جميع نتائج القطع متوفرة؟"""

        return (
            self.total_results > 0
            and self.available_results
            == self.total_results
        )

    def result_for(
        self,
        hardware_kind: HardwareKind,
    ) -> OnlineBenchmarkResult | None:
        """إرجاع نتيجة CPU أو GPU."""

        for result in self.results:
            if (
                result.hardware.kind
                == hardware_kind
            ):
                return result

        return None