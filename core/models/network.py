from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class NetworkAdapterInfo:
    """معلومات كرت شبكة فعلي."""

    name: str
    description: str
    interface_index: int | None
    adapter_type: str
    status: str
    mac_address: str
    link_speed: str
    media_type: str
    physical_media_type: str
    ipv4_addresses: tuple[str, ...]
    ipv6_addresses: tuple[str, ...]
    default_gateway: str
    dns_servers: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class NetworkInventory:
    """جميع كروت الشبكة المكتشفة."""

    adapters: tuple[NetworkAdapterInfo, ...]