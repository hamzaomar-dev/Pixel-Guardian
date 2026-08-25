from dataclasses import dataclass


@dataclass(frozen=True, slots=True)

class LogicalVolumeInfo:
    """معلومات Volume مثل C: أو D:."""

    device_id: str
    volume_name: str
    file_system: str
    size_bytes: int | None
    free_bytes: int | None

    @property
    def size_gb(self) -> float | None:
        if self.size_bytes is None:
            return None

        return round(
            self.size_bytes / (1024 ** 3),
            2,
        )

    @property
    def free_gb(self) -> float | None:
        if self.free_bytes is None:
            return None

        return round(
            self.free_bytes / (1024 ** 3),
            2,
        )

    @property
    def used_gb(self) -> float | None:
        if (
            self.size_bytes is None
            or self.free_bytes is None
        ):
            return None

        used_bytes = (
            self.size_bytes - self.free_bytes
        )

        return round(
            used_bytes / (1024 ** 3),
            2,
        )


@dataclass(frozen=True, slots=True)
class PartitionInfo:
    """معلومات قسم موجود على قرص فعلي."""

    name: str
    device_id: str
    partition_type: str
    size_bytes: int | None
    boot_partition: bool
    primary_partition: bool
    volumes: tuple[LogicalVolumeInfo, ...]

    @property
    def size_gb(self) -> float | None:
        if self.size_bytes is None:
            return None

        return round(
            self.size_bytes / (1024 ** 3),
            2,
        )


@dataclass(frozen=True, slots=True)
class StorageDeviceInfo:
    """معلومات قرص تخزين فعلي."""

    index: int | None
    device_id: str
    model: str
    manufacturer: str
    serial_number: str
    interface_type: str
    bus_type: str
    media_type: str
    storage_type: str
    size_bytes: int | None
    status: str
    pnp_device_id: str
    partitions: tuple[PartitionInfo, ...]

    @property
    def size_gb(self) -> float | None:
        if self.size_bytes is None:
            return None

        return round(
            self.size_bytes / (1024 ** 3),
            2,
        )


@dataclass(frozen=True, slots=True)
class StorageInventory:
    """جميع أقراص التخزين المكتشفة."""

    devices: tuple[StorageDeviceInfo, ...]