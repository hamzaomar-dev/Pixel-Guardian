from __future__ import annotations

from abc import ABC, abstractmethod

from core.models.hardware_benchmark import (
    BenchmarkLookupStatus,
    BenchmarkSource,
    DetectedHardware,
    HardwareKind,
    OnlineBenchmarkResult,
)


class OnlineBenchmarkProvider(ABC):
    """
    واجهة موحدة لأي مصدر Benchmark على الإنترنت.

    أي موقع أو API سنربطه لاحقًا يجب أن يطبق
    هذه الواجهة، حتى لا يرتبط البرنامج بموقع واحد.
    """

    @property
    @abstractmethod
    def source(
        self,
    ) -> BenchmarkSource:
        """معلومات مصدر نتائج Benchmark."""

        raise NotImplementedError

    @property
    def supported_hardware(
        self,
    ) -> tuple[HardwareKind, ...]:
        """أنواع القطع التي يدعمها المصدر."""

        return (
            HardwareKind.CPU,
            HardwareKind.GPU,
        )

    def supports(
        self,
        hardware: DetectedHardware,
    ) -> bool:
        """فحص دعم المصدر لنوع القطعة."""

        return (
            hardware.kind
            in self.supported_hardware
        )

    @abstractmethod
    def lookup(
        self,
        hardware: DetectedHardware,
    ) -> OnlineBenchmarkResult:
        """
        البحث عن نتيجة Benchmark للقطعة.

        يجب ألا ترجع الدالة أرقامًا يدوية.
        النتيجة يجب أن تأتي من المصدر الفعلي.
        """

        raise NotImplementedError

    def create_unsupported_result(
        self,
        hardware: DetectedHardware,
    ) -> OnlineBenchmarkResult:
        """إنشاء نتيجة عندما لا يدعم المصدر القطعة."""

        return OnlineBenchmarkResult(
            hardware=hardware,
            status=BenchmarkLookupStatus.NOT_FOUND,
            source=self.source,
            confidence=0.0,
            message=(
                f"{self.source.provider_name} "
                f"does not support "
                f"{hardware.kind.value} lookups."
            ),
        )

    def validate_hardware(
        self,
        hardware: DetectedHardware,
    ) -> str | None:
        """التحقق من أن بيانات القطعة صالحة للبحث."""

        if not hardware.raw_name.strip():
            return (
                "The detected hardware name is empty."
            )

        if not hardware.normalized_name.strip():
            return (
                "The normalized hardware name is empty."
            )

        if not self.supports(
            hardware
        ):
            return (
                f"Unsupported hardware type: "
                f"{hardware.kind.value}"
            )

        return None