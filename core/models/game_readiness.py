from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class GamingSettingStatus:
    """حالة إعداد واحد متعلق بالألعاب."""

    key: str
    title: str
    description: str
    current_value: str
    recommended_value: str
    is_recommended: bool
    available: bool = True

    # بعض الإعدادات تكون معلوماتية فقط
    # ولا يصح إدخالها في نسبة التقييم.
    score_eligible: bool = True

    @property
    def status_text(self) -> str:
        """النص المختصر لحالة الإعداد."""

        if not self.available:
            return "Unavailable"

        if not self.score_eligible:
            return "Informational"

        if self.is_recommended:
            return "Recommended"

        return "Needs Attention"


@dataclass(frozen=True, slots=True)
class GameReadinessReport:
    """تقرير جاهزية Windows للألعاب."""

    scanned_at: str
    settings: tuple[GamingSettingStatus, ...]
    warnings: tuple[str, ...] = ()

    @property
    def total_settings(self) -> int:
        """إجمالي الإعدادات الموجودة في التقرير."""

        return len(
            self.settings
        )

    @property
    def available_settings(self) -> int:
        """عدد الإعدادات التي أمكن قراءتها."""

        return sum(
            1
            for setting in self.settings
            if setting.available
        )

    @property
    def evaluated_settings(self) -> int:
        """عدد الإعدادات الداخلة فعليًا في التقييم."""

        return sum(
            1
            for setting in self.settings
            if (
                setting.available
                and setting.score_eligible
            )
        )

    @property
    def recommended_settings(self) -> int:
        """عدد الإعدادات المطابقة للتوصية."""

        return sum(
            1
            for setting in self.settings
            if (
                setting.available
                and setting.score_eligible
                and setting.is_recommended
            )
        )

    @property
    def attention_settings(self) -> int:
        """عدد الإعدادات التي تحتاج مراجعة."""

        return sum(
            1
            for setting in self.settings
            if (
                setting.available
                and setting.score_eligible
                and not setting.is_recommended
            )
        )

    @property
    def informational_settings(self) -> int:
        """عدد الإعدادات المعلوماتية."""

        return sum(
            1
            for setting in self.settings
            if (
                setting.available
                and not setting.score_eligible
            )
        )

    @property
    def unavailable_settings(self) -> int:
        """عدد الإعدادات التي لم يمكن تحديدها."""

        return sum(
            1
            for setting in self.settings
            if not setting.available
        )

    @property
    def coverage_percentage(self) -> int:
        """نسبة الإعدادات التي أمكن قراءتها."""

        if self.total_settings == 0:
            return 0

        return round(
            (
                self.available_settings
                / self.total_settings
            )
            * 100
        )

    @property
    def readiness_percentage(self) -> int:
        """نسبة الإعدادات المطابقة من الإعدادات المقيمة."""

        if self.evaluated_settings == 0:
            return 0

        return round(
            (
                self.recommended_settings
                / self.evaluated_settings
            )
            * 100
        )

    @property
    def has_limited_data(self) -> bool:
        """هل بيانات الفحص غير كافية لتقييم قوي؟"""

        if self.total_settings == 0:
            return True

        return (
            self.coverage_percentage < 75
            or self.evaluated_settings < 2
        )

    @property
    def readiness_label(self) -> str:
        """التقييم النصي مع مراعاة نقص البيانات."""

        if self.evaluated_settings == 0:
            return "Not Enough Data"

        if self.has_limited_data:
            return "Limited Data"

        percentage = (
            self.readiness_percentage
        )

        if percentage >= 90:
            return "Excellent"

        if percentage >= 70:
            return "Good"

        if percentage >= 50:
            return "Fair"

        return "Needs Attention"