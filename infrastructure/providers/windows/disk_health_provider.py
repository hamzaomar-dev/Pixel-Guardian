import json
import platform
import shutil
import subprocess
from typing import Any

from core.models.disk_health import (
    DiskHealthInfo,
    DiskHealthInventory,
)


class WindowsDiskHealthProvider:
    """قراءة صحة واعتمادية الأقراص من Windows."""

    def get_disk_health_inventory(
        self,
    ) -> DiskHealthInventory:
        """قراءة حالة جميع الأقراص الفعلية."""

        if platform.system() != "Windows":
            raise RuntimeError(
                "WindowsDiskHealthProvider supports "
                "Windows only."
            )

        raw_data = self._run_disk_health_query()

        disks: list[DiskHealthInfo] = []

        for item in self._as_list(
            raw_data.get("disks")
        ):
            if not isinstance(item, dict):
                continue

            friendly_name = self._clean_text(
                item.get("FriendlyName")
            )

            model = self._clean_text(
                item.get("Model")
            )

            if friendly_name == "Unavailable":
                friendly_name = model

            disks.append(
                DiskHealthInfo(
                    device_id=self._clean_text(
                        item.get("DeviceId")
                    ),
                    friendly_name=friendly_name,
                    manufacturer=self._clean_text(
                        item.get("Manufacturer")
                    ),
                    model=model,
                    serial_number=self._normalize_serial(
                        item.get("SerialNumber")
                    ),
                    media_type=self._clean_text(
                        item.get("MediaType")
                    ),
                    bus_type=self._clean_text(
                        item.get("BusType")
                    ),
                    firmware_version=self._clean_text(
                        item.get("FirmwareVersion")
                    ),
                    size_bytes=self._safe_int(
                        item.get("Size")
                    ),
                    health_status=self._clean_text(
                        item.get("HealthStatus")
                    ),
                    operational_status=(
                        self._parse_text_tuple(
                            item.get(
                                "OperationalStatus"
                            )
                        )
                    ),
                    reliability_available=bool(
                        item.get(
                            "ReliabilityAvailable",
                            False,
                        )
                    ),
                    reliability_error=self._clean_text(
                        item.get("ReliabilityError"),
                        default="",
                    ),
                    temperature_celsius=(
                        self._normalize_temperature(
                            item.get("Temperature")
                        )
                    ),
                    temperature_max_celsius=(
                        self._normalize_temperature(
                            item.get("TemperatureMax")
                        )
                    ),
                    wear_percent=(
                        self._normalize_percentage(
                            item.get("Wear")
                        )
                    ),
                    power_on_hours=(
                        self._normalize_counter(
                            item.get("PowerOnHours")
                        )
                    ),
                    read_errors_total=(
                        self._normalize_counter(
                            item.get(
                                "ReadErrorsTotal"
                            )
                        )
                    ),
                    read_errors_corrected=(
                        self._normalize_counter(
                            item.get(
                                "ReadErrorsCorrected"
                            )
                        )
                    ),
                    read_errors_uncorrected=(
                        self._normalize_counter(
                            item.get(
                                "ReadErrorsUncorrected"
                            )
                        )
                    ),
                    write_errors_total=(
                        self._normalize_counter(
                            item.get(
                                "WriteErrorsTotal"
                            )
                        )
                    ),
                    write_errors_corrected=(
                        self._normalize_counter(
                            item.get(
                                "WriteErrorsCorrected"
                            )
                        )
                    ),
                    write_errors_uncorrected=(
                        self._normalize_counter(
                            item.get(
                                "WriteErrorsUncorrected"
                            )
                        )
                    ),
                    start_stop_cycle_count=(
                        self._normalize_counter(
                            item.get(
                                "StartStopCycleCount"
                            )
                        )
                    ),
                    start_stop_cycle_count_max=(
                        self._normalize_counter(
                            item.get(
                                "StartStopCycleCountMax"
                            )
                        )
                    ),
                    load_unload_cycle_count=(
                        self._normalize_counter(
                            item.get(
                                "LoadUnloadCycleCount"
                            )
                        )
                    ),
                    load_unload_cycle_count_max=(
                        self._normalize_counter(
                            item.get(
                                "LoadUnloadCycleCountMax"
                            )
                        )
                    ),
                )
            )

        disks.sort(
            key=lambda disk: (
                self._device_sort_value(
                    disk.device_id
                ),
                disk.friendly_name.lower(),
            )
        )

        return DiskHealthInventory(
            disks=tuple(disks)
        )

    def _run_disk_health_query(
        self,
    ) -> dict[str, Any]:
        """تشغيل استعلام PowerShell وإرجاع JSON."""

        powershell_path = (
            shutil.which("powershell.exe")
            or shutil.which("pwsh.exe")
        )

        if powershell_path is None:
            raise RuntimeError(
                "PowerShell could not be found."
            )

        script = r"""
$ErrorActionPreference = "Stop"
$ProgressPreference = "SilentlyContinue"
$WarningPreference = "SilentlyContinue"

[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new($false)

$disks = @(
    Get-PhysicalDisk -ErrorAction Stop |
    Sort-Object DeviceId |
    ForEach-Object {
        $disk = $_
        $counter = $null
        $counterError = $null

        try {
            $counter = Get-StorageReliabilityCounter `
                -PhysicalDisk $disk `
                -ErrorAction Stop
        }
        catch {
            $counterError = $_.Exception.Message
            $counter = $null
        }

        $operationalStatus = @(
            $disk.OperationalStatus |
            ForEach-Object {
                [string]$_
            }
        )

        [PSCustomObject]@{
            DeviceId = [string]$disk.DeviceId
            FriendlyName = $disk.FriendlyName
            Manufacturer = $disk.Manufacturer
            Model = $disk.Model
            SerialNumber = $disk.SerialNumber
            MediaType = [string]$disk.MediaType
            BusType = [string]$disk.BusType
            FirmwareVersion = $disk.FirmwareVersion
            Size = $disk.Size

            HealthStatus = [string]$disk.HealthStatus
            OperationalStatus = $operationalStatus

            ReliabilityAvailable = ($null -ne $counter)
            ReliabilityError = $counterError

            Temperature = if ($null -ne $counter) {
                $counter.Temperature
            }
            else {
                $null
            }

            TemperatureMax = if ($null -ne $counter) {
                $counter.TemperatureMax
            }
            else {
                $null
            }

            Wear = if ($null -ne $counter) {
                $counter.Wear
            }
            else {
                $null
            }

            PowerOnHours = if ($null -ne $counter) {
                $counter.PowerOnHours
            }
            else {
                $null
            }

            ReadErrorsTotal = if ($null -ne $counter) {
                $counter.ReadErrorsTotal
            }
            else {
                $null
            }

            ReadErrorsCorrected = if ($null -ne $counter) {
                $counter.ReadErrorsCorrected
            }
            else {
                $null
            }

            ReadErrorsUncorrected = if ($null -ne $counter) {
                $counter.ReadErrorsUncorrected
            }
            else {
                $null
            }

            WriteErrorsTotal = if ($null -ne $counter) {
                $counter.WriteErrorsTotal
            }
            else {
                $null
            }

            WriteErrorsCorrected = if ($null -ne $counter) {
                $counter.WriteErrorsCorrected
            }
            else {
                $null
            }

            WriteErrorsUncorrected = if ($null -ne $counter) {
                $counter.WriteErrorsUncorrected
            }
            else {
                $null
            }

            StartStopCycleCount = if ($null -ne $counter) {
                $counter.StartStopCycleCount
            }
            else {
                $null
            }

            StartStopCycleCountMax = if ($null -ne $counter) {
                $counter.StartStopCycleCountMax
            }
            else {
                $null
            }

            LoadUnloadCycleCount = if ($null -ne $counter) {
                $counter.LoadUnloadCycleCount
            }
            else {
                $null
            }

            LoadUnloadCycleCountMax = if ($null -ne $counter) {
                $counter.LoadUnloadCycleCountMax
            }
            else {
                $null
            }
        }
    }
)

$result = [ordered]@{
    disks = $disks
}

$result | ConvertTo-Json -Depth 7 -Compress
"""

        creation_flags = getattr(
            subprocess,
            "CREATE_NO_WINDOW",
            0,
        )

        completed_process = subprocess.run(
            [
                powershell_path,
                "-NoLogo",
                "-NoProfile",
                "-NonInteractive",
                "-ExecutionPolicy",
                "Bypass",
                "-Command",
                script,
            ],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=40,
            check=False,
            creationflags=creation_flags,
        )

        if completed_process.returncode != 0:
            error_message = (
                completed_process.stderr.strip()
                or "PowerShell disk health query failed."
            )

            raise RuntimeError(error_message)

        output = (
            completed_process.stdout
            .lstrip("\ufeff")
            .strip()
        )

        if not output:
            raise RuntimeError(
                "Windows returned no disk health data."
            )

        try:
            parsed_data = json.loads(output)

        except json.JSONDecodeError as error:
            raise RuntimeError(
                "Windows returned invalid disk health data."
            ) from error

        if not isinstance(parsed_data, dict):
            raise RuntimeError(
                "Unexpected disk health data format."
            )

        return parsed_data

    @staticmethod
    def _normalize_temperature(
        value: Any,
    ) -> int | None:
        """تنظيف درجة حرارة القرص."""

        temperature = (
            WindowsDiskHealthProvider._safe_int(
                value
            )
        )

        if temperature is None:
            return None

        if temperature <= 0 or temperature > 150:
            return None

        return temperature

    @staticmethod
    def _normalize_percentage(
        value: Any,
    ) -> int | None:
        """تنظيف قيمة مئوية."""

        percentage = (
            WindowsDiskHealthProvider._safe_int(
                value
            )
        )

        if percentage is None:
            return None

        if percentage < 0 or percentage > 100:
            return None

        return percentage

    @staticmethod
    def _normalize_counter(
        value: Any,
    ) -> int | None:
        """تنظيف عداد لا يقبل القيم السالبة."""

        counter = (
            WindowsDiskHealthProvider._safe_int(
                value
            )
        )

        if counter is None or counter < 0:
            return None

        return counter

    @staticmethod
    def _parse_text_tuple(
        value: Any,
    ) -> tuple[str, ...]:
        """تحويل قائمة النصوص إلى tuple."""

        values: list[str] = []

        for item in WindowsDiskHealthProvider._as_list(
            value
        ):
            if item is None:
                continue

            cleaned_item = " ".join(
                str(item).strip().split()
            )

            if cleaned_item:
                values.append(cleaned_item)

        return tuple(
            dict.fromkeys(values)
        )

    @staticmethod
    def _normalize_serial(
        value: Any,
    ) -> str:
        """تنظيف Serial Number غير المتاح."""

        if value is None:
            return "Unavailable"

        cleaned_value = " ".join(
            str(value).strip().split()
        )

        invalid_values = {
            "",
            "none",
            "unknown",
            "default string",
            "to be filled by o.e.m.",
            "system serial number",
            "unavailable",
        }

        if cleaned_value.lower() in invalid_values:
            return "Unavailable"

        return cleaned_value

    @staticmethod
    def _device_sort_value(
        device_id: str,
    ) -> int:
        """تحويل DeviceId إلى قيمة تستخدم للترتيب."""

        try:
            return int(device_id)

        except (TypeError, ValueError):
            return 9999

    @staticmethod
    def _safe_int(
        value: Any,
    ) -> int | None:
        """تحويل القيمة إلى رقم بأمان."""

        if value is None:
            return None

        try:
            return int(value)

        except (TypeError, ValueError):
            return None

    @staticmethod
    def _as_list(
        value: Any,
    ) -> list[Any]:
        """تحويل القيمة إلى قائمة."""

        if value is None:
            return []

        if isinstance(value, list):
            return value

        return [value]

    @staticmethod
    def _clean_text(
        value: Any,
        default: str = "Unavailable",
    ) -> str:
        """تنظيف قيمة نصية."""

        if value is None:
            return default

        cleaned_value = " ".join(
            str(value).strip().split()
        )

        return cleaned_value or default