from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class DriverInfo:
    """معلومات تعريف جهاز واحد في Windows."""

    device_name: str
    device_class: str
    device_id: str

    manufacturer: str
    driver_provider: str
    driver_version: str
    driver_date: str

    inf_name: str
    signer: str
    is_signed: bool | None

    device_status: str
    config_manager_error_code: int
    problem_description: str

    present: bool
    has_driver_record: bool

    @property
    def is_working_correctly(self) -> bool:
        """هل الجهاز يعمل دون خطأ من Device Manager؟"""

        return self.config_manager_error_code == 0

    @property
    def is_missing_driver(self) -> bool:
        """الخطأ 28 يعني أن تعريف الجهاز غير مثبت."""

        return self.config_manager_error_code == 28

    @property
    def requires_attention(self) -> bool:
        """هل يحتاج الجهاز إلى مراجعة؟"""

        return (
            self.config_manager_error_code != 0
            or self.is_signed is False
        )


@dataclass(frozen=True, slots=True)
class DriverInventory:
    """قائمة تعريفات وأجهزة Windows."""

    devices: tuple[DriverInfo, ...]

    @property
    def total_devices(self) -> int:
        return len(self.devices)

    @property
    def problem_devices(self) -> tuple[DriverInfo, ...]:
        return tuple(
            device
            for device in self.devices
            if device.requires_attention
        )

    @property
    def missing_driver_devices(
        self,
    ) -> tuple[DriverInfo, ...]:
        return tuple(
            device
            for device in self.devices
            if device.is_missing_driver
        )

    @property
    def unsigned_driver_devices(
        self,
    ) -> tuple[DriverInfo, ...]:
        return tuple(
            device
            for device in self.devices
            if device.is_signed is False
        )

    @property
    def working_devices(self) -> tuple[DriverInfo, ...]:
        return tuple(
            device
            for device in self.devices
            if device.is_working_correctly
            and device.is_signed is not False
        )