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

from core.models.cleaner_cleanup import (
    CleanerCategoryCleanResult,
    CleanerCleanInventory,
)


@dataclass(slots=True)
class _CleanAccumulator:
    deleted_files: int = 0
    deleted_directories: int = 0
    deleted_size_bytes: int = 0
    skipped_items: int = 0
    failed_items: int = 0
    errors: list[str] = field(default_factory=list)


class _SHQueryRecycleBinInfo(ctypes.Structure):
    _fields_ = [
        ("cbSize", wintypes.DWORD),
        ("i64Size", ctypes.c_longlong),
        ("i64NumItems", ctypes.c_longlong),
    ]


class WindowsCleanerCleanupProvider:
    """حذف آمن للأقسام المحددة من Cleaner."""

    USER_TEMP_MINIMUM_AGE_HOURS = 24
    WINDOWS_TEMP_MINIMUM_AGE_HOURS = 24
    PIXEL_LOG_MINIMUM_AGE_HOURS = 30 * 24

    ERROR_SAMPLE_LIMIT = 12

    _CATEGORY_TITLES = {
        "user_temp": "User Temporary Files",
        "windows_temp": "Windows Temporary Files",
        "thumbnail_cache": "Thumbnail Cache",
        "directx_shader_cache": "DirectX Shader Cache",
        "crash_dumps": "Crash Dump Files",
        "windows_error_reports": "Windows Error Reports",
        "pixel_guardian_logs": "Pixel Guardian Old Logs",
        "recycle_bin": "Recycle Bin",
    }

    def clean_categories(
        self,
        category_keys: tuple[str, ...],
    ) -> CleanerCleanInventory:
        """تنظيف الأقسام المسموح بها فقط."""

        if platform.system() != "Windows":
            raise RuntimeError(
                "WindowsCleanerCleanupProvider supports Windows only."
            )

        normalized_keys = tuple(
            dict.fromkeys(
                str(key).strip()
                for key in category_keys
                if str(key).strip()
            )
        )

        if not normalized_keys:
            raise ValueError(
                "No Cleaner categories were selected."
            )

        unknown_keys = [
            key
            for key in normalized_keys
            if key not in self._CATEGORY_TITLES
        ]

        if unknown_keys:
            raise ValueError(
                "Unsupported Cleaner categories: "
                + ", ".join(unknown_keys)
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
                Path.home() / "AppData" / "Local",
            )
        )

        program_data = Path(
            os.environ.get(
                "ProgramData",
                r"C:\ProgramData",
            )
        )

        user_temp = Path(tempfile.gettempdir())

        category_results: list[
            CleanerCategoryCleanResult
        ] = []

        for key in normalized_keys:
            if key == "user_temp":
                result = self._clean_file_category(
                    key=key,
                    roots=(user_temp,),
                    minimum_age_hours=(
                        self.USER_TEMP_MINIMUM_AGE_HOURS
                    ),
                )

            elif key == "windows_temp":
                result = self._clean_file_category(
                    key=key,
                    roots=(windows_root / "Temp",),
                    minimum_age_hours=(
                        self.WINDOWS_TEMP_MINIMUM_AGE_HOURS
                    ),
                )

            elif key == "thumbnail_cache":
                result = self._clean_file_category(
                    key=key,
                    roots=(
                        local_app_data
                        / "Microsoft"
                        / "Windows"
                        / "Explorer",
                    ),
                    file_filter=(
                        self._is_thumbnail_cache_file
                    ),
                )

            elif key == "directx_shader_cache":
                result = self._clean_file_category(
                    key=key,
                    roots=(
                        local_app_data / "D3DSCache",
                    ),
                )

            elif key == "crash_dumps":
                result = self._clean_file_category(
                    key=key,
                    roots=(
                        local_app_data / "CrashDumps",
                        windows_root / "Minidump",
                    ),
                )

            elif key == "windows_error_reports":
                result = self._clean_file_category(
                    key=key,
                    roots=(
                        local_app_data
                        / "Microsoft"
                        / "Windows"
                        / "WER",
                        program_data
                        / "Microsoft"
                        / "Windows"
                        / "WER",
                    ),
                )

            elif key == "pixel_guardian_logs":
                result = self._clean_file_category(
                    key=key,
                    roots=(
                        local_app_data
                        / "PixelGuardian"
                        / "logs",
                    ),
                    minimum_age_hours=(
                        self.PIXEL_LOG_MINIMUM_AGE_HOURS
                    ),
                    file_filter=(
                        self._is_old_pixel_guardian_log
                    ),
                )

            elif key == "recycle_bin":
                result = self._clean_recycle_bin()

            else:
                raise RuntimeError(
                    f"Cleaner category handler missing: {key}"
                )

            category_results.append(result)

        return CleanerCleanInventory(
            cleaned_at=datetime.now().isoformat(
                timespec="seconds"
            ),
            requested_categories=normalized_keys,
            categories=tuple(category_results),
        )

    def _clean_file_category(
        self,
        key: str,
        roots: tuple[Path, ...],
        minimum_age_hours: int | None = None,
        file_filter: Callable[[Path], bool] | None = None,
    ) -> CleanerCategoryCleanResult:
        accumulator = _CleanAccumulator()
        current_time = time.time()

        minimum_age_seconds = (
            minimum_age_hours * 60 * 60
            if minimum_age_hours is not None
            else None
        )

        for root in roots:
            try:
                if not root.exists():
                    continue

                if root.is_symlink():
                    accumulator.skipped_items += 1
                    self._append_error(
                        accumulator,
                        f"Skipped symbolic link root: {root}",
                    )
                    continue

                if root.is_file():
                    self._try_delete_file(
                        file_path=root,
                        allowed_root=root.parent,
                        accumulator=accumulator,
                        current_time=current_time,
                        minimum_age_seconds=(
                            minimum_age_seconds
                        ),
                        file_filter=file_filter,
                    )
                    continue

                self._clean_directory(
                    directory=root,
                    allowed_root=root,
                    accumulator=accumulator,
                    current_time=current_time,
                    minimum_age_seconds=(
                        minimum_age_seconds
                    ),
                    file_filter=file_filter,
                    delete_directory=False,
                )

            except (OSError, PermissionError) as error:
                self._record_os_error(
                    accumulator,
                    root,
                    error,
                )

        return CleanerCategoryCleanResult(
            key=key,
            title=self._CATEGORY_TITLES[key],
            deleted_files=accumulator.deleted_files,
            deleted_directories=(
                accumulator.deleted_directories
            ),
            deleted_size_bytes=(
                accumulator.deleted_size_bytes
            ),
            skipped_items=accumulator.skipped_items,
            failed_items=accumulator.failed_items,
            errors=tuple(accumulator.errors),
        )

    def _clean_directory(
        self,
        directory: Path,
        allowed_root: Path,
        accumulator: _CleanAccumulator,
        current_time: float,
        minimum_age_seconds: int | None,
        file_filter: Callable[[Path], bool] | None,
        delete_directory: bool,
    ) -> None:
        if not self._is_within_root(
            directory,
            allowed_root,
        ):
            accumulator.failed_items += 1
            self._append_error(
                accumulator,
                f"Blocked path outside allowed root: {directory}",
            )
            return

        try:
            with os.scandir(directory) as entries:
                for entry in entries:
                    entry_path = Path(entry.path)

                    try:
                        if entry.is_symlink():
                            accumulator.skipped_items += 1
                            continue

                        if entry.is_dir(
                            follow_symlinks=False
                        ):
                            self._clean_directory(
                                directory=entry_path,
                                allowed_root=allowed_root,
                                accumulator=accumulator,
                                current_time=current_time,
                                minimum_age_seconds=(
                                    minimum_age_seconds
                                ),
                                file_filter=file_filter,
                                delete_directory=True,
                            )
                            continue

                        if entry.is_file(
                            follow_symlinks=False
                        ):
                            self._try_delete_file(
                                file_path=entry_path,
                                allowed_root=allowed_root,
                                accumulator=accumulator,
                                current_time=current_time,
                                minimum_age_seconds=(
                                    minimum_age_seconds
                                ),
                                file_filter=file_filter,
                            )

                    except (OSError, PermissionError) as error:
                        self._record_os_error(
                            accumulator,
                            entry_path,
                            error,
                        )

        except (OSError, PermissionError) as error:
            self._record_os_error(
                accumulator,
                directory,
                error,
            )
            return

        if not delete_directory:
            return

        try:
            directory.rmdir()
            accumulator.deleted_directories += 1

        except OSError:
            # غالبًا المجلد غير فارغ أو مستخدم؛ لا نجبر حذفه.
            pass

    def _try_delete_file(
        self,
        file_path: Path,
        allowed_root: Path,
        accumulator: _CleanAccumulator,
        current_time: float,
        minimum_age_seconds: int | None,
        file_filter: Callable[[Path], bool] | None,
    ) -> None:
        if not self._is_within_root(
            file_path,
            allowed_root,
        ):
            accumulator.failed_items += 1
            self._append_error(
                accumulator,
                f"Blocked path outside allowed root: {file_path}",
            )
            return

        try:
            if file_path.is_symlink():
                accumulator.skipped_items += 1
                return

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
                    current_time - file_stat.st_mtime
                )

                if file_age_seconds < minimum_age_seconds:
                    return

            file_size = max(
                0,
                int(file_stat.st_size),
            )

            file_path.unlink()

            accumulator.deleted_files += 1
            accumulator.deleted_size_bytes += file_size

        except FileNotFoundError:
            return

        except (OSError, PermissionError) as error:
            self._record_os_error(
                accumulator,
                file_path,
                error,
            )

    def _clean_recycle_bin(
        self,
    ) -> CleanerCategoryCleanResult:
        accumulator = _CleanAccumulator()

        try:
            file_count, total_size = (
                self._query_recycle_bin()
            )

            if file_count == 0:
                return CleanerCategoryCleanResult(
                    key="recycle_bin",
                    title=self._CATEGORY_TITLES[
                        "recycle_bin"
                    ],
                    deleted_files=0,
                    deleted_directories=0,
                    deleted_size_bytes=0,
                    skipped_items=0,
                    failed_items=0,
                    errors=(),
                )

            shell32 = ctypes.windll.shell32

            empty_recycle_bin = (
                shell32.SHEmptyRecycleBinW
            )
            empty_recycle_bin.argtypes = [
                wintypes.HWND,
                wintypes.LPCWSTR,
                wintypes.DWORD,
            ]
            empty_recycle_bin.restype = ctypes.c_long

            flags = (
                0x00000001  # SHERB_NOCONFIRMATION
                | 0x00000002  # SHERB_NOPROGRESSUI
                | 0x00000004  # SHERB_NOSOUND
            )

            result = empty_recycle_bin(
                None,
                None,
                flags,
            )

            if result != 0:
                raise OSError(
                    "Windows could not empty the Recycle Bin. "
                    f"HRESULT: {result}"
                )

            accumulator.deleted_files = file_count
            accumulator.deleted_size_bytes = total_size

        except (OSError, PermissionError) as error:
            accumulator.failed_items += 1
            self._append_error(
                accumulator,
                str(error),
            )

        return CleanerCategoryCleanResult(
            key="recycle_bin",
            title=self._CATEGORY_TITLES[
                "recycle_bin"
            ],
            deleted_files=accumulator.deleted_files,
            deleted_directories=0,
            deleted_size_bytes=(
                accumulator.deleted_size_bytes
            ),
            skipped_items=accumulator.skipped_items,
            failed_items=accumulator.failed_items,
            errors=tuple(accumulator.errors),
        )

    @staticmethod
    def _query_recycle_bin() -> tuple[int, int]:
        info = _SHQueryRecycleBinInfo()
        info.cbSize = ctypes.sizeof(
            _SHQueryRecycleBinInfo
        )

        query = ctypes.windll.shell32.SHQueryRecycleBinW
        query.argtypes = [
            wintypes.LPCWSTR,
            ctypes.POINTER(_SHQueryRecycleBinInfo),
        ]
        query.restype = ctypes.c_long

        result = query(
            None,
            ctypes.byref(info),
        )

        if result != 0:
            raise OSError(
                "Windows could not query the Recycle Bin. "
                f"HRESULT: {result}"
            )

        return (
            max(0, int(info.i64NumItems)),
            max(0, int(info.i64Size)),
        )

    @staticmethod
    def _is_thumbnail_cache_file(
        file_path: Path,
    ) -> bool:
        name = file_path.name.lower()

        return (
            name.startswith("thumbcache")
            and name.endswith(".db")
        )

    @staticmethod
    def _is_old_pixel_guardian_log(
        file_path: Path,
    ) -> bool:
        return (
            file_path.name.lower()
            != "application.log"
        )

    @staticmethod
    def _is_within_root(
        candidate: Path,
        root: Path,
    ) -> bool:
        try:
            candidate_text = os.path.normcase(
                os.path.abspath(candidate)
            )
            root_text = os.path.normcase(
                os.path.abspath(root)
            )

            return (
                os.path.commonpath(
                    [candidate_text, root_text]
                )
                == root_text
            )

        except (OSError, ValueError):
            return False

    def _record_os_error(
        self,
        accumulator: _CleanAccumulator,
        path: Path,
        error: OSError,
    ) -> None:
        windows_error = getattr(
            error,
            "winerror",
            None,
        )

        if (
            isinstance(error, PermissionError)
            or windows_error in {5, 32, 33}
        ):
            accumulator.skipped_items += 1
        else:
            accumulator.failed_items += 1

        self._append_error(
            accumulator,
            f"{path}: {error}",
        )

    def _append_error(
        self,
        accumulator: _CleanAccumulator,
        message: str,
    ) -> None:
        if (
            len(accumulator.errors)
            < self.ERROR_SAMPLE_LIMIT
        ):
            accumulator.errors.append(message)