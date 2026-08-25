import json
import platform
import shutil
import subprocess
from typing import Any

from core.models.driver import (
    DriverInfo,
    DriverInventory,
)


class WindowsDriverProvider:
    """قراءة تعريفات وحالة أجهزة Windows."""

    def get_driver_inventory(
        self,
    ) -> DriverInventory:
        """قراءة الأجهزة والتعريفات المثبتة."""

        if platform.system() != "Windows":
            raise RuntimeError(
                "WindowsDriverProvider supports Windows only."
            )

        raw_data = self._run_driver_query()

        devices: list[DriverInfo] = []

        for item in self._as_list(
            raw_data.get("devices")
        ):
            if not isinstance(item, dict):
                continue

            error_code = self._safe_int(
                item.get("ConfigManagerErrorCode")
            )

            if error_code is None:
                error_code = 0

            device_name = self._first_available_text(
                item.get("DeviceName"),
                item.get("Caption"),
                item.get("Description"),
            )

            devices.append(
                DriverInfo(
                    device_name=device_name,
                    device_class=self._clean_text(
                        item.get("DeviceClass")
                    ),
                    device_id=self._clean_text(
                        item.get("DeviceID")
                    ),
                    manufacturer=self._clean_text(
                        item.get("Manufacturer")
                    ),
                    driver_provider=self._clean_text(
                        item.get("DriverProviderName")
                    ),
                    driver_version=self._clean_text(
                        item.get("DriverVersion")
                    ),
                    driver_date=self._clean_text(
                        item.get("DriverDate")
                    ),
                    inf_name=self._clean_text(
                        item.get("InfName")
                    ),
                    signer=self._clean_text(
                        item.get("Signer")
                    ),
                    is_signed=self._safe_bool(
                        item.get("IsSigned")
                    ),
                    device_status=self._clean_text(
                        item.get("Status")
                    ),
                    config_manager_error_code=error_code,
                    problem_description=(
                        self._get_problem_description(
                            error_code
                        )
                    ),
                    present=self._safe_bool_with_default(
                        item.get("Present"),
                        default=True,
                    ),
                    has_driver_record=(
                        self._safe_bool_with_default(
                            item.get("HasDriverRecord"),
                            default=False,
                        )
                    ),
                )
            )

        devices.sort(
            key=lambda device: (
                0 if device.requires_attention else 1,
                device.device_class.lower(),
                device.device_name.lower(),
            )
        )

        return DriverInventory(
            devices=tuple(devices)
        )

    def _run_driver_query(
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

$signedDrivers = @(
    Get-CimInstance `
        -ClassName Win32_PnPSignedDriver `
        -ErrorAction Stop
)

$driverTable = @{}

foreach ($driver in $signedDrivers) {
    $driverDeviceId = [string]$driver.DeviceID

    if (-not [string]::IsNullOrWhiteSpace($driverDeviceId)) {
        $driverKey = $driverDeviceId.ToUpperInvariant()
        $driverTable[$driverKey] = $driver
    }
}

$devices = @(
    Get-CimInstance `
        -ClassName Win32_PnPEntity `
        -ErrorAction Stop |
    Where-Object {
        $_.Present -ne $false
    } |
    ForEach-Object {
        $device = $_
        $deviceId = [string]$device.PNPDeviceID
        $driver = $null

        if (-not [string]::IsNullOrWhiteSpace($deviceId)) {
            $deviceKey = $deviceId.ToUpperInvariant()

            if ($driverTable.ContainsKey($deviceKey)) {
                $driver = $driverTable[$deviceKey]
            }
        }

        $driverDate = $null

        if (
            $null -ne $driver -and
            $null -ne $driver.DriverDate
        ) {
            try {
                $driverDate = (
                    [datetime]$driver.DriverDate
                ).ToString("yyyy-MM-dd")
            }
            catch {
                $driverDate = [string]$driver.DriverDate
            }
        }

        $deviceName = $device.Name
        $deviceClass = $device.PNPClass
        $manufacturer = $device.Manufacturer
        $driverProviderName = $null
        $driverVersion = $null
        $infName = $null
        $signer = $null
        $isSigned = $null
        $hasDriverRecord = $false

        if ($null -ne $driver) {
            $hasDriverRecord = $true

            if (
                -not [string]::IsNullOrWhiteSpace(
                    [string]$driver.DeviceName
                )
            ) {
                $deviceName = $driver.DeviceName
            }

            if (
                -not [string]::IsNullOrWhiteSpace(
                    [string]$driver.DeviceClass
                )
            ) {
                $deviceClass = $driver.DeviceClass
            }

            if (
                -not [string]::IsNullOrWhiteSpace(
                    [string]$driver.Manufacturer
                )
            ) {
                $manufacturer = $driver.Manufacturer
            }

            $driverProviderName = $driver.DriverProviderName
            $driverVersion = $driver.DriverVersion
            $infName = $driver.InfName
            $signer = $driver.Signer
            $isSigned = $driver.IsSigned
        }

        $present = $true

        if ($null -ne $device.Present) {
            $present = [bool]$device.Present
        }

        $errorCode = 0

        if ($null -ne $device.ConfigManagerErrorCode) {
            $errorCode = [int]$device.ConfigManagerErrorCode
        }

        [PSCustomObject]@{
            DeviceName = $deviceName
            Caption = $device.Caption
            Description = $device.Description
            DeviceClass = $deviceClass
            DeviceID = $deviceId
            Manufacturer = $manufacturer
            DriverProviderName = $driverProviderName
            DriverVersion = $driverVersion
            DriverDate = $driverDate
            InfName = $infName
            Signer = $signer
            IsSigned = $isSigned
            Status = [string]$device.Status
            ConfigManagerErrorCode = $errorCode
            Present = $present
            HasDriverRecord = $hasDriverRecord
        }
    }
)

$result = [ordered]@{
    devices = $devices
}

$result | ConvertTo-Json -Depth 6 -Compress
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
            timeout=70,
            check=False,
            creationflags=creation_flags,
        )

        if completed_process.returncode != 0:
            error_message = (
                completed_process.stderr.strip()
                or "PowerShell driver query failed."
            )

            raise RuntimeError(
                error_message
            )

        output = (
            completed_process.stdout
            .lstrip("\ufeff")
            .strip()
        )

        if not output:
            raise RuntimeError(
                "Windows returned no driver data."
            )

        try:
            parsed_data = json.loads(output)

        except json.JSONDecodeError as error:
            raise RuntimeError(
                "Windows returned invalid driver data."
            ) from error

        if not isinstance(parsed_data, dict):
            raise RuntimeError(
                "Unexpected driver data format."
            )

        return parsed_data

    @staticmethod
    def _get_problem_description(
        error_code: int,
    ) -> str:
        """وصف أشهر أخطاء Device Manager."""

        descriptions = {
            0: "The device is working properly.",
            1: "The device is not configured correctly.",
            2: "Windows cannot load the driver.",
            3: (
                "The driver may be corrupted or system "
                "resources are insufficient."
            ),
            4: (
                "The device or one of its drivers is "
                "not working properly."
            ),
            10: "The device cannot start.",
            12: (
                "The device cannot find enough free "
                "resources."
            ),
            14: (
                "Windows must be restarted for the "
                "device to work."
            ),
            18: "The device drivers must be reinstalled.",
            22: "The device is disabled.",
            24: (
                "The device is not present, is not "
                "working, or does not have its drivers."
            ),
            28: (
                "The drivers for this device "
                "are not installed."
            ),
            31: (
                "Windows cannot load the drivers "
                "required for this device."
            ),
            32: (
                "The driver service is disabled or an "
                "alternative driver is being used."
            ),
            37: (
                "Windows cannot initialize the driver "
                "for this device."
            ),
            39: (
                "The driver is corrupted, missing, or "
                "cannot be loaded."
            ),
            43: (
                "Windows stopped the device because it "
                "reported a problem."
            ),
            45: (
                "The device is not currently connected."
            ),
            48: (
                "The driver was blocked because of a "
                "compatibility problem."
            ),
            52: (
                "Windows cannot verify the digital "
                "signature for the driver."
            ),
        }

        return descriptions.get(
            error_code,
            (
                "Windows reported device error code "
                f"{error_code}."
            ),
        )

    @staticmethod
    def _first_available_text(
        *values: Any,
    ) -> str:
        """إرجاع أول قيمة نصية متوفرة."""

        for value in values:
            cleaned_value = (
                WindowsDriverProvider._clean_text(
                    value,
                    default="",
                )
            )

            if cleaned_value:
                return cleaned_value

        return "Unknown Device"

    @staticmethod
    def _clean_text(
        value: Any,
        default: str = "Unavailable",
    ) -> str:
        """تنظيف النص."""

        if value is None:
            return default

        cleaned_value = " ".join(
            str(value).strip().split()
        )

        return cleaned_value or default

    @staticmethod
    def _safe_int(
        value: Any,
    ) -> int | None:
        """تحويل القيمة إلى int بأمان."""

        if value is None:
            return None

        try:
            return int(value)

        except (TypeError, ValueError):
            return None

    @staticmethod
    def _safe_bool(
        value: Any,
    ) -> bool | None:
        """تحويل القيمة إلى bool بأمان."""

        if value is None:
            return None

        if isinstance(value, bool):
            return value

        normalized_value = (
            str(value)
            .strip()
            .lower()
        )

        if normalized_value in {
            "true",
            "1",
            "yes",
        }:
            return True

        if normalized_value in {
            "false",
            "0",
            "no",
        }:
            return False

        return None

    @staticmethod
    def _safe_bool_with_default(
        value: Any,
        default: bool,
    ) -> bool:
        """تحويل القيمة إلى bool مع قيمة افتراضية."""

        converted_value = (
            WindowsDriverProvider._safe_bool(
                value
            )
        )

        if converted_value is None:
            return default

        return converted_value

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