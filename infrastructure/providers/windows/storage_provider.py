import json
import platform
import shutil
import subprocess
from typing import Any

from core.models.storage import (
    LogicalVolumeInfo,
    PartitionInfo,
    StorageDeviceInfo,
    StorageInventory,
)


class WindowsStorageProvider:
    """قراءة أقراص وأقسام التخزين من Windows."""

    def get_storage_inventory(
        self,
    ) -> StorageInventory:
        """قراءة جميع أقراص التخزين."""

        if platform.system() != "Windows":
            raise RuntimeError(
                "WindowsStorageProvider supports "
                "Windows only."
            )

        raw_data = self._run_storage_query()

        physical_disks = self._as_list(
            raw_data.get("physicalDisks")
        )

        disk_drives = self._as_list(
            raw_data.get("diskDrives")
        )

        devices: list[StorageDeviceInfo] = []

        for raw_disk in disk_drives:
            if not isinstance(raw_disk, dict):
                continue

            disk_index = self._safe_int(
                raw_disk.get("Index")
            )

            physical_disk = (
                self._find_physical_disk(
                    raw_disk=raw_disk,
                    disk_index=disk_index,
                    physical_disks=physical_disks,
                )
            )

            bus_type = self._clean_text(
                (
                    physical_disk.get("BusType")
                    if physical_disk
                    else None
                ),
                default=self._clean_text(
                    raw_disk.get("InterfaceType")
                ),
            )

            physical_media_type = self._clean_text(
                (
                    physical_disk.get("MediaType")
                    if physical_disk
                    else None
                ),
                default="Unavailable",
            )

            win32_media_type = self._clean_text(
                raw_disk.get("MediaType"),
                default="Unavailable",
            )

            model = self._clean_text(
                raw_disk.get("Model")
            )

            storage_type = (
                self._detect_storage_type(
                    model=model,
                    bus_type=bus_type,
                    physical_media_type=(
                        physical_media_type
                    ),
                    win32_media_type=(
                        win32_media_type
                    ),
                )
            )

            partitions = self._parse_partitions(
                raw_disk.get("Partitions")
            )

            devices.append(
                StorageDeviceInfo(
                    index=disk_index,
                    device_id=self._clean_text(
                        raw_disk.get("DeviceID")
                    ),
                    model=model,
                    manufacturer=self._clean_text(
                        raw_disk.get(
                            "Manufacturer"
                        )
                    ),
                    serial_number=(
                        self._normalize_serial(
                            raw_disk.get(
                                "SerialNumber"
                            )
                        )
                    ),
                    interface_type=(
                        self._clean_text(
                            raw_disk.get(
                                "InterfaceType"
                            )
                        )
                    ),
                    bus_type=bus_type,
                    media_type=(
                        physical_media_type
                        if physical_media_type
                        != "Unavailable"
                        else win32_media_type
                    ),
                    storage_type=storage_type,
                    size_bytes=self._safe_int(
                        raw_disk.get("Size")
                    ),
                    status=self._clean_text(
                        raw_disk.get("Status")
                    ),
                    pnp_device_id=(
                        self._clean_text(
                            raw_disk.get(
                                "PNPDeviceID"
                            )
                        )
                    ),
                    partitions=partitions,
                )
            )

        devices.sort(
            key=lambda device: (
                device.index is None,
                (
                    device.index
                    if device.index is not None
                    else 9999
                ),
            )
        )

        return StorageInventory(
            devices=tuple(devices)
        )

    def _run_storage_query(
        self,
    ) -> dict[str, Any]:
        """تشغيل استعلام Windows وإرجاع JSON."""

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

[Console]::OutputEncoding = `
    [System.Text.UTF8Encoding]::new($false)

$physicalDisks = @()

try {
    $physicalDisks = @(
        Get-PhysicalDisk -ErrorAction Stop |
        Select-Object `
            DeviceId,
            FriendlyName,
            SerialNumber,
            MediaType,
            BusType,
            Size
    )
}
catch {
    $physicalDisks = @()
}

$diskDrives = @(
    Get-CimInstance `
        -ClassName Win32_DiskDrive |
    ForEach-Object {
        $disk = $_

        $partitions = @(
            Get-CimAssociatedInstance `
                -InputObject $disk `
                -Association `
                    Win32_DiskDriveToDiskPartition `
                -ErrorAction SilentlyContinue |
            ForEach-Object {
                $partition = $_

                $logicalDisks = @(
                    Get-CimAssociatedInstance `
                        -InputObject $partition `
                        -Association `
                            Win32_LogicalDiskToPartition `
                        -ErrorAction SilentlyContinue |
                    Select-Object `
                        DeviceID,
                        VolumeName,
                        FileSystem,
                        Size,
                        FreeSpace
                )

                [PSCustomObject]@{
                    Name = $partition.Name
                    DeviceID = $partition.DeviceID
                    Type = $partition.Type
                    Size = $partition.Size
                    BootPartition = `
                        $partition.BootPartition
                    PrimaryPartition = `
                        $partition.PrimaryPartition
                    LogicalDisks = $logicalDisks
                }
            }
        )

        [PSCustomObject]@{
            Index = $disk.Index
            DeviceID = $disk.DeviceID
            Model = $disk.Model
            Manufacturer = $disk.Manufacturer
            SerialNumber = $disk.SerialNumber
            InterfaceType = $disk.InterfaceType
            MediaType = $disk.MediaType
            Size = $disk.Size
            Status = $disk.Status
            PNPDeviceID = $disk.PNPDeviceID
            Partitions = $partitions
        }
    }
)

$result = [ordered]@{
    physicalDisks = $physicalDisks
    diskDrives = $diskDrives
}

$result |
    ConvertTo-Json `
        -Depth 8 `
        -Compress
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
                or "PowerShell storage query failed."
            )

            raise RuntimeError(error_message)

        output = (
            completed_process.stdout
            .lstrip("\ufeff")
            .strip()
        )

        if not output:
            raise RuntimeError(
                "Windows returned no storage data."
            )

        try:
            parsed_data = json.loads(output)

        except json.JSONDecodeError as error:
            raise RuntimeError(
                "Windows returned invalid storage data."
            ) from error

        if not isinstance(parsed_data, dict):
            raise RuntimeError(
                "Unexpected storage data format."
            )

        return parsed_data

    def _parse_partitions(
        self,
        raw_partitions: Any,
    ) -> tuple[PartitionInfo, ...]:
        """تحويل أقسام القرص إلى Models."""

        partitions: list[PartitionInfo] = []

        for item in self._as_list(
            raw_partitions
        ):
            if not isinstance(item, dict):
                continue

            volumes = self._parse_volumes(
                item.get("LogicalDisks")
            )

            partitions.append(
                PartitionInfo(
                    name=self._clean_text(
                        item.get("Name")
                    ),
                    device_id=self._clean_text(
                        item.get("DeviceID")
                    ),
                    partition_type=(
                        self._clean_text(
                            item.get("Type")
                        )
                    ),
                    size_bytes=self._safe_int(
                        item.get("Size")
                    ),
                    boot_partition=bool(
                        item.get(
                            "BootPartition",
                            False,
                        )
                    ),
                    primary_partition=bool(
                        item.get(
                            "PrimaryPartition",
                            False,
                        )
                    ),
                    volumes=volumes,
                )
            )

        return tuple(partitions)

    def _parse_volumes(
        self,
        raw_volumes: Any,
    ) -> tuple[LogicalVolumeInfo, ...]:
        """تحويل Volumes إلى Models."""

        volumes: list[LogicalVolumeInfo] = []

        for item in self._as_list(raw_volumes):
            if not isinstance(item, dict):
                continue

            volumes.append(
                LogicalVolumeInfo(
                    device_id=self._clean_text(
                        item.get("DeviceID")
                    ),
                    volume_name=self._clean_text(
                        item.get("VolumeName"),
                        default="",
                    ),
                    file_system=self._clean_text(
                        item.get("FileSystem")
                    ),
                    size_bytes=self._safe_int(
                        item.get("Size")
                    ),
                    free_bytes=self._safe_int(
                        item.get("FreeSpace")
                    ),
                )
            )

        return tuple(volumes)

    def _find_physical_disk(
        self,
        raw_disk: dict[str, Any],
        disk_index: int | None,
        physical_disks: list[Any],
    ) -> dict[str, Any] | None:
        """مطابقة Win32_DiskDrive مع Get-PhysicalDisk."""

        disk_serial = self._normalize_serial(
            raw_disk.get("SerialNumber")
        ).lower()

        disk_model = self._clean_text(
            raw_disk.get("Model"),
            default="",
        ).lower()

        for item in physical_disks:
            if not isinstance(item, dict):
                continue

            physical_index = self._safe_int(
                item.get("DeviceId")
            )

            if (
                disk_index is not None
                and physical_index == disk_index
            ):
                return item

        if disk_serial != "unavailable":
            for item in physical_disks:
                if not isinstance(item, dict):
                    continue

                physical_serial = (
                    self._normalize_serial(
                        item.get("SerialNumber")
                    ).lower()
                )

                if physical_serial == disk_serial:
                    return item

        if disk_model:
            for item in physical_disks:
                if not isinstance(item, dict):
                    continue

                friendly_name = (
                    self._clean_text(
                        item.get("FriendlyName"),
                        default="",
                    ).lower()
                )

                if (
                    friendly_name
                    and (
                        friendly_name in disk_model
                        or disk_model in friendly_name
                    )
                ):
                    return item

        return None

    @staticmethod
    def _detect_storage_type(
        model: str,
        bus_type: str,
        physical_media_type: str,
        win32_media_type: str,
    ) -> str:
        """تحديد HDD أو SSD أو NVMe بأفضل دقة متاحة."""

        model_lower = model.lower()
        bus_lower = bus_type.lower()
        physical_media_lower = (
            physical_media_type.lower()
        )
        win32_media_lower = (
            win32_media_type.lower()
        )

        if "nvme" in bus_lower:
            return "NVMe SSD"

        if "nvme" in model_lower:
            return "NVMe SSD"

        if "ssd" in physical_media_lower:
            return "SSD"

        if "ssd" in model_lower:
            return "SSD"

        if "hdd" in physical_media_lower:
            return "HDD"

        if "hard disk drive" in physical_media_lower:
            return "HDD"

        if "usb" in bus_lower:
            return "USB Storage"

        # Win32 غالبًا يعرض Fixed hard disk media
        # لكل من HDD وSSD، لذلك لا نعتمد عليه وحده.
        if (
            "removable" in win32_media_lower
            or "external" in win32_media_lower
        ):
            return "Removable Storage"

        return "Unknown"

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
        }

        if cleaned_value.lower() in invalid_values:
            return "Unavailable"

        return cleaned_value

    @staticmethod
    def _safe_int(
        value: Any,
    ) -> int | None:
        """تحويل القيمة إلى رقم بشكل آمن."""

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