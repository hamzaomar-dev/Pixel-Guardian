from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class BasicSystemInfo:
    """معلومات النظام الأساسية."""

    operating_system: str
    os_version: str
    os_build: str
    architecture: str
    computer_name: str

    cpu_name: str
    physical_cores: int | None
    logical_cores: int | None

    total_memory_bytes: int
    available_memory_bytes: int

    @property
    def total_memory_gb(self) -> float:
        return round(
            self.total_memory_bytes / (1024 ** 3),
            2,
        )

    @property
    def available_memory_gb(self) -> float:
        return round(
            self.available_memory_bytes / (1024 ** 3),
            2,
        )