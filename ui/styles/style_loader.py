from pathlib import Path


def load_app_style() -> str:
    """قراءة ملف تصميم Pixel Guardian الداكن."""

    style_path = (
        Path(__file__).resolve().parent
        / "app.qss"
    )

    if not style_path.is_file():
        raise FileNotFoundError(
            "Pixel Guardian stylesheet was not found: "
            f"{style_path}"
        )

    stylesheet = style_path.read_text(
        encoding="utf-8"
    ).strip()

    if not stylesheet:
        raise RuntimeError(
            "Pixel Guardian stylesheet is empty: "
            f"{style_path}"
        )

    return stylesheet