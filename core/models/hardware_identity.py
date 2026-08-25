from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class GpuInfo:
    """معلومات كرت الشاشة الأساسية."""

    name: str
    manufacturer: str
    video_processor: str
    driver_version: str
    pnp_device_id: str
    status: str


@dataclass(frozen=True, slots=True)
class MotherboardInfo:
    """معلومات اللوحة الأم."""

    manufacturer: str
    product: str
    version: str
    serial_number: str


@dataclass(frozen=True, slots=True)
class BiosInfo:
    """معلومات BIOS."""

    manufacturer: str
    version: str
    release_date: str
    serial_number: str


@dataclass(frozen=True, slots=True)
class HardwareIdentity:
    """معلومات تعريف مكونات الجهاز."""

    gpus: tuple[GpuInfo, ...]
    motherboards: tuple[MotherboardInfo, ...]
    bios: BiosInfo | None