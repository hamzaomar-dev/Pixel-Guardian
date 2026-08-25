from core.models.cleaner import (
    CleanerScanInventory,
)
from core.models.result import ServiceResult
from infrastructure.logging.logger import get_logger
from infrastructure.providers.windows.cleaner_scan_provider import (
    WindowsCleanerScanProvider,
)


class CleanerService:
    """خدمة فحص الملفات القابلة للتنظيف."""

    def __init__(self) -> None:
        self.logger = get_logger()

        self.scan_provider = (
            WindowsCleanerScanProvider()
        )

    def scan_cleanable_files(
        self,
    ) -> ServiceResult[CleanerScanInventory]:
        """فحص الملفات دون حذفها."""

        self.logger.info(
            "Starting cleaner scan"
        )

        try:
            inventory = (
                self.scan_provider
                .get_cleaner_scan()
            )

            self.logger.info(
                (
                    "Cleaner scan completed successfully. "
                    "Categories: %s, items: %s, size: %s bytes"
                ),
                len(inventory.categories),
                inventory.total_file_count,
                inventory.total_size_bytes,
            )

            return ServiceResult.ok(
                data=inventory,
                message=(
                    "Cleaner scan completed successfully."
                ),
                source=(
                    "Windows File System + "
                    "Windows Recycle Bin API"
                ),
            )

        except Exception as error:
            self.logger.exception(
                "Cleaner scan failed"
            )

            return ServiceResult.fail(
                message=str(error),
                error_code="CLEANER_SCAN_FAILED",
                source=(
                    "Windows File System + "
                    "Windows Recycle Bin API"
                ),
            )