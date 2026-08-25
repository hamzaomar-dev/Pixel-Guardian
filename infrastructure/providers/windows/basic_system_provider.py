import os
import platform
import socket
import winreg
from typing import Any

import psutil

from core.models.basic_system_info import BasicSystemInfo


class WindowsBasicSystemProvider:
    """قراءة المعلومات الأساسية من Windows."""

    WINDOWS_VERSION_KEY = (
        r"SOFTWARE\Microsoft\Windows NT\CurrentVersion"
    )

    CPU_KEY = (
        r"HARDWARE\DESCRIPTION\System\CentralProcessor\0"
    )

    def get_basic_system_info(self) -> BasicSystemInfo:
        """قراءة نظام التشغيل والمعالج والرام."""

        if platform.system() != "Windows":
            raise RuntimeError(
                "WindowsBasicSystemProvider supports Windows only."
            )

        memory = psutil.virtual_memory()

        operating_system, os_version, os_build = (
            self._get_windows_version()
        )

        return BasicSystemInfo(
            operating_system=operating_system,
            os_version=os_version,
            os_build=os_build,
            architecture=self._get_architecture(),
            computer_name=socket.gethostname(),
            cpu_name=self._get_cpu_name(),
            physical_cores=psutil.cpu_count(logical=False),
            logical_cores=psutil.cpu_count(logical=True),
            total_memory_bytes=int(memory.total),
            available_memory_bytes=int(memory.available),
        )

    def _get_cpu_name(self) -> str:
        cpu_name = self._read_registry_value(
            self.CPU_KEY,
            "ProcessorNameString",
        )

        if cpu_name:
            return self._clean_text(cpu_name)

        fallback_name = (
            platform.processor()
            or platform.uname().processor
        )

        return self._clean_text(
            fallback_name or "Unavailable"
        )

    def _get_windows_version(
        self,
    ) -> tuple[str, str, str]:
        product_name = self._read_registry_value(
            self.WINDOWS_VERSION_KEY,
            "ProductName",
        )

        display_version = self._read_registry_value(
            self.WINDOWS_VERSION_KEY,
            "DisplayVersion",
        )

        if not display_version:
            display_version = self._read_registry_value(
                self.WINDOWS_VERSION_KEY,
                "ReleaseId",
            )

        build_number = self._read_registry_value(
            self.WINDOWS_VERSION_KEY,
            "CurrentBuildNumber",
        )

        ubr = self._read_registry_value(
            self.WINDOWS_VERSION_KEY,
            "UBR",
        )

        product_name_text = self._clean_text(
            product_name
            or f"{platform.system()} {platform.release()}"
        )

        build_number_text = self._clean_text(
            build_number or platform.version()
        )

        # بعض إصدارات Windows 11 قد تبقى مسجلة باسم Windows 10.
        try:
            build_as_number = int(build_number_text)

            if (
                build_as_number >= 22000
                and "Windows 10" in product_name_text
            ):
                product_name_text = product_name_text.replace(
                    "Windows 10",
                    "Windows 11",
                    1,
                )
        except ValueError:
            pass

        if ubr is not None:
            full_build = (
                f"{build_number_text}."
                f"{self._clean_text(ubr)}"
            )
        else:
            full_build = build_number_text

        version_text = self._clean_text(
            display_version or platform.release()
        )

        return (
            product_name_text,
            version_text,
            full_build,
        )

    def _get_architecture(self) -> str:
        architecture = (
            platform.machine()
            or os.getenv("PROCESSOR_ARCHITECTURE")
            or "Unavailable"
        )

        return self._clean_text(architecture)

    @staticmethod
    def _read_registry_value(
        key_path: str,
        value_name: str,
    ) -> Any | None:
        access = winreg.KEY_READ

        if hasattr(winreg, "KEY_WOW64_64KEY"):
            access |= winreg.KEY_WOW64_64KEY

        try:
            with winreg.OpenKey(
                winreg.HKEY_LOCAL_MACHINE,
                key_path,
                0,
                access,
            ) as registry_key:
                value, _ = winreg.QueryValueEx(
                    registry_key,
                    value_name,
                )

                return value

        except OSError:
            return None

    @staticmethod
    def _clean_text(value: Any) -> str:
        """تنظيف المسافات الزائدة من قيم Registry."""

        return " ".join(str(value).strip().split())