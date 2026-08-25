import argparse
import json
import os

from dataclasses import asdict
from pathlib import Path
from typing import Any

from core.services.cleaner_service import CleanerService


def _write_result(
    output_path: Path,
    payload: dict[str, Any],
) -> None:
    """كتابة النتيجة بشكل ذري وآمن."""

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    temporary_path = output_path.with_suffix(
        output_path.suffix + ".tmp"
    )

    temporary_path.write_text(
        json.dumps(
            payload,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    os.replace(
        temporary_path,
        output_path,
    )


def main() -> int:
    """تشغيل Cleaner Scan في عملية Administrator."""

    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--output",
        required=True,
        help="Path used to store the scan result.",
    )

    arguments = parser.parse_args()

    output_path = Path(
        arguments.output
    ).resolve()

    try:
        result = (
            CleanerService()
            .scan_cleanable_files()
        )

        payload = {
            "success": bool(result.success),
            "message": result.message,
            "error_code": result.error_code,
            "source": result.source,
            "data": (
                asdict(result.data)
                if result.success
                and result.data is not None
                else None
            ),
        }

        _write_result(
            output_path,
            payload,
        )

        return (
            0
            if result.success
            else 1
        )

    except Exception as error:
        payload = {
            "success": False,
            "message": str(error),
            "error_code": (
                "ADMIN_CLEANER_SCAN_FAILED"
            ),
            "source": (
                "Elevated Windows Cleaner Scan"
            ),
            "data": None,
        }

        try:
            _write_result(
                output_path,
                payload,
            )

        except Exception:
            pass

        return 1


if __name__ == "__main__":
    raise SystemExit(
        main()
    )