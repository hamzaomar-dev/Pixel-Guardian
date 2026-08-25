from core.models.basic_system_info import BasicSystemInfo
from core.models.battery import BatteryInventory
from core.models.disk_health import DiskHealthInventory
from core.models.hardware_identity import HardwareIdentity
from core.models.network import NetworkInventory
from core.models.result import ServiceResult
from core.models.storage import StorageInventory

from infrastructure.logging.logger import get_logger
from infrastructure.providers.windows.basic_system_provider import (
    WindowsBasicSystemProvider,
)
from infrastructure.providers.windows.battery_provider import (
    WindowsBatteryProvider,
)
from infrastructure.providers.windows.disk_health_provider import (
    WindowsDiskHealthProvider,
)
from infrastructure.providers.windows.hardware_identity_provider import (
    WindowsHardwareIdentityProvider,
)
from infrastructure.providers.windows.network_provider import (
    WindowsNetworkProvider,
)
from infrastructure.providers.windows.storage_provider import (
    WindowsStorageProvider,
)


class InventoryService:
    """خدمة قراءة معلومات ومكونات الجهاز."""

    def __init__(self) -> None:
        self.logger = get_logger()

        self.basic_system_provider = (
            WindowsBasicSystemProvider()
        )

        self.identity_provider = (
            WindowsHardwareIdentityProvider()
        )

        self.storage_provider = (
            WindowsStorageProvider()
        )

        self.network_provider = (
            WindowsNetworkProvider()
        )

        self.battery_provider = (
            WindowsBatteryProvider()
        )

        self.disk_health_provider = (
            WindowsDiskHealthProvider()
        )

    def get_basic_system_info(
        self,
    ) -> ServiceResult[BasicSystemInfo]:
        """قراءة النظام والمعالج والرام بأمان."""

        self.logger.info(
            "Starting basic system information detection"
        )

        try:
            system_info = (
                self.basic_system_provider
                .get_basic_system_info()
            )

            self.logger.info(
                "Basic system information "
                "detected successfully"
            )

            return ServiceResult.ok(
                data=system_info,
                message=(
                    "Basic system information was read "
                    "successfully."
                ),
                source="Windows Registry + psutil",
            )

        except Exception as error:
            self.logger.exception(
                "Failed to read basic system information"
            )

            return ServiceResult.fail(
                message=str(error),
                error_code="BASIC_SYSTEM_INFO_FAILED",
                source="Windows Registry + psutil",
            )

    def get_hardware_identity(
        self,
    ) -> ServiceResult[HardwareIdentity]:
        """قراءة كرت الشاشة واللوحة والـBIOS."""

        self.logger.info(
            "Starting hardware identity detection"
        )

        try:
            hardware_identity = (
                self.identity_provider
                .get_hardware_identity()
            )

            self.logger.info(
                (
                    "Hardware identity detected successfully. "
                    "GPU count: %s, motherboard count: %s"
                ),
                len(hardware_identity.gpus),
                len(hardware_identity.motherboards),
            )

            return ServiceResult.ok(
                data=hardware_identity,
                message=(
                    "Hardware identity was read "
                    "successfully."
                ),
                source="Windows CIM",
            )

        except Exception as error:
            self.logger.exception(
                "Failed to read hardware identity"
            )

            return ServiceResult.fail(
                message=str(error),
                error_code="HARDWARE_IDENTITY_FAILED",
                source="Windows CIM",
            )

    def get_storage_inventory(
        self,
    ) -> ServiceResult[StorageInventory]:
        """قراءة الأقراص والأقسام بأمان."""

        self.logger.info(
            "Starting storage inventory detection"
        )

        try:
            storage_inventory = (
                self.storage_provider
                .get_storage_inventory()
            )

            self.logger.info(
                (
                    "Storage inventory detected "
                    "successfully. Device count: %s"
                ),
                len(storage_inventory.devices),
            )

            return ServiceResult.ok(
                data=storage_inventory,
                message=(
                    "Storage inventory was read "
                    "successfully."
                ),
                source=(
                    "Windows CIM + "
                    "Windows Storage Management"
                ),
            )

        except Exception as error:
            self.logger.exception(
                "Failed to read storage inventory"
            )

            return ServiceResult.fail(
                message=str(error),
                error_code="STORAGE_INVENTORY_FAILED",
                source=(
                    "Windows CIM + "
                    "Windows Storage Management"
                ),
            )

    def get_network_inventory(
        self,
    ) -> ServiceResult[NetworkInventory]:
        """قراءة كروت الشبكة بأمان."""

        self.logger.info(
            "Starting network inventory detection"
        )

        try:
            network_inventory = (
                self.network_provider
                .get_network_inventory()
            )

            self.logger.info(
                (
                    "Network inventory detected "
                    "successfully. Adapter count: %s"
                ),
                len(network_inventory.adapters),
            )

            return ServiceResult.ok(
                data=network_inventory,
                message=(
                    "Network inventory was read "
                    "successfully."
                ),
                source="Windows Network Management",
            )

        except Exception as error:
            self.logger.exception(
                "Failed to read network inventory"
            )

            return ServiceResult.fail(
                message=str(error),
                error_code="NETWORK_INVENTORY_FAILED",
                source="Windows Network Management",
            )

    def get_battery_inventory(
        self,
    ) -> ServiceResult[BatteryInventory]:
        """قراءة معلومات البطارية بأمان."""

        self.logger.info(
            "Starting battery inventory detection"
        )

        try:
            battery_inventory = (
                self.battery_provider
                .get_battery_inventory()
            )

            self.logger.info(
                (
                    "Battery inventory detected "
                    "successfully. Battery count: %s"
                ),
                len(battery_inventory.batteries),
            )

            return ServiceResult.ok(
                data=battery_inventory,
                message=(
                    "Battery inventory was read "
                    "successfully."
                ),
                source="Windows CIM + psutil",
            )

        except Exception as error:
            self.logger.exception(
                "Failed to read battery inventory"
            )

            return ServiceResult.fail(
                message=str(error),
                error_code="BATTERY_INVENTORY_FAILED",
                source="Windows CIM + psutil",
            )

    def get_disk_health_inventory(
        self,
    ) -> ServiceResult[DiskHealthInventory]:
        """قراءة صحة واعتمادية الأقراص بأمان."""

        self.logger.info(
            "Starting disk health inventory detection"
        )

        try:
            disk_health_inventory = (
                self.disk_health_provider
                .get_disk_health_inventory()
            )

            self.logger.info(
                (
                    "Disk health inventory detected "
                    "successfully. Disk count: %s"
                ),
                len(disk_health_inventory.disks),
            )

            return ServiceResult.ok(
                data=disk_health_inventory,
                message=(
                    "Disk health inventory was read "
                    "successfully."
                ),
                source=(
                    "Windows Physical Disk + "
                    "Storage Reliability Counters"
                ),
            )

        except Exception as error:
            self.logger.exception(
                "Failed to read disk health inventory"
            )

            return ServiceResult.fail(
                message=str(error),
                error_code="DISK_HEALTH_INVENTORY_FAILED",
                source=(
                    "Windows Physical Disk + "
                    "Storage Reliability Counters"
                ),
            )