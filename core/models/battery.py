from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class BatteryInfo:
    """معلومات بطارية واحدة."""

    name: str
    description: str
    device_id: str
    status: str
    battery_status_code: int | None
    battery_status: str
    chemistry: str
    charge_percent: float | None
    power_plugged: bool | None
    estimated_runtime_minutes: int | None


@dataclass(frozen=True, slots=True)
class BatteryInventory:
    """جميع البطاريات المكتشفة في الجهاز."""

    batteries: tuple[BatteryInfo, ...]

    @property
    def has_battery(self) -> bool:
        """هل يحتوي الجهاز على بطارية؟"""

        return bool(self.batteries)