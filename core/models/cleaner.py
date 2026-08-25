from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class CleanerCategoryScan:
    """نتيجة فحص قسم واحد من أقسام التنظيف."""

    key: str
    title: str
    description: str

    risk_level: str
    requires_admin: bool
    selected_by_default: bool

    minimum_age_hours: int | None

    scanned_paths: tuple[str, ...]
    missing_paths: tuple[str, ...]
    unavailable_paths: tuple[str, ...]

    file_count: int
    total_size_bytes: int
    skipped_items: int

    sample_files: tuple[str, ...]
    warnings: tuple[str, ...]

    @property
    def total_size_kb(self) -> float:
        """الحجم بالكيلوبايت."""

        return round(
            self.total_size_bytes / 1024,
            2,
        )

    @property
    def total_size_mb(self) -> float:
        """الحجم بالميجابايت."""

        return round(
            self.total_size_bytes / (1024 ** 2),
            2,
        )

    @property
    def total_size_gb(self) -> float:
        """الحجم بالجيجابايت."""

        return round(
            self.total_size_bytes / (1024 ** 3),
            2,
        )

    @property
    def is_empty(self) -> bool:
        """هل القسم لا يحتوي عناصر قابلة للتنظيف؟"""

        return self.file_count == 0


@dataclass(frozen=True, slots=True)
class CleanerScanInventory:
    """نتيجة فحص جميع أقسام Cleaner."""

    scanned_at: str
    categories: tuple[CleanerCategoryScan, ...]

    @property
    def total_file_count(self) -> int:
        """إجمالي عدد العناصر المكتشفة."""

        return sum(
            category.file_count
            for category in self.categories
        )

    @property
    def total_size_bytes(self) -> int:
        """إجمالي المساحة الممكن تنظيفها."""

        return sum(
            category.total_size_bytes
            for category in self.categories
        )

    @property
    def total_size_mb(self) -> float:
        """إجمالي المساحة بالميجابايت."""

        return round(
            self.total_size_bytes / (1024 ** 2),
            2,
        )

    @property
    def total_size_gb(self) -> float:
        """إجمالي المساحة بالجيجابايت."""

        return round(
            self.total_size_bytes / (1024 ** 3),
            2,
        )

    @property
    def safe_categories(
        self,
    ) -> tuple[CleanerCategoryScan, ...]:
        """الأقسام المصنفة Safe."""

        return tuple(
            category
            for category in self.categories
            if category.risk_level == "safe"
        )

    @property
    def advanced_categories(
        self,
    ) -> tuple[CleanerCategoryScan, ...]:
        """الأقسام المصنفة Advanced."""

        return tuple(
            category
            for category in self.categories
            if category.risk_level == "advanced"
        )

    @property
    def safe_total_size_bytes(self) -> int:
        """إجمالي مساحة الأقسام الآمنة."""

        return sum(
            category.total_size_bytes
            for category in self.safe_categories
        )

    @property
    def advanced_total_size_bytes(self) -> int:
        """إجمالي مساحة الأقسام المتقدمة."""

        return sum(
            category.total_size_bytes
            for category in self.advanced_categories
        )