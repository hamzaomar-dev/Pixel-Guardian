from __future__ import annotations

from core.models.online_gaming_performance import (
    GamingLookupStatus,
    GamingPerformanceRequest,
    OnlineGamingPerformanceResult,
)
from core.services.online_gaming_performance_provider import (
    OnlineGamingPerformanceProvider,
)


class OnlineGamingPerformanceService:
    """
    الخدمة الرئيسية لجلب نتائج أداء الألعاب.

    تفصل واجهة Game Lab عن الموقع أو الـAPI
    المستخدم للحصول على بيانات FPS.
    """

    def __init__(
        self,
        provider: OnlineGamingPerformanceProvider,
    ) -> None:
        self._provider = provider

    @property
    def provider_name(self) -> str:
        """اسم مصدر بيانات الأداء الحالي."""

        return self._provider.provider_name

    def lookup(
        self,
        request: GamingPerformanceRequest,
    ) -> OnlineGamingPerformanceResult:
        """فحص الطلب ثم محاولة جلب نتيجة الأداء."""

        validation_error = (
            self._provider.validate_request(
                request
            )
        )

        if validation_error:
            return self._provider.create_error_result(
                request=request,
                status=GamingLookupStatus.ERROR,
                message=validation_error,
            )

        try:
            result = self._provider.lookup(
                request
            )

        except ConnectionError:
            return self._provider.create_offline_result(
                request
            )

        except TimeoutError:
            return self._provider.create_error_result(
                request=request,
                status=GamingLookupStatus.OFFLINE,
                message=(
                    "The gaming performance service "
                    "did not respond in time."
                ),
            )

        except Exception as error:
            return self._provider.create_error_result(
                request=request,
                status=GamingLookupStatus.ERROR,
                message=(
                    "An unexpected error occurred while "
                    "retrieving gaming performance data: "
                    f"{error}"
                ),
            )

        if not isinstance(
            result,
            OnlineGamingPerformanceResult,
        ):
            return self._provider.create_error_result(
                request=request,
                status=GamingLookupStatus.ERROR,
                message=(
                    "The gaming performance provider "
                    "returned an invalid result."
                ),
            )

        return result