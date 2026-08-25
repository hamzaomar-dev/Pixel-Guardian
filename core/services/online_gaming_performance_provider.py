from __future__ import annotations

from abc import ABC, abstractmethod

from core.models.online_gaming_performance import (
    GamingLookupStatus,
    GamingPerformanceRequest,
    OnlineGamingPerformanceResult,
)


class OnlineGamingPerformanceProvider(ABC):
    """
    واجهة موحدة لأي موقع يعطينا نتائج FPS.

    لاحقًا ممكن نربط HowManyFPS أو أي مصدر آخر
    بدون تغيير Game Lab أو منطق البرنامج.
    """

    @property
    @abstractmethod
    def provider_id(self) -> str:
        """معرف داخلي ثابت للمصدر."""

        raise NotImplementedError

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """اسم المصدر الذي سيظهر للمستخدم."""

        raise NotImplementedError

    @abstractmethod
    def lookup(
        self,
        request: GamingPerformanceRequest,
    ) -> OnlineGamingPerformanceResult:
        """إرسال الطلب للمصدر وإرجاع نتيجة FPS."""

        raise NotImplementedError

    def validate_request(
        self,
        request: GamingPerformanceRequest,
    ) -> str | None:
        """فحص الطلب قبل إرساله للإنترنت."""

        if not request.cpu_query_name:
            return "Processor name is unavailable."

        if not request.gpu_query_name:
            return "Graphics card name is unavailable."

        if not request.game.strip():
            return "Game name is empty."

        return None

    def create_error_result(
        self,
        request: GamingPerformanceRequest,
        status: GamingLookupStatus,
        message: str,
    ) -> OnlineGamingPerformanceResult:
        """إنشاء نتيجة خطأ موحدة."""

        return OnlineGamingPerformanceResult(
            request=request,
            status=status,
            provider_id=self.provider_id,
            provider_name=self.provider_name,
            message=message,
        )

    def create_offline_result(
        self,
        request: GamingPerformanceRequest,
    ) -> OnlineGamingPerformanceResult:
        """إنشاء نتيجة عند عدم توفر الإنترنت."""

        return self.create_error_result(
            request=request,
            status=GamingLookupStatus.OFFLINE,
            message=(
                "An internet connection is required "
                "to retrieve gaming performance data."
            ),
        )