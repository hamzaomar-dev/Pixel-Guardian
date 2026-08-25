from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class LiveMetrics:
    """لقطة لحظية لاستخدام موارد الجهاز."""

    sampled_at: str

    cpu_usage_percent: float
    cpu_frequency_mhz: float | None
    cpu_per_core_percent: tuple[float, ...]

    memory_total_bytes: int
    memory_used_bytes: int
    memory_available_bytes: int
    memory_usage_percent: float

    system_drive: str
    system_drive_total_bytes: int | None
    system_drive_used_bytes: int | None
    system_drive_free_bytes: int | None
    system_drive_usage_percent: float | None

    disk_read_bytes_per_second: float
    disk_write_bytes_per_second: float

    network_download_bytes_per_second: float
    network_upload_bytes_per_second: float

    process_count: int

    @property
    def memory_total_gb(self) -> float:
        return round(
            self.memory_total_bytes / (1024 ** 3),
            2,
        )

    @property
    def memory_used_gb(self) -> float:
        return round(
            self.memory_used_bytes / (1024 ** 3),
            2,
        )

    @property
    def memory_available_gb(self) -> float:
        return round(
            self.memory_available_bytes / (1024 ** 3),
            2,
        )

    @property
    def system_drive_total_gb(
        self,
    ) -> float | None:
        return self._bytes_to_gb(
            self.system_drive_total_bytes
        )

    @property
    def system_drive_used_gb(
        self,
    ) -> float | None:
        return self._bytes_to_gb(
            self.system_drive_used_bytes
        )

    @property
    def system_drive_free_gb(
        self,
    ) -> float | None:
        return self._bytes_to_gb(
            self.system_drive_free_bytes
        )

    @property
    def disk_read_mb_per_second(self) -> float:
        return self._bytes_to_mb_rate(
            self.disk_read_bytes_per_second
        )

    @property
    def disk_write_mb_per_second(self) -> float:
        return self._bytes_to_mb_rate(
            self.disk_write_bytes_per_second
        )

    @property
    def network_download_mb_per_second(
        self,
    ) -> float:
        return self._bytes_to_mb_rate(
            self.network_download_bytes_per_second
        )

    @property
    def network_upload_mb_per_second(
        self,
    ) -> float:
        return self._bytes_to_mb_rate(
            self.network_upload_bytes_per_second
        )

    @staticmethod
    def _bytes_to_gb(
        value: int | None,
    ) -> float | None:
        if value is None:
            return None

        return round(
            value / (1024 ** 3),
            2,
        )

    @staticmethod
    def _bytes_to_mb_rate(
        value: float,
    ) -> float:
        return round(
            value / (1024 ** 2),
            2,
        )