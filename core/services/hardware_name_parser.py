from __future__ import annotations

import re

from core.models.hardware_benchmark import (
    DetectedHardware,
    HardwareKind,
)


class HardwareNameParser:
    """تنظيف وتحليل أسماء المعالجات وكروت الشاشة."""

    _SPACE_PATTERN = re.compile(r"\s+")

    _FREQUENCY_PATTERN = re.compile(
        r"(?:@|\bat\b)?\s*"
        r"\d+(?:\.\d+)?\s*"
        r"(?:ghz|mhz)\b",
        re.IGNORECASE,
    )

    _CORE_DESCRIPTION_PATTERN = re.compile(
        r"\b\d+\s*[- ]?\s*core(?:s)?\b",
        re.IGNORECASE,
    )

    _CPU_NOISE_PATTERNS = (
        re.compile(
            r"\bcpu\b",
            re.IGNORECASE,
        ),
        re.compile(
            r"\bprocessor\b",
            re.IGNORECASE,
        ),
        re.compile(
            r"\bwith radeon graphics\b",
            re.IGNORECASE,
        ),
    )

    _GPU_NOISE_PATTERNS = (
        re.compile(
            r"\bgraphics adapter\b",
            re.IGNORECASE,
        ),
        re.compile(
            r"\bdisplay adapter\b",
            re.IGNORECASE,
        ),
        re.compile(
            r"\bgraphics card\b",
            re.IGNORECASE,
        ),
    )

    _VENDOR_PATTERNS = (
        (
            "NVIDIA",
            (
                "nvidia",
                "geforce",
                "quadro",
                "tesla",
                "rtx",
                "gtx",
            ),
        ),
        (
            "AMD",
            (
                "advanced micro devices",
                "amd",
                "ryzen",
                "radeon",
                "athlon",
                "threadripper",
                "epyc",
            ),
        ),
        (
            "Intel",
            (
                "intel",
                "core ultra",
                "core i",
                "xeon",
                "iris",
                "arc",
                "pentium",
                "celeron",
            ),
        ),
        (
            "Apple",
            (
                "apple",
                "m1",
                "m2",
                "m3",
                "m4",
                "m5",
            ),
        ),
        (
            "Qualcomm",
            (
                "qualcomm",
                "snapdragon",
                "adreno",
            ),
        ),
        (
            "Microsoft",
            (
                "microsoft",
                "basic display",
            ),
        ),
        (
            "VMware",
            (
                "vmware",
                "svga",
            ),
        ),
    )

    @classmethod
    def parse_cpu(
        cls,
        raw_name: str,
        physical_cores: int | None = None,
        logical_cores: int | None = None,
    ) -> DetectedHardware:
        """تحليل اسم معالج مكتشف من Windows."""

        safe_name = cls._safe_text(
            raw_name
        )

        normalized_name = (
            cls.normalize_cpu_name(
                safe_name
            )
        )

        vendor = cls.detect_vendor(
            safe_name
        )

        return DetectedHardware(
            kind=HardwareKind.CPU,
            raw_name=safe_name,
            normalized_name=normalized_name,
            vendor=vendor,
            physical_cores=cls._safe_positive_int(
                physical_cores
            ),
            logical_cores=cls._safe_positive_int(
                logical_cores
            ),
        )

    @classmethod
    def parse_gpu(
        cls,
        raw_name: str,
        dedicated_memory_bytes: int | None = None,
    ) -> DetectedHardware:
        """تحليل اسم كرت شاشة مكتشف من Windows."""

        safe_name = cls._safe_text(
            raw_name
        )

        normalized_name = (
            cls.normalize_gpu_name(
                safe_name
            )
        )

        vendor = cls.detect_vendor(
            safe_name
        )

        return DetectedHardware(
            kind=HardwareKind.GPU,
            raw_name=safe_name,
            normalized_name=normalized_name,
            vendor=vendor,
            dedicated_memory_bytes=(
                cls._safe_positive_int(
                    dedicated_memory_bytes
                )
            ),
        )

    @classmethod
    def normalize_cpu_name(
        cls,
        raw_name: str,
    ) -> str:
        """تنظيف اسم المعالج مع الحفاظ على رقم الموديل."""

        value = cls._prepare_name(
            raw_name
        )

        value = cls._FREQUENCY_PATTERN.sub(
            " ",
            value,
        )

        value = (
            cls._CORE_DESCRIPTION_PATTERN.sub(
                " ",
                value,
            )
        )

        for pattern in (
            cls._CPU_NOISE_PATTERNS
        ):
            value = pattern.sub(
                " ",
                value,
            )

        return cls._finish_name(
            value
        )

    @classmethod
    def normalize_gpu_name(
        cls,
        raw_name: str,
    ) -> str:
        """تنظيف اسم كرت الشاشة مع الحفاظ على رقم الموديل."""

        value = cls._prepare_name(
            raw_name
        )

        for pattern in (
            cls._GPU_NOISE_PATTERNS
        ):
            value = pattern.sub(
                " ",
                value,
            )

        return cls._finish_name(
            value
        )

    @classmethod
    def normalize_search_text(
        cls,
        value: str,
    ) -> str:
        """تنظيف اسم قبل استخدامه في البحث والمطابقة."""

        return cls._finish_name(
            cls._prepare_name(
                value
            )
        )

    @classmethod
    def detect_vendor(
        cls,
        raw_name: str,
    ) -> str:
        """تحديد الشركة المصنّعة من اسم القطعة."""

        normalized_name = (
            cls.normalize_search_text(
                raw_name
            )
        )

        for vendor, patterns in (
            cls._VENDOR_PATTERNS
        ):
            for pattern in patterns:
                normalized_pattern = (
                    cls.normalize_search_text(
                        pattern
                    )
                )

                if cls._contains_term(
                    normalized_name,
                    normalized_pattern,
                ):
                    return vendor

        return "Unknown"

    @classmethod
    def extract_model_tokens(
        cls,
        normalized_name: str,
    ) -> tuple[str, ...]:
        """استخراج الكلمات المهمة المستخدمة بالمطابقة."""

        ignored_tokens = {
            "amd",
            "intel",
            "nvidia",
            "apple",
            "qualcomm",
            "advanced",
            "micro",
            "devices",
            "graphics",
            "geforce",
            "radeon",
            "processor",
        }

        tokens = tuple(
            token
            for token in cls.normalize_search_text(
                normalized_name
            ).split()
            if (
                token
                and token not in ignored_tokens
            )
        )

        return tokens

    @staticmethod
    def _contains_term(
        normalized_name: str,
        term: str,
    ) -> bool:
        """فحص وجود كلمة أو عبارة كاملة داخل الاسم."""

        if not term:
            return False

        padded_name = (
            f" {normalized_name} "
        )

        padded_term = (
            f" {term} "
        )

        return padded_term in padded_name

    @classmethod
    def _prepare_name(
        cls,
        value: str,
    ) -> str:
        """إزالة الرموز والعلامات غير المهمة."""

        cleaned = cls._safe_text(
            value
        ).casefold()

        replacements = {
            "®": " ",
            "™": " ",
            "©": " ",
            "(r)": " ",
            "(tm)": " ",
            "(c)": " ",
            "_": " ",
            "/": " ",
            "\\": " ",
            ",": " ",
            ";": " ",
            ":": " ",
            "(": " ",
            ")": " ",
            "[": " ",
            "]": " ",
            "{": " ",
            "}": " ",
        }

        for old_value, new_value in (
            replacements.items()
        ):
            cleaned = cleaned.replace(
                old_value,
                new_value,
            )

        # نحول الشرطة بين رقمين أو كلمات إلى مسافة
        # حتى تتطابق i5-9400F مع i5 9400F.
        cleaned = re.sub(
            r"(?<=\w)-(?=\w)",
            " ",
            cleaned,
        )

        cleaned = re.sub(
            r"[^a-z0-9.+\s]",
            " ",
            cleaned,
        )

        return cleaned

    @classmethod
    def _finish_name(
        cls,
        value: str,
    ) -> str:
        """توحيد المسافات وإزالة الفراغات الزائدة."""

        return cls._SPACE_PATTERN.sub(
            " ",
            value,
        ).strip()

    @staticmethod
    def _safe_text(
        value: object,
    ) -> str:
        """تحويل القيمة إلى نص آمن."""

        if value is None:
            return ""

        return str(
            value
        ).strip()

    @staticmethod
    def _safe_positive_int(
        value: object,
    ) -> int | None:
        """تحويل القيمة إلى رقم موجب أو None."""

        try:
            converted_value = int(
                value
            )

        except (
            TypeError,
            ValueError,
        ):
            return None

        if converted_value <= 0:
            return None

        return converted_value