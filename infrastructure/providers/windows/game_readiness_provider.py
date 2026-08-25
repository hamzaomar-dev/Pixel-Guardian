from __future__ import annotations

import re
import subprocess
import winreg
from datetime import datetime, timezone

from core.models.game_readiness import (
    GameReadinessReport,
    GamingSettingStatus,
)


class WindowsGameReadinessProvider:
    """فحص إعدادات Windows المتعلقة بالألعاب."""


    BALANCED_GUID = (
        "381b4222-f694-41f0-9685-ff5bb260df2e"
    )

    HIGH_PERFORMANCE_GUID = (
        "8c5e7fda-e8bf-4a96-9a85-a6e23a8c635c"
    )

    ULTIMATE_PERFORMANCE_GUID = (
        "e9a42b02-d5df-448d-aa00-03f14749eb61"
    )

    def scan(self) -> GameReadinessReport:
        """إنشاء تقرير جاهزية Windows للألعاب."""

        settings: list[GamingSettingStatus] = []
        warnings: list[str] = []

        settings.append(
            self._scan_game_mode(
                warnings
            )
        )

        settings.append(
            self._scan_hardware_gpu_scheduling(
                warnings
            )
        )

        settings.append(
            self._scan_game_dvr(
                warnings
            )
        )

        settings.append(
            self._scan_power_plan(
                warnings
            )
        )

        return GameReadinessReport(
            scanned_at=datetime.now(
                timezone.utc
            ).isoformat(),
            settings=tuple(settings),
            warnings=tuple(warnings),
        )

    def _scan_game_mode(
        self,
        warnings: list[str],
    ) -> GamingSettingStatus:
        """فحص حالة Windows Game Mode."""

        value = self._read_registry_dword(
            hive=winreg.HKEY_CURRENT_USER,
            key_path=(
                r"Software\Microsoft\GameBar"
            ),
            value_names=(
                "AutoGameModeEnabled",
                "AllowAutoGameMode",
            ),
            warnings=warnings,
        )

        if value is None:
            return GamingSettingStatus(
                key="game_mode",
                title="Windows Game Mode",
                description=(
                    "Prioritizes gaming workloads while "
                    "a game is running."
                ),
                current_value="Not detected",
                recommended_value="Enabled",
                is_recommended=False,
                available=False,
            )

        enabled = value == 1

        return GamingSettingStatus(
            key="game_mode",
            title="Windows Game Mode",
            description=(
                "Prioritizes gaming workloads while "
                "a game is running."
            ),
            current_value=(
                "Enabled"
                if enabled
                else "Disabled"
            ),
            recommended_value="Enabled",
            is_recommended=enabled,
        )

    def _scan_hardware_gpu_scheduling(
        self,
        warnings: list[str],
    ) -> GamingSettingStatus:
        """فحص Hardware-accelerated GPU scheduling."""

        value = self._read_registry_dword(
            hive=winreg.HKEY_LOCAL_MACHINE,
            key_path=(
                r"SYSTEM\CurrentControlSet"
                r"\Control\GraphicsDrivers"
            ),
            value_names=(
                "HwSchMode",
            ),
            warnings=warnings,
        )

        if value is None:
            return GamingSettingStatus(
                key="hags",
                title=(
                    "Hardware-accelerated "
                    "GPU Scheduling"
                ),
                description=(
                    "Allows compatible graphics hardware "
                    "to manage GPU scheduling."
                ),
                current_value=(
                    "System default or unavailable"
                ),
                recommended_value="Enabled",
                is_recommended=False,
                available=False,
            )

        enabled = value == 2

        return GamingSettingStatus(
            key="hags",
            title=(
                "Hardware-accelerated "
                "GPU Scheduling"
            ),
            description=(
                "Allows compatible graphics hardware "
                "to manage GPU scheduling."
            ),
            current_value=(
                "Enabled"
                if enabled
                else "Disabled"
            ),
            recommended_value="Enabled",
            is_recommended=enabled,
        )

    def _scan_game_dvr(
        self,
        warnings: list[str],
    ) -> GamingSettingStatus:
        """فحص تسجيل الألعاب في الخلفية."""

        game_dvr_enabled = (
            self._read_registry_dword(
                hive=winreg.HKEY_CURRENT_USER,
                key_path=(
                    r"System\GameConfigStore"
                ),
                value_names=(
                    "GameDVR_Enabled",
                ),
                warnings=warnings,
            )
        )

        app_capture_enabled = (
            self._read_registry_dword(
                hive=winreg.HKEY_CURRENT_USER,
                key_path=(
                    r"Software\Microsoft\Windows"
                    r"\CurrentVersion\GameDVR"
                ),
                value_names=(
                    "AppCaptureEnabled",
                ),
                warnings=warnings,
            )
        )

        detected_values = [
            value
            for value in (
                game_dvr_enabled,
                app_capture_enabled,
            )
            if value is not None
        ]

        if not detected_values:
            return GamingSettingStatus(
                key="game_dvr",
                title="Xbox Game DVR",
                description=(
                    "Controls game capture and "
                    "background recording features."
                ),
                current_value="Not detected",
                recommended_value="User preference",
                is_recommended=True,
                available=False,
                score_eligible=False,
            )

        enabled = any(
            value == 1
            for value in detected_values
        )

        return GamingSettingStatus(
            key="game_dvr",
            title="Xbox Game DVR",
            description=(
                "Controls game capture and "
                "background recording features."
            ),
            current_value=(
                "Enabled"
                if enabled
                else "Disabled"
            ),
            recommended_value="User preference",
            is_recommended=True,
            score_eligible=False,
        )

    def _scan_power_plan(
        self,
        warnings: list[str],
    ) -> GamingSettingStatus:
        """فحص خطة الطاقة النشطة."""

        try:
            completed_process = subprocess.run(
                [
                    "powercfg",
                    "/getactivescheme",
                ],
                capture_output=True,
                text=True,
                errors="replace",
                timeout=10,
                check=False,
                creationflags=(
                    subprocess.CREATE_NO_WINDOW
                ),
            )

        except (
            OSError,
            subprocess.SubprocessError,
        ) as error:
            warnings.append(
                "Could not read the active power plan: "
                f"{error}"
            )

            return GamingSettingStatus(
                key="power_plan",
                title="Windows Power Plan",
                description=(
                    "Controls how Windows balances "
                    "performance and power usage."
                ),
                current_value="Unavailable",
                recommended_value=(
                    "High performance or "
                    "Ultimate Performance"
                ),
                is_recommended=False,
                available=False,
            )

        output = (
            completed_process.stdout
            or completed_process.stderr
            or ""
        ).strip()

        guid_match = re.search(
            r"[0-9a-fA-F]{8}"
            r"-[0-9a-fA-F]{4}"
            r"-[0-9a-fA-F]{4}"
            r"-[0-9a-fA-F]{4}"
            r"-[0-9a-fA-F]{12}",
            output,
        )

        if guid_match is None:
            warnings.append(
                "Windows returned an unknown "
                "power plan response."
            )

            return GamingSettingStatus(
                key="power_plan",
                title="Windows Power Plan",
                description=(
                    "Controls how Windows balances "
                    "performance and power usage."
                ),
                current_value="Unknown",
                recommended_value=(
                    "High performance or "
                    "Ultimate Performance"
                ),
                is_recommended=False,
                available=False,
            )

        active_guid = (
            guid_match.group(0).casefold()
        )

        name_match = re.search(
            r"\(([^()]*)\)",
            output,
        )

        plan_name = (
            name_match.group(1).strip()
            if name_match
            else active_guid
        )

        recommended = active_guid in {
            self.BALANCED_GUID,
            self.HIGH_PERFORMANCE_GUID,
            self.ULTIMATE_PERFORMANCE_GUID,
        }

        return GamingSettingStatus(
            key="power_plan",
            title="Windows Power Plan",
            description=(
                "Controls how Windows balances "
                "performance and power usage."
            ),
            current_value=plan_name,
            recommended_value=(
                "Balanced, High performance, "
                "or Ultimate Performance"
            ),
            is_recommended=recommended,
        )

    @staticmethod
    def _read_registry_dword(
        hive: int,
        key_path: str,
        value_names: tuple[str, ...],
        warnings: list[str],
    ) -> int | None:
        """قراءة أول قيمة DWORD متاحة من Registry."""

        try:
            with winreg.OpenKey(
                hive,
                key_path,
                0,
                winreg.KEY_READ,
            ) as registry_key:

                for value_name in value_names:
                    try:
                        value, _value_type = (
                            winreg.QueryValueEx(
                                registry_key,
                                value_name,
                            )
                        )

                    except FileNotFoundError:
                        continue

                    try:
                        return int(value)

                    except (
                        TypeError,
                        ValueError,
                    ):
                        warnings.append(
                            "Invalid registry value: "
                            f"{key_path}\\{value_name}"
                        )
                        return None

        except FileNotFoundError:
            return None

        except PermissionError as error:
            warnings.append(
                "Registry access was denied for "
                f"{key_path}: {error}"
            )

        except OSError as error:
            warnings.append(
                "Could not read registry key "
                f"{key_path}: {error}"
            )

        return None