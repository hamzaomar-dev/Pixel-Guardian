from core.models.driver import DriverInventory
from core.models.result import ServiceResult
from infrastructure.logging.logger import get_logger
from infrastructure.providers.windows.driver_provider import (
    WindowsDriverProvider,
)


class DriverService:
    """خدمة قراءة تعريفات وحالة أجهزة Windows."""

    def __init__(self) -> None:
        self.logger = get_logger()

        # يجب إنشاء Object من الـProvider باستخدام ()
        self.driver_provider = WindowsDriverProvider()

    def get_driver_inventory(
        self,
    ) -> ServiceResult[DriverInventory]:
        """قراءة تعريفات الأجهزة بأمان."""

        self.logger.info(
            "Starting driver inventory detection"
        )

        try:
            inventory = (
                self.driver_provider
                .get_driver_inventory()
            )

            self.logger.info(
                (
                    "Driver inventory detected successfully. "
                    "Total: %s, problems: %s, missing: %s"
                ),
                inventory.total_devices,
                len(inventory.problem_devices),
                len(inventory.missing_driver_devices),
            )

            return ServiceResult.ok(
                data=inventory,
                message=(
                    "Driver inventory was read successfully."
                ),
                source=(
                    "Windows PnP Signed Drivers + "
                    "Windows PnP Entities"
                ),
            )

        except Exception as error:
            self.logger.exception(
                "Failed to read driver inventory"
            )

            return ServiceResult.fail(
                message=str(error),
                error_code="DRIVER_INVENTORY_FAILED",
                source=(
                    "Windows PnP Signed Drivers + "
                    "Windows PnP Entities"
                ),
            )