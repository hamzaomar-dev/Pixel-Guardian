import json
import platform
import shutil
import subprocess
from typing import Any

from core.models.hardware_identity import (
    BiosInfo,
    GpuInfo,
    HardwareIdentity,
    MotherboardInfo,
)


class WindowsHardwareIdentityProvider:
    """قراءة GPU واللوحة الأم وBIOS من Windows."""

    def get_hardware_identity(self) -> HardwareIdentity:
        """قراءة معلومات تعريف المكونات."""

        if platform.system() != "Windows":
            raise RuntimeError(
                "This provider supports Windows only."
            )

        raw_data = self._run_cim_query()

        return HardwareIdentity(
            gpus=tuple(
                self._parse_gpus(raw_data.get("gpus"))
            ),
            motherboards=tuple(
                self._parse_motherboards(
                    raw_data.get("motherboards")
                )
            ),
            bios=self._parse_bios(
                raw_data.get("bios")
            ),
        )

    def _run_cim_query(self) -> dict[str, Any]:
        """تشغيل استعلامات CIM وإرجاع JSON."""

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

$gpus = @(
    Get-CimInstance -ClassName Win32_VideoController |
    Select-Object `
        Name,
        AdapterCompatibility,
        VideoProcessor,
        DriverVersion,
        PNPDeviceID,
        Status
)

$motherboards = @(
    Get-CimInstance -ClassName Win32_BaseBoard |
    Select-Object `
        Manufacturer,
        Product,
        Version,
        SerialNumber
)

$bios = (
    Get-CimInstance -ClassName Win32_BIOS |
    Select-Object -First 1 `
        Manufacturer,
        SMBIOSBIOSVersion,
        @{
            Name = "ReleaseDate"
            Expression = {
                if ($_.ReleaseDate) {
                    $_.ReleaseDate.ToString("yyyy-MM-dd")
                }
                else {
                    $null
                }
            }
        },
        SerialNumber
)

$result = [ordered]@{
    gpus = $gpus
    motherboards = $motherboards
    bios = $bios
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
            timeout=20,
            check=False,
            creationflags=creation_flags,
        )

        if completed_process.returncode != 0:
            error_message = (
                completed_process.stderr.strip()
                or "PowerShell hardware query failed."
            )

            raise RuntimeError(error_message)

        output = (
            completed_process.stdout
            .lstrip("\ufeff")
            .strip()
        )

        if not output:
            raise RuntimeError(
                "PowerShell returned no hardware data."
            )

        try:
            parsed_data = json.loads(output)
        except json.JSONDecodeError as error:
            raise RuntimeError(
                "Windows returned invalid hardware data."
            ) from error

        if not isinstance(parsed_data, dict):
            raise RuntimeError(
                "Unexpected hardware data format."
            )

        return parsed_data

    def _parse_gpus(
        self,
        raw_gpus: Any,
    ) -> list[GpuInfo]:
        """تحويل بيانات كروت الشاشة إلى Models."""

        parsed_gpus: list[GpuInfo] = []

        for item in self._as_list(raw_gpus):
            if not isinstance(item, dict):
                continue

            name = self._clean_text(
                item.get("Name")
            )

            manufacturer = self._clean_text(
                item.get("AdapterCompatibility"),
                default="",
            )

            if not manufacturer:
                manufacturer = (
                    self._infer_gpu_manufacturer(name)
                )

            parsed_gpus.append(
                GpuInfo(
                    name=name,
                    manufacturer=manufacturer,
                    video_processor=self._clean_text(
                        item.get("VideoProcessor")
                    ),
                    driver_version=self._clean_text(
                        item.get("DriverVersion")
                    ),
                    pnp_device_id=self._clean_text(
                        item.get("PNPDeviceID")
                    ),
                    status=self._clean_text(
                        item.get("Status")
                    ),
                )
            )

        return parsed_gpus

    def _parse_motherboards(
        self,
        raw_motherboards: Any,
    ) -> list[MotherboardInfo]:
        """تحويل بيانات اللوحات الأم إلى Models."""

        parsed_motherboards: list[
            MotherboardInfo
        ] = []

        for item in self._as_list(
            raw_motherboards
        ):
            if not isinstance(item, dict):
                continue

            parsed_motherboards.append(
                MotherboardInfo(
                    manufacturer=self._clean_text(
                        item.get("Manufacturer")
                    ),
                    product=self._clean_text(
                        item.get("Product")
                    ),
                    version=self._clean_text(
                        item.get("Version")
                    ),
                    serial_number=self._clean_text(
                        item.get("SerialNumber")
                    ),
                )
            )

        return parsed_motherboards

    def _parse_bios(
        self,
        raw_bios: Any,
    ) -> BiosInfo | None:
        """تحويل بيانات BIOS إلى Model."""

        if not isinstance(raw_bios, dict):
            return None

        return BiosInfo(
            manufacturer=self._clean_text(
                raw_bios.get("Manufacturer")
            ),
            version=self._clean_text(
                raw_bios.get("SMBIOSBIOSVersion")
            ),
            release_date=self._clean_text(
                raw_bios.get("ReleaseDate")
            ),
            serial_number=self._clean_text(
                raw_bios.get("SerialNumber")
            ),
        )

    @staticmethod
    def _as_list(value: Any) -> list[Any]:
        """تحويل القيمة إلى قائمة بشكل آمن."""

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
        """تنظيف النص وإزالة المسافات الزائدة."""

        if value is None:
            return default

        cleaned_value = " ".join(
            str(value).strip().split()
        )

        return cleaned_value or default

    @staticmethod
    def _infer_gpu_manufacturer(
        gpu_name: str,
    ) -> str:
        """استنتاج الشركة من اسم كرت الشاشة."""

        normalized_name = gpu_name.lower()

        if "nvidia" in normalized_name:
            return "NVIDIA"

        if (
            "amd" in normalized_name
            or "radeon" in normalized_name
        ):
            return "AMD"

        if (
            "intel" in normalized_name
            or "arc" in normalized_name
        ):
            return "Intel"

        if "microsoft" in normalized_name:
            return "Microsoft"

        return "Unavailable"