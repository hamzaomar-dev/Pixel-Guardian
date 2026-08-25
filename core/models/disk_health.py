from dataclasses import dataclass

@dataclass(frozen=True , slots=True)
class DiskHealthInfo:
    """معلومات صحة واعتمادية قرص فعلي.
    """

    device_id:str
    friendly_name: str
    manufacturer: str
    model: str
    serial_number: str
    media_type: str
    bus_type: str
    firmware_version: str

    size_bytes: int | None

    health_status: str
    operational_status: tuple[str, ...]

    reliability_available: bool
    reliability_error: str

    temperature_celsius: int | None
    temperature_max_celsius: int | None

    wear_percent: int | None
    power_on_hours: int | None

    read_errors_total: int | None
    read_errors_corrected: int | None
    read_errors_uncorrected: int | None

    write_errors_total: int | None
    write_errors_corrected: int | None
    write_errors_uncorrected: int | None

    start_stop_cycle_count: int | None
    start_stop_cycle_count_max: int | None

    load_unload_cycle_count: int | None
    load_unload_cycle_count_max: int | None

    @property
    def size_gb(self) -> float | None:
        """تحويل حجم القرص إلى GB."""

        if self.size_bytes is None:
            return None

        return round(
            self.size_bytes / (1024 ** 3),
            2,
        )

    @property
    def estimated_remaining_life_percent(
        self,
    ) -> int | None:
        """
        تقدير العمر المتبقي اعتمادًا على Wear.

        قيمة Wear تُمثل نسبة الاستهلاك، وليست العمر المتبقي.
        """

        if self.wear_percent is None:
            return None

        remaining = 100 - self.wear_percent

        return max(
            0,
            min(100, remaining),
        )


@dataclass(frozen=True, slots=True)
class DiskHealthInventory:
    """جميع الأقراص المكتشفة مع بيانات الصحة."""

    disks: tuple[DiskHealthInfo, ...]