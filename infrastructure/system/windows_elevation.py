import ctypes
import subprocess
import sys
from pathlib import Path
from typing import Sequence


class ElevationRequestError(RuntimeError):
    """فشل طلب تشغيل عملية بصلاحية Administrator."""


def is_running_as_admin() -> bool:
    """التحقق هل العملية الحالية تعمل كمسؤول."""

    try:
        return bool(
            ctypes.windll.shell32.IsUserAnAdmin()
        )

    except Exception:
        return False


def request_elevated_python_module(
    module_name: str,
    arguments: Sequence[str],
) -> None:
    """تشغيل Python module منفصل بصلاحية Administrator."""

    project_root = (
        Path(__file__).resolve().parents[2]
    )

    python_executable = Path(
        sys.executable
    ).resolve()

    parameters = subprocess.list2cmdline(
        [
            "-m",
            module_name,
            *arguments,
        ]
    )

    shell_execute = (
        ctypes.windll.shell32.ShellExecuteW
    )

    shell_execute.argtypes = [
        ctypes.c_void_p,
        ctypes.c_wchar_p,
        ctypes.c_wchar_p,
        ctypes.c_wchar_p,
        ctypes.c_wchar_p,
        ctypes.c_int,
    ]

    shell_execute.restype = ctypes.c_void_p

    result = shell_execute(
        None,
        "runas",
        str(python_executable),
        parameters,
        str(project_root),
        0,
    )

    result_code = int(
        result or 0
    )

    if result_code > 32:
        return

    error_messages = {
        2: "The Python executable was not found.",
        3: "The project path was not found.",
        5: (
            "Administrator permission was not granted "
            "or the UAC request was cancelled."
        ),
        8: "Windows did not have enough memory.",
        26: "A sharing violation occurred.",
        27: "The file association is incomplete.",
        28: "The operation timed out.",
        29: "A DDE transaction failed.",
        30: "Another DDE transaction is busy.",
        31: "No application is associated with the file.",
        32: "The required DLL could not be found.",
    }

    message = error_messages.get(
        result_code,
        (
            "Windows could not start the elevated "
            f"process. Error code: {result_code}"
        ),
    )

    raise ElevationRequestError(
        message
    )