from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class GamingComponentAssessment:
    """تقييم قطعة واحدة من قطع الجهاز للألعاب."""

    key: str
    title: str
    detected_value: str

    score: int
    weight: float

    note: str
    available: bool = True

    @property
    def safe_score(self) -> int:
        """حصر النتيجة بين صفر ومئة."""

        return max(
            0,
            min(
                100,
                int(self.score),
            ),
        )

    @property
    def weighted_score(self) -> float:
        """نتيجة القطعة بعد تطبيق الوزن."""

        if not self.available:
            return 0.0

        return (
            self.safe_score
            * max(
                0.0,
                float(self.weight),
            )
        )

    @property
    def rating_label(self) -> str:
        """التقييم النصي للقطعة."""

        if not self.available:
            return "Unavailable"

        if self.safe_score >= 85:
            return "Excellent"

        if self.safe_score >= 70:
            return "Very Good"

        if self.safe_score >= 55:
            return "Good"

        if self.safe_score >= 40:
            return "Basic"

        return "Limited"


@dataclass(frozen=True, slots=True)
class GamingHardwareReport:
    """تقرير قوة الجهاز العامة للألعاب."""

    scanned_at: str
    target_resolution: str

    components: tuple[
        GamingComponentAssessment,
        ...
    ]

    warnings: tuple[str, ...] = ()

    @property
    def total_components(self) -> int:
        """إجمالي القطع الموجودة بالتقرير."""

        return len(
            self.components
        )

    @property
    def available_components(self) -> int:
        """عدد القطع التي أمكن تقييمها."""

        return sum(
            1
            for component in self.components
            if component.available
        )

    @property
    def coverage_percentage(self) -> int:
        """نسبة اكتمال بيانات التقييم."""

        if self.total_components == 0:
            return 0

        return round(
            (
                self.available_components
                / self.total_components
            )
            * 100
        )

    @property
    def overall_score(self) -> int:
        """حساب النتيجة العامة حسب أوزان القطع."""

        available = tuple(
            component
            for component in self.components
            if (
                component.available
                and component.weight > 0
            )
        )

        if not available:
            return 0

        total_weight = sum(
            component.weight
            for component in available
        )

        if total_weight <= 0:
            return 0

        total_score = sum(
            component.weighted_score
            for component in available
        )

        return round(
            total_score
            / total_weight
        )

    @property
    def rating_label(self) -> str:
        """التقييم النصي العام للجهاز."""

        score = self.overall_score

        if score >= 85:
            return "Excellent"

        if score >= 70:
            return "Very Good"

        if score >= 55:
            return "Good"

        if score >= 40:
            return "Basic"

        return "Limited"

    @property
    def recommended_preset(self) -> str:
        """إعداد الرسوم العام المقترح."""

        score = self.overall_score

        if score >= 85:
            return "High to Ultra"

        if score >= 70:
            return "High"

        if score >= 55:
            return "Medium"

        if score >= 40:
            return "Low to Medium"

        return "Low"

    @property
    def bottleneck_component(
        self,
    ) -> GamingComponentAssessment | None:
        """أضعف قطعة متاحة حسب نتيجة التقييم."""

        available = tuple(
            component
            for component in self.components
            if component.available
        )

        if not available:
            return None

        return min(
            available,
            key=lambda component:
            component.safe_score,
        )

    @property
    def bottleneck_title(self) -> str:
        """اسم القطعة الأضعف."""

        component = (
            self.bottleneck_component
        )

        if component is None:
            return "Unknown"

        return component.title