import json
import platform
import shutil
import subprocess
from typing import Any

from core.models.network import (
    NetworkAdapterInfo,
    NetworkInventory,
)


class WindowsNetworkProvider:
    """قراءة معلومات كروت الشبكة الفعلية من Windows."""

    def get_network_inventory(
        self,
    ) -> NetworkInventory:
        """قراءة جميع كروت الشبكة الفعلية."""

        if platform.system() != "Windows":
            raise RuntimeError(
                "WindowsNetworkProvider supports "
                "Windows only."
            )

        raw_data = self._run_network_query()

        adapters: list[NetworkAdapterInfo] = []

        for item in self._as_list(
            raw_data.get("adapters")
        ):
            if not isinstance(item, dict):
                continue

            name = self._clean_text(
                item.get("Name")
            )

            description = self._clean_text(
                item.get("InterfaceDescription")
            )

            media_type = self._clean_text(
                item.get("MediaType")
            )

            physical_media_type = self._clean_text(
                item.get("PhysicalMediaType")
            )

            adapter_type = self._detect_adapter_type(
                name=name,
                description=description,
                media_type=media_type,
                physical_media_type=physical_media_type,
            )

            adapters.append(
                NetworkAdapterInfo(
                    name=name,
                    description=description,
                    interface_index=self._safe_int(
                        item.get("InterfaceIndex")
                    ),
                    adapter_type=adapter_type,
                    status=self._clean_text(
                        item.get("Status")
                    ),
                    mac_address=(
                        self._normalize_mac_address(
                            item.get("MacAddress")
                        )
                    ),
                    link_speed=self._clean_text(
                        item.get("LinkSpeed")
                    ),
                    media_type=media_type,
                    physical_media_type=(
                        physical_media_type
                    ),
                    ipv4_addresses=(
                        self._parse_text_tuple(
                            item.get("IPv4Addresses")
                        )
                    ),
                    ipv6_addresses=(
                        self._parse_text_tuple(
                            item.get("IPv6Addresses")
                        )
                    ),
                    default_gateway=self._clean_text(
                        item.get("DefaultGateway")
                    ),
                    dns_servers=(
                        self._parse_text_tuple(
                            item.get("DnsServers")
                        )
                    ),
                )
            )

        adapters.sort(
            key=lambda adapter: (
                self._adapter_sort_order(
                    adapter.adapter_type
                ),
                adapter.status.lower() != "up",
                adapter.name.lower(),
            )
        )

        return NetworkInventory(
            adapters=tuple(adapters)
        )

    def _run_network_query(
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

$adapters = @(
    Get-NetAdapter -IncludeHidden -ErrorAction Stop |
    Where-Object {
        $_.HardwareInterface -eq $true
    } |
    ForEach-Object {
        $adapter = $_
        $ipConfiguration = $null

        try {
            $ipConfiguration = Get-NetIPConfiguration `
                -InterfaceIndex $adapter.ifIndex `
                -ErrorAction Stop
        }
        catch {
            $ipConfiguration = $null
        }

        $ipv4Addresses = @()
        $ipv6Addresses = @()
        $dnsServers = @()
        $defaultGateway = $null

        if ($null -ne $ipConfiguration) {
            $ipv4Addresses = @(
                $ipConfiguration.IPv4Address |
                ForEach-Object {
                    $_.IPAddress
                }
            )

            $ipv6Addresses = @(
                $ipConfiguration.IPv6Address |
                ForEach-Object {
                    $_.IPAddress
                }
            )

            if ($null -ne $ipConfiguration.DNSServer) {
                $dnsServers = @(
                    $ipConfiguration.DNSServer.ServerAddresses
                )
            }

            $ipv4Gateways = @(
                $ipConfiguration.IPv4DefaultGateway |
                ForEach-Object {
                    $_.NextHop
                }
            )

            $ipv6Gateways = @(
                $ipConfiguration.IPv6DefaultGateway |
                ForEach-Object {
                    $_.NextHop
                }
            )

            if ($ipv4Gateways.Count -gt 0) {
                $defaultGateway = $ipv4Gateways[0]
            }
            elseif ($ipv6Gateways.Count -gt 0) {
                $defaultGateway = $ipv6Gateways[0]
            }
        }

        [PSCustomObject]@{
            Name = $adapter.Name
            InterfaceDescription = $adapter.InterfaceDescription
            InterfaceIndex = $adapter.ifIndex
            Status = [string]$adapter.Status
            MacAddress = $adapter.MacAddress
            LinkSpeed = [string]$adapter.LinkSpeed
            MediaType = [string]$adapter.MediaType
            PhysicalMediaType = [string]$adapter.PhysicalMediaType
            IPv4Addresses = $ipv4Addresses
            IPv6Addresses = $ipv6Addresses
            DefaultGateway = $defaultGateway
            DnsServers = $dnsServers
        }
    }
)

$result = [ordered]@{
    adapters = $adapters
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
            timeout=30,
            check=False,
            creationflags=creation_flags,
        )

        if completed_process.returncode != 0:
            error_message = (
                completed_process.stderr.strip()
                or "PowerShell network query failed."
            )

            raise RuntimeError(error_message)

        output = (
            completed_process.stdout
            .lstrip("\ufeff")
            .strip()
        )

        if not output:
            raise RuntimeError(
                "Windows returned no network data."
            )

        try:
            parsed_data = json.loads(output)

        except json.JSONDecodeError as error:
            raise RuntimeError(
                "Windows returned invalid network data."
            ) from error

        if not isinstance(parsed_data, dict):
            raise RuntimeError(
                "Unexpected network data format."
            )

        return parsed_data

    @staticmethod
    def _detect_adapter_type(
        name: str,
        description: str,
        media_type: str,
        physical_media_type: str,
    ) -> str:
        """تحديد نوع كرت الشبكة."""

        combined_text = " ".join(
            (
                name,
                description,
                media_type,
                physical_media_type,
            )
        ).lower()

        wifi_terms = (
            "wi-fi",
            "wifi",
            "wireless",
            "wlan",
            "802.11",
            "native 802.11",
        )

        ethernet_terms = (
            "ethernet",
            "802.3",
            "gigabit",
            "gbe",
            "pci-e ethernet",
        )

        bluetooth_terms = (
            "bluetooth",
        )

        if any(
            term in combined_text
            for term in wifi_terms
        ):
            return "Wi-Fi"

        if any(
            term in combined_text
            for term in ethernet_terms
        ):
            return "Ethernet"

        if any(
            term in combined_text
            for term in bluetooth_terms
        ):
            return "Bluetooth"

        return "Network Adapter"

    @staticmethod
    def _adapter_sort_order(
        adapter_type: str,
    ) -> int:
        """ترتيب أنواع كروت الشبكة."""

        order = {
            "Ethernet": 0,
            "Wi-Fi": 1,
            "Bluetooth": 2,
            "Network Adapter": 3,
        }

        return order.get(
            adapter_type,
            99,
        )

    @staticmethod
    def _normalize_mac_address(
        value: Any,
    ) -> str:
        """تنظيف عنوان MAC."""

        if value is None:
            return "Unavailable"

        cleaned_value = str(value).strip()

        if not cleaned_value:
            return "Unavailable"

        return cleaned_value.upper()

    @staticmethod
    def _parse_text_tuple(
        value: Any,
    ) -> tuple[str, ...]:
        """تحويل قيمة أو قائمة نصوص إلى tuple."""

        values: list[str] = []

        for item in WindowsNetworkProvider._as_list(
            value
        ):
            if item is None:
                continue

            cleaned_item = str(item).strip()

            if cleaned_item:
                values.append(cleaned_item)

        return tuple(
            dict.fromkeys(values)
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