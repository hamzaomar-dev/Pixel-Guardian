import json
import platform
import shutil
import subprocess
from typing import Any

import psutil

from core.models.battery import (
    BatteryInfo,
    BatteryInventory,
)


class WindowsBatteryProvider:
    """قراءة معلومات البطارية من Windows."""

    def get_battery_inventory(
        self,
    ) -> BatteryInventory:
        """قراءة جميع البطاريات المتوفرة."""

        if platform.system() != "Windows":
            raise RuntimeError(
                "WindowsBatteryProvider supports "
                "Windows only."
            )

        raw_data = self._run_battery_query()

        system_battery = psutil.sensors_battery()

        batteries: list[BatteryInfo] = []

        raw_batteries = self._as_list(
            raw_data.get("batteries")
        )

        for index, item in enumerate(
            raw_batteries
        ):
            if not isinstance(item, dict):
                continue

            status_code = self._safe_int(
                item.get("BatteryStatus")
            )

            charge_percent = (
                self._normalize_percent(
                    item.get(
                        "EstimatedChargeRemaining"
                    )
                )
            )

            runtime_minutes = (
                self._normalize_runtime_minutes(
                    item.get("EstimatedRunTime")
                )
            )

            power_plugged: bool | None = None

            # psutil يعرض حالة الطاقة العامة للجهاز.
            # نستخدمه مع البطارية الأولى.
            if (
                index == 0
                and system_battery is not None
            ):
                power_plugged = bool(
                    system_battery.power_plugged
                )

                if charge_percent is None:
                    charge_percent = (
                        self._normalize_percent(
                            system_battery.percent
                        )
                    )

                if runtime_minutes is None:
                    runtime_minutes = (
                        self._get_psutil_runtime_minutes(
                            system_battery
                        )
                    )

            if power_plugged is None:
                power_plugged = (
                    self._infer_power_plugged(
                        status_code
                    )
                )

            batteries.append(
                BatteryInfo(
                    name=self._clean_text(
                        item.get("Name"),
                        default="System Battery",
                    ),
                    description=self._clean_text(
                        item.get("Description")
                    ),
                    device_id=self._clean_text(
                        item.get("DeviceID")
                    ),
                    status=self._clean_text(
                        item.get("Status")
                    ),
                    battery_status_code=status_code,
                    battery_status=(
                        self._battery_status_text(
                            status_code
                        )
                    ),
                    chemistry=(
                        self._chemistry_text(
                            self._safe_int(
                                item.get("Chemistry")
                            )
                        )
                    ),
                    charge_percent=charge_percent,
                    power_plugged=power_plugged,
                    estimated_runtime_minutes=(
                        runtime_minutes
                    ),
                )
            )

        # بعض الأجهزة تعرض البطارية من psutil
        # ولكن لا تعرضها من Win32_Battery.
        if (
            not batteries
            and system_battery is not None
        ):
            batteries.append(
                BatteryInfo(
                    name="System Battery",
                    description=(
                        "Battery detected by "
                        "Windows power management"
                    ),
                    device_id="Unavailable",
                    status="OK",
                    battery_status_code=None,
                    battery_status=(
                        self._get_psutil_status_text(
                            system_battery
                        )
                    ),
                    chemistry="Unavailable",
                    charge_percent=(
                        self._normalize_percent(
                            system_battery.percent
                        )
                    ),
                    power_plugged=bool(
                        system_battery.power_plugged
                    ),
                    estimated_runtime_minutes=(
                        self._get_psutil_runtime_minutes(
                            system_battery
                        )
                    ),
                )
            )

        return BatteryInventory(
            batteries=tuple(batteries)
        )

    def _run_battery_query(
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

$batteries = @(
    Get-CimInstance `
        -ClassName Win32_Battery `
        -ErrorAction Stop |
    Select-Object `
        Name,
        Description,
        DeviceID,
        Status,
        BatteryStatus,
        Chemistry,
        EstimatedChargeRemaining,
        EstimatedRunTime
)

$result = [ordered]@{
    batteries = $batteries
}

$result | ConvertTo-Json -Depth 5 -Compress
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
            timeout=30,
            check=False,
            creationflags=creation_flags,
        )

        if completed_process.returncode != 0:
            error_message = (
                completed_process.stderr.strip()
                or "PowerShell battery query failed."
            )

            raise RuntimeError(error_message)

        output = (
            completed_process.stdout
            .lstrip("\ufeff")
            .strip()
        )

        if not output:
            raise RuntimeError(
                "Windows returned no battery data."
            )

        try:
            parsed_data = json.loads(output)

        except json.JSONDecodeError as error:
            raise RuntimeError(
                "Windows returned invalid battery data."
            ) from error

        if not isinstance(parsed_data, dict):
            raise RuntimeError(
                "Unexpected battery data format."
            )

        return parsed_data

    @staticmethod
    def _battery_status_text(
        status_code: int | None,
    ) -> str:
        """تحويل كود حالة البطارية إلى نص."""

        statuses = {
            1: "Other",
            2: "Unknown",
            3: "Fully Charged",
            4: "Low",
            5: "Critical",
            6: "Charging",
            7: "Charging and High",
            8: "Charging and Low",
            9: "Charging and Critical",
            10: "Undefined",
            11: "Partially Charged",
        }

        if status_code is None:
            return "Unavailable"

        return statuses.get(
            status_code,
            f"Unknown Status ({status_code})",
        )

    @staticmethod
    def _chemistry_text(
        chemistry_code: int | None,
    ) -> str:
        """تحويل كود نوع البطارية إلى نص."""

        chemistries = {
            1: "Other",
            2: "Unknown",
            3: "Lead Acid",
            4: "Nickel Cadmium",
            5: "Nickel Metal Hydride",
            6: "Lithium-ion",
            7: "Zinc Air",
            8: "Lithium Polymer",
        }

        if chemistry_code is None:
            return "Unavailable"

        return chemistries.get(
            chemistry_code,
            f"Unknown Chemistry ({chemistry_code})",
        )

    @staticmethod
    def _infer_power_plugged(
        status_code: int | None,
    ) -> bool | None:
        """استنتاج حالة الشاحن من حالة البطارية."""

        charging_statuses = {
            6,
            7,
            8,
            9,
        }

        if status_code in charging_statuses:
            return True

        if status_code in {
            4,
            5,
        }:
            return False

        return None

    @staticmethod
    def _get_psutil_status_text(
        battery,
    ) -> str:
        """إنشاء حالة البطارية من psutil."""

        if battery.power_plugged:
            if battery.percent >= 99:
                return "Fully Charged"

            return "Charging or Plugged In"

        if battery.percent <= 10:
            return "Critical"

        if battery.percent <= 25:
            return "Low"

        return "Discharging"

    @staticmethod
    def _get_psutil_runtime_minutes(
        battery,
    ) -> int | None:
        """تحويل الوقت المتبقي من ثوانٍ إلى دقائق."""

        seconds_left = battery.secsleft

        invalid_values = {
            psutil.POWER_TIME_UNKNOWN,
            psutil.POWER_TIME_UNLIMITED,
        }

        if seconds_left in invalid_values:
            return None

        if seconds_left is None:
            return None

        try:
            seconds_value = int(seconds_left)

        except (TypeError, ValueError):
            return None

        if seconds_value <= 0:
            return None

        return round(
            seconds_value / 60
        )

    @staticmethod
    def _normalize_runtime_minutes(
        value: Any,
    ) -> int | None:
        """تنظيف وقت التشغيل المتبقي."""

        runtime = WindowsBatteryProvider._safe_int(
            value
        )

        if runtime is None:
            return None

        # Windows قد يعيد قيمة ضخمة
        # عندما يكون الوقت غير معروف.
        if runtime <= 0 or runtime >= 71582788:
            return None

        return runtime

    @staticmethod
    def _normalize_percent(
        value: Any,
    ) -> float | None:
        """تنظيف نسبة شحن البطارية."""

        if value is None:
            return None

        try:
            percent = float(value)

        except (TypeError, ValueError):
            return None

        if percent < 0 or percent > 100:
            return None

        return round(
            percent,
            1,
        )

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