from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class CleanerCategoryCleanResult:
    """نتيجة تنظيف قسم واحد."""

    key: str
    title: str

    deleted_files: int
    deleted_directories: int
    deleted_size_bytes: int

    skipped_items: int
    failed_items: int

    errors: tuple[str, ...]

    @property
    def deleted_size_mb(self) -> float:
        return round(
            self.deleted_size_bytes / (1024 ** 2),
            2,
        )

    @property
    def deleted_size_gb(self) -> float:
        return round(
            self.deleted_size_bytes / (1024 ** 3),
            2,
        )


@dataclass(frozen=True, slots=True)
class CleanerCleanInventory:
    """تقرير تنظيف الأقسام المحددة."""

    cleaned_at: str
    requested_categories: tuple[str, ...]
    categories: tuple[CleanerCategoryCleanResult, ...]

    @property
    def total_deleted_files(self) -> int:
        return sum(
            category.deleted_files
            for category in self.categories
        )

    @property
    def total_deleted_directories(self) -> int:
        return sum(
            category.deleted_directories
            for category in self.categories
        )

    @property
    def total_deleted_size_bytes(self) -> int:
        return sum(
            category.deleted_size_bytes
            for category in self.categories
        )

    @property
    def total_deleted_size_mb(self) -> float:
        return round(
            self.total_deleted_size_bytes / (1024 ** 2),
            2,
        )

    @property
    def total_deleted_size_gb(self) -> float:
        return round(
            self.total_deleted_size_bytes / (1024 ** 3),
            2,
        )

    @property
    def total_skipped_items(self) -> int:
        return sum(
            category.skipped_items
            for category in self.categories
        )

    @property
    def total_failed_items(self) -> int:
        return sum(
            category.failed_items
            for category in self.categories
        )