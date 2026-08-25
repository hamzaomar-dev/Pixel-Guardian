import ctypes
import os
import platform
import tempfile
import time

from ctypes import wintypes
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Callable

from core.models.cleaner import (
    CleanerCategoryScan,
    CleanerScanInventory,
)


@dataclass(slots=True)
class _ScanAccumulator:
    """قيم داخلية تُستخدم أثناء فحص الملفات."""

    file_count: int = 0
    total_size_bytes: int = 0
    skipped_items: int = 0

    sample_files: list[str] = field(
        default_factory=list
    )

    missing_paths: list[str] = field(
        default_factory=list
    )

    unavailable_paths: list[str] = field(
        default_factory=list
    )


class _SHQueryRecycleBinInfo(ctypes.Structure):
    """بنية Windows الخاصة بمعلومات سلة المحذوفات."""

    _fields_ = [
        (
            "cbSize",
            wintypes.DWORD,
        ),
        (
            "i64Size",
            ctypes.c_longlong,
        ),
        (
            "i64NumItems",
            ctypes.c_longlong,
        ),
    ]


class WindowsCleanerScanProvider:
    """فحص الملفات القابلة للتنظيف في Windows."""

    SAMPLE_FILE_LIMIT = 8

    USER_TEMP_MINIMUM_AGE_HOURS = 24
    WINDOWS_TEMP_MINIMUM_AGE_HOURS = 24
    PIXEL_LOG_MINIMUM_AGE_HOURS = 30 * 24

    def get_cleaner_scan(
        self,
    ) -> CleanerScanInventory:
        """فحص أقسام التنظيف دون حذف أي ملف."""

        if platform.system() != "Windows":
            raise RuntimeError(
                "WindowsCleanerScanProvider supports "
                "Windows only."
            )

        windows_root = Path(
            os.environ.get(
                "SystemRoot",
                r"C:\Windows",
            )
        )

        local_app_data = Path(
            os.environ.get(
                "LOCALAPPDATA",
                Path.home()
                / "AppData"
                / "Local",
            )
        )

        program_data = Path(
            os.environ.get(
                "ProgramData",
                r"C:\ProgramData",
            )
        )

        user_temp = Path(
            tempfile.gettempdir()
        )

        categories = (
            self._scan_file_category(
                key="user_temp",
                title="User Temporary Files",
                description=(
                    "Temporary files created by applications "
                    "for the current Windows user."
                ),
                risk_level="safe",
                requires_admin=False,
                selected_by_default=True,
                minimum_age_hours=(
                    self.USER_TEMP_MINIMUM_AGE_HOURS
                ),
                paths=(
                    user_temp,
                ),
            ),
            self._scan_file_category(
                key="windows_temp",
                title="Windows Temporary Files",
                description=(
                    "Old temporary files stored inside "
                    "the Windows Temp directory."
                ),
                risk_level="safe",
                requires_admin=True,
                selected_by_default=True,
                minimum_age_hours=(
                    self.WINDOWS_TEMP_MINIMUM_AGE_HOURS
                ),
                paths=(
                    windows_root / "Temp",
                ),
            ),
            self._scan_file_category(
                key="thumbnail_cache",
                title="Thumbnail Cache",
                description=(
                    "Cached image and video thumbnails "
                    "that Windows can rebuild."
                ),
                risk_level="safe",
                requires_admin=False,
                selected_by_default=True,
                minimum_age_hours=None,
                paths=(
                    local_app_data
                    / "Microsoft"
                    / "Windows"
                    / "Explorer",
                ),
                file_filter=self._is_thumbnail_cache_file,
            ),
            self._scan_file_category(
                key="directx_shader_cache",
                title="DirectX Shader Cache",
                description=(
                    "Cached DirectX shader files. Games "
                    "may rebuild them after cleaning."
                ),
                risk_level="safe",
                requires_admin=False,
                selected_by_default=True,
                minimum_age_hours=None,
                paths=(
                    local_app_data / "D3DSCache",
                ),
            ),
            self._scan_file_category(
                key="crash_dumps",
                title="Crash Dump Files",
                description=(
                    "Application and Windows crash dump "
                    "files used for diagnostics."
                ),
                risk_level="advanced",
                requires_admin=True,
                selected_by_default=False,
                minimum_age_hours=None,
                paths=(
                    local_app_data / "CrashDumps",
                    windows_root / "Minidump",
                ),
            ),
            self._scan_file_category(
                key="windows_error_reports",
                title="Windows Error Reports",
                description=(
                    "Reports created when Windows or an "
                    "application encounters an error."
                ),
                risk_level="advanced",
                requires_admin=True,
                selected_by_default=False,
                minimum_age_hours=None,
                paths=(
                    local_app_data
                    / "Microsoft"
                    / "Windows"
                    / "WER",
                    program_data
                    / "Microsoft"
                    / "Windows"
                    / "WER",
                ),
            ),
            self._scan_file_category(
                key="pixel_guardian_logs",
                title="Pixel Guardian Old Logs",
                description=(
                    "Pixel Guardian log files older than "
                    "30 days. The active log is excluded."
                ),
                risk_level="advanced",
                requires_admin=False,
                selected_by_default=False,
                minimum_age_hours=(
                    self.PIXEL_LOG_MINIMUM_AGE_HOURS
                ),
                paths=(
                    local_app_data
                    / "PixelGuardian"
                    / "logs",
                ),
                file_filter=(
                    self._is_old_pixel_guardian_log_candidate
                ),
            ),
            self._scan_recycle_bin(),
        )

        return CleanerScanInventory(
            scanned_at=datetime.now().isoformat(
                timespec="seconds"
            ),
            categories=categories,
        )

    def _scan_file_category(
        self,
        key: str,
        title: str,
        description: str,
        risk_level: str,
        requires_admin: bool,
        selected_by_default: bool,
        minimum_age_hours: int | None,
        paths: tuple[Path, ...],
        file_filter: Callable[[Path], bool] | None = None,
    ) -> CleanerCategoryScan:
        """فحص مسار أو عدة مسارات لقسم واحد."""

        accumulator = _ScanAccumulator()

        current_time = time.time()

        minimum_age_seconds = (
            minimum_age_hours * 60 * 60
            if minimum_age_hours is not None
            else None
        )

        for path in paths:
            if not path.exists():
                accumulator.missing_paths.append(
                    str(path)
                )
                continue

            if path.is_symlink():
                accumulator.skipped_items += 1
                continue

            if path.is_file():
                self._inspect_file(
                    file_path=path,
                    accumulator=accumulator,
                    current_time=current_time,
                    minimum_age_seconds=(
                        minimum_age_seconds
                    ),
                    file_filter=file_filter,
                )
                continue

            self._scan_directory(
                directory=path,
                accumulator=accumulator,
                current_time=current_time,
                minimum_age_seconds=(
                    minimum_age_seconds
                ),
                file_filter=file_filter,
            )

        warnings: list[str] = []

        if accumulator.unavailable_paths:
            warnings.append(
                "Some paths could not be read because "
                "they were locked or require permission."
            )

        if accumulator.skipped_items:
            warnings.append(
                f"{accumulator.skipped_items} item(s) "
                "were skipped during the scan."
            )

        return CleanerCategoryScan(
            key=key,
            title=title,
            description=description,
            risk_level=risk_level,
            requires_admin=requires_admin,
            selected_by_default=selected_by_default,
            minimum_age_hours=minimum_age_hours,
            scanned_paths=tuple(
                str(path)
                for path in paths
            ),
            missing_paths=tuple(
                accumulator.missing_paths
            ),
            unavailable_paths=tuple(
                accumulator.unavailable_paths
            ),
            file_count=accumulator.file_count,
            total_size_bytes=(
                accumulator.total_size_bytes
            ),
            skipped_items=(
                accumulator.skipped_items
            ),
            sample_files=tuple(
                accumulator.sample_files
            ),
            warnings=tuple(warnings),
        )

    def _scan_directory(
        self,
        directory: Path,
        accumulator: _ScanAccumulator,
        current_time: float,
        minimum_age_seconds: int | None,
        file_filter: Callable[[Path], bool] | None,
    ) -> None:
        """فحص مجلد بشكل متكرر دون اتباع الروابط."""

        try:
            with os.scandir(directory) as entries:
                for entry in entries:
                    try:
                        if entry.is_symlink():
                            accumulator.skipped_items += 1
                            continue

                        if entry.is_dir(
                            follow_symlinks=False
                        ):
                            self._scan_directory(
                                directory=Path(
                                    entry.path
                                ),
                                accumulator=accumulator,
                                current_time=current_time,
                                minimum_age_seconds=(
                                    minimum_age_seconds
                                ),
                                file_filter=file_filter,
                            )
                            continue

                        if entry.is_file(
                            follow_symlinks=False
                        ):
                            self._inspect_file(
                                file_path=Path(
                                    entry.path
                                ),
                                accumulator=accumulator,
                                current_time=current_time,
                                minimum_age_seconds=(
                                    minimum_age_seconds
                                ),
                                file_filter=file_filter,
                            )

                    except OSError:
                        accumulator.skipped_items += 1

        except (OSError, PermissionError):
            path_text = str(directory)

            if (
                path_text
                not in accumulator.unavailable_paths
            ):
                accumulator.unavailable_paths.append(
                    path_text
                )

            accumulator.skipped_items += 1

    def _inspect_file(
        self,
        file_path: Path,
        accumulator: _ScanAccumulator,
        current_time: float,
        minimum_age_seconds: int | None,
        file_filter: Callable[[Path], bool] | None,
    ) -> None:
        """فحص ملف واحد وإضافته للنتيجة عند مطابقته."""

        try:
            if (
                file_filter is not None
                and not file_filter(file_path)
            ):
                return

            file_stat = file_path.stat(
                follow_symlinks=False
            )

            if minimum_age_seconds is not None:
                file_age_seconds = (
                    current_time
                    - file_stat.st_mtime
                )

                if (
                    file_age_seconds
                    < minimum_age_seconds
                ):
                    return

            file_size = max(
                0,
                int(file_stat.st_size),
            )

            accumulator.file_count += 1
            accumulator.total_size_bytes += file_size

            if (
                len(accumulator.sample_files)
                < self.SAMPLE_FILE_LIMIT
            ):
                accumulator.sample_files.append(
                    str(file_path)
                )

        except (OSError, PermissionError):
            accumulator.skipped_items += 1

    def _scan_recycle_bin(
        self,
    ) -> CleanerCategoryScan:
        """قراءة حجم وعدد عناصر سلة المحذوفات."""

        warnings: list[str] = []

        file_count = 0
        total_size_bytes = 0
        skipped_items = 0

        try:
            recycle_bin_info = (
                _SHQueryRecycleBinInfo()
            )

            recycle_bin_info.cbSize = (
                ctypes.sizeof(
                    _SHQueryRecycleBinInfo
                )
            )

            query_recycle_bin = (
                ctypes.windll
                .shell32
                .SHQueryRecycleBinW
            )

            query_recycle_bin.argtypes = [
                wintypes.LPCWSTR,
                ctypes.POINTER(
                    _SHQueryRecycleBinInfo
                ),
            ]

            query_recycle_bin.restype = (
                ctypes.c_long
            )

            result = query_recycle_bin(
                "",
                ctypes.byref(
                    recycle_bin_info
                ),
            )

            if result != 0:
                raise OSError(
                    "Windows returned Recycle Bin "
                    f"error code: {result}"
                )

            file_count = max(
                0,
                int(
                    recycle_bin_info.i64NumItems
                ),
            )

            total_size_bytes = max(
                0,
                int(
                    recycle_bin_info.i64Size
                ),
            )

        except Exception as error:
            skipped_items = 1

            warnings.append(
                "Recycle Bin information could not "
                f"be read: {error}"
            )

        return CleanerCategoryScan(
            key="recycle_bin",
            title="Recycle Bin",
            description=(
                "Files currently stored in the Windows "
                "Recycle Bin."
            ),
            risk_level="advanced",
            requires_admin=False,
            selected_by_default=False,
            minimum_age_hours=None,
            scanned_paths=(
                "Windows Recycle Bin",
            ),
            missing_paths=(),
            unavailable_paths=(),
            file_count=file_count,
            total_size_bytes=total_size_bytes,
            skipped_items=skipped_items,
            sample_files=(),
            warnings=tuple(warnings),
        )

    @staticmethod
    def _is_thumbnail_cache_file(
        file_path: Path,
    ) -> bool:
        """فحص اسم ملف Thumbnail Cache."""

        file_name = file_path.name.lower()

        return (
            file_name.startswith("thumbcache")
            and file_name.endswith(".db")
        )

    @staticmethod
    def _is_old_pixel_guardian_log_candidate(
        file_path: Path,
    ) -> bool:
        """استثناء ملف السجل النشط."""

        return (
            file_path.name.lower()
            != "application.log"
        )