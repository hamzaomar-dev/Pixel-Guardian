from core.models.cleaner_cleanup import (
    CleanerCleanInventory,
)
from core.models.result import ServiceResult
from infrastructure.logging.logger import get_logger
from infrastructure.providers.windows.cleaner_cleanup_provider import (
    WindowsCleanerCleanupProvider,
)


class CleanerCleanupService:
    """خدمة حذف أقسام Cleaner المحددة بأمان."""

    def __init__(self) -> None:
        self.logger = get_logger()
        self.cleanup_provider = (
            WindowsCleanerCleanupProvider()
        )

    def clean_categories(
        self,
        category_keys: tuple[str, ...],
    ) -> ServiceResult[CleanerCleanInventory]:
        """تنظيف الأقسام المحددة فقط."""

        self.logger.info(
            "Starting Cleaner cleanup. Categories: %s",
            category_keys,
        )

        try:
            inventory = (
                self.cleanup_provider.clean_categories(
                    category_keys
                )
            )

            self.logger.info(
                (
                    "Cleaner cleanup completed. "
                    "Deleted files: %s, bytes: %s, "
                    "skipped: %s, failed: %s"
                ),
                inventory.total_deleted_files,
                inventory.total_deleted_size_bytes,
                inventory.total_skipped_items,
                inventory.total_failed_items,
            )

            return ServiceResult.ok(
                data=inventory,
                message=(
                    "Selected Cleaner categories were processed."
                ),
                source=(
                    "Windows File System + "
                    "Windows Recycle Bin API"
                ),
            )

        except Exception as error:
            self.logger.exception(
                "Cleaner cleanup failed"
            )

            return ServiceResult.fail(
                message=str(error),
                error_code="CLEANER_CLEANUP_FAILED",
                source=(
                    "Windows File System + "
                    "Windows Recycle Bin API"
                ),
            )