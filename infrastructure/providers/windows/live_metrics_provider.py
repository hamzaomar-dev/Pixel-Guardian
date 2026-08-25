import os
import platform
import threading
import time
from datetime import datetime

import psutil

from core.models.live_metrics import LiveMetrics


class WindowsLiveMetricsProvider:
    """قراءة استخدام موارد الجهاز بشكل لحظي."""

    def __init__(self) -> None:
        if platform.system() != "Windows":
            raise RuntimeError(
                "WindowsLiveMetricsProvider supports "
                "Windows only."
            )

        self._lock = threading.Lock()

        self._previous_disk_counters = (
            psutil.disk_io_counters()
        )

        self._previous_network_counters = (
            psutil.net_io_counters()
        )

        self._previous_sample_time = (
            time.monotonic()
        )

        # تجهيز عداد CPU حتى تكون القراءة التالية دقيقة.
        psutil.cpu_percent(
            interval=None,
        )

        psutil.cpu_percent(
            interval=None,
            percpu=True,
        )

    def get_live_metrics(
        self,
    ) -> LiveMetrics:
        """إرجاع لقطة جديدة لاستخدام الموارد."""

        with self._lock:
            current_time = time.monotonic()

            elapsed_seconds = max(
                current_time
                - self._previous_sample_time,
                0.001,
            )

            cpu_usage = round(
                float(
                    psutil.cpu_percent(
                        interval=None
                    )
                ),
                1,
            )

            cpu_per_core = tuple(
                round(float(value), 1)
                for value in psutil.cpu_percent(
                    interval=None,
                    percpu=True,
                )
            )

            cpu_frequency = psutil.cpu_freq()

            cpu_frequency_mhz = (
                round(
                    float(cpu_frequency.current),
                    1,
                )
                if cpu_frequency is not None
                else None
            )

            memory = psutil.virtual_memory()

            system_drive = os.environ.get(
                "SystemDrive",
                "C:",
            )

            drive_usage = self._get_drive_usage(
                system_drive
            )

            current_disk_counters = (
                psutil.disk_io_counters()
            )

            current_network_counters = (
                psutil.net_io_counters()
            )

            disk_read_rate = self._calculate_rate(
                current_value=(
                    current_disk_counters.read_bytes
                    if current_disk_counters
                    else None
                ),
                previous_value=(
                    self._previous_disk_counters.read_bytes
                    if self._previous_disk_counters
                    else None
                ),
                elapsed_seconds=elapsed_seconds,
            )

            disk_write_rate = self._calculate_rate(
                current_value=(
                    current_disk_counters.write_bytes
                    if current_disk_counters
                    else None
                ),
                previous_value=(
                    self._previous_disk_counters.write_bytes
                    if self._previous_disk_counters
                    else None
                ),
                elapsed_seconds=elapsed_seconds,
            )

            network_download_rate = (
                self._calculate_rate(
                    current_value=(
                        current_network_counters
                        .bytes_recv
                        if current_network_counters
                        else None
                    ),
                    previous_value=(
                        self._previous_network_counters
                        .bytes_recv
                        if self._previous_network_counters
                        else None
                    ),
                    elapsed_seconds=elapsed_seconds,
                )
            )

            network_upload_rate = (
                self._calculate_rate(
                    current_value=(
                        current_network_counters
                        .bytes_sent
                        if current_network_counters
                        else None
                    ),
                    previous_value=(
                        self._previous_network_counters
                        .bytes_sent
                        if self._previous_network_counters
                        else None
                    ),
                    elapsed_seconds=elapsed_seconds,
                )
            )

            self._previous_disk_counters = (
                current_disk_counters
            )

            self._previous_network_counters = (
                current_network_counters
            )

            self._previous_sample_time = (
                current_time
            )

            return LiveMetrics(
                sampled_at=datetime.now().isoformat(
                    timespec="seconds"
                ),
                cpu_usage_percent=cpu_usage,
                cpu_frequency_mhz=(
                    cpu_frequency_mhz
                ),
                cpu_per_core_percent=(
                    cpu_per_core
                ),
                memory_total_bytes=int(
                    memory.total
                ),
                memory_used_bytes=int(
                    memory.used
                ),
                memory_available_bytes=int(
                    memory.available
                ),
                memory_usage_percent=round(
                    float(memory.percent),
                    1,
                ),
                system_drive=system_drive,
                system_drive_total_bytes=(
                    drive_usage["total"]
                ),
                system_drive_used_bytes=(
                    drive_usage["used"]
                ),
                system_drive_free_bytes=(
                    drive_usage["free"]
                ),
                system_drive_usage_percent=(
                    drive_usage["percent"]
                ),
                disk_read_bytes_per_second=(
                    disk_read_rate
                ),
                disk_write_bytes_per_second=(
                    disk_write_rate
                ),
                network_download_bytes_per_second=(
                    network_download_rate
                ),
                network_upload_bytes_per_second=(
                    network_upload_rate
                ),
                process_count=len(
                    psutil.pids()
                ),
            )

    @staticmethod
    def _get_drive_usage(
        system_drive: str,
    ) -> dict[str, int | float | None]:
        """قراءة استخدام قرص النظام بأمان."""

        drive_root = (
            system_drive.rstrip("\\/")
            + "\\"
        )

        try:
            usage = psutil.disk_usage(
                drive_root
            )

            return {
                "total": int(usage.total),
                "used": int(usage.used),
                "free": int(usage.free),
                "percent": round(
                    float(usage.percent),
                    1,
                ),
            }

        except (OSError, PermissionError):
            return {
                "total": None,
                "used": None,
                "free": None,
                "percent": None,
            }

    @staticmethod
    def _calculate_rate(
        current_value: int | None,
        previous_value: int | None,
        elapsed_seconds: float,
    ) -> float:
        """حساب عدد البايتات في الثانية."""

        if (
            current_value is None
            or previous_value is None
        ):
            return 0.0

        difference = (
            current_value
            - previous_value
        )

        if difference < 0:
            return 0.0

        return round(
            difference / elapsed_seconds,
            2,
        )