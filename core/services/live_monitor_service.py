from core.models.live_metrics import LiveMetrics
from core.models.result import ServiceResult
from infrastructure.logging.logger import get_logger
from infrastructure.providers.windows.live_metrics_provider import (
    WindowsLiveMetricsProvider,
)


class LiveMonitorService:
    """خدمة قراءة القياسات اللحظية للجهاز."""

    def __init__(self) -> None:
        self.logger = get_logger()

        self.metrics_provider = (
            WindowsLiveMetricsProvider()
        )

    def get_live_metrics(
        self,
    ) -> ServiceResult[LiveMetrics]:
        """قراءة لقطة لحظية للموارد بأمان."""

        try:
            metrics = (
                self.metrics_provider
                .get_live_metrics()
            )

            return ServiceResult.ok(
                data=metrics,
                message=(
                    "Live system metrics were read "
                    "successfully."
                ),
                source="psutil",
            )

        except Exception as error:
            self.logger.exception(
                "Failed to read live system metrics"
            )

            return ServiceResult.fail(
                message=str(error),
                error_code="LIVE_METRICS_FAILED",
                source="psutil",
            )