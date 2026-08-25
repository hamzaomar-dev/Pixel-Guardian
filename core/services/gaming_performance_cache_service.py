from __future__ import annotations

import hashlib
import json
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path

from core.models.online_gaming_performance import (
    GamingLookupStatus,
    GamingPerformanceRequest,
    GamingResultSource,
    OnlineGamingPerformanceResult,
)


class GamingPerformanceCacheService:
    """
    حفظ نتائج أداء الألعاب محليًا.

    النتيجة تُستخدم لمدة محددة، وبعد انتهاء المدة
    يطلب البرنامج نتيجة جديدة من الإنترنت.
    """

    SCHEMA_VERSION = 2

    def __init__(
        self,
        cache_path: Path | None = None,
        max_age_days: int = 30,
    ) -> None:
        self._cache_path = (
            cache_path
            or self._default_cache_path()
        )

        self._max_age = timedelta(
            days=max(
                1,
                int(max_age_days),
            )
        )

    @property
    def cache_path(self) -> Path:
        """مسار ملف الكاش."""

        return self._cache_path

    def get(
        self,
        request: GamingPerformanceRequest,
    ) -> OnlineGamingPerformanceResult | None:
        """قراءة نتيجة محفوظة وغير منتهية."""

        database = self._read_database()

        cache_key = self._create_key(
            request
        )

        entry = database["entries"].get(
            cache_key
        )

        if not isinstance(
            entry,
            dict,
        ):
            return None

        if self._is_expired(
            entry
        ):
            self._remove_entry(
                database,
                cache_key,
            )
            return None

        try:
            status = GamingLookupStatus(
                entry["status"]
            )

            result_source_value = str(
                entry.get(
                    "result_source",
                    GamingResultSource.UNKNOWN.value,
                )
            )

            try:
                result_source = GamingResultSource(
                    result_source_value
                )
            except ValueError:
                result_source = GamingResultSource.UNKNOWN

            return OnlineGamingPerformanceResult(
                request=request,
                status=status,
                average_fps=self._optional_float(
                    entry.get(
                        "average_fps"
                    )
                ),
                minimum_fps=self._optional_float(
                    entry.get(
                        "minimum_fps"
                    )
                ),
                maximum_fps=self._optional_float(
                    entry.get(
                        "maximum_fps"
                    )
                ),
                one_percent_low_fps=(
                    self._optional_float(
                        entry.get(
                            "one_percent_low_fps"
                        )
                    )
                ),
                verdict=str(
                    entry.get(
                        "verdict",
                        "",
                    )
                ),
                result_source=result_source,
                provider_id=str(
                    entry.get(
                        "provider_id",
                        "",
                    )
                ),
                provider_name=str(
                    entry.get(
                        "provider_name",
                        "",
                    )
                ),
                source_url=entry.get(
                    "source_url"
                ),
                fetched_at=str(
                    entry.get(
                        "fetched_at",
                        "",
                    )
                ),
                message=str(
                    entry.get(
                        "message",
                        "",
                    )
                ),
            )

        except (
            KeyError,
            TypeError,
            ValueError,
        ):
            self._remove_entry(
                database,
                cache_key,
            )
            return None

    def put(
        self,
        result: OnlineGamingPerformanceResult,
    ) -> bool:
        """حفظ نتيجة أداء ناجحة."""

        if not result.is_available:
            return False

        database = self._read_database()

        cache_key = self._create_key(
            result.request
        )

        database["entries"][
            cache_key
        ] = {
            "request": (
                result.request
                .to_api_payload()
            ),
            "status": (
                result.status.value
            ),
            "average_fps": (
                result.safe_average_fps
            ),
            "minimum_fps": (
                result.safe_minimum_fps
            ),
            "maximum_fps": (
                result.safe_maximum_fps
            ),
            "one_percent_low_fps": (
                result.safe_one_percent_low_fps
            ),
            "verdict": (
                result.verdict
            ),
            "result_source": (
                result.result_source.value
            ),
            "provider_id": (
                result.provider_id
            ),
            "provider_name": (
                result.provider_name
            ),
            "source_url": (
                result.source_url
            ),
            "fetched_at": (
                result.fetched_at
            ),
            "message": (
                result.message
            ),
        }

        self._write_database(
            database
        )

        return True

    def remove(
        self,
        request: GamingPerformanceRequest,
    ) -> bool:
        """حذف نتيجة طلب محدد."""

        database = self._read_database()

        cache_key = self._create_key(
            request
        )

        if cache_key not in database["entries"]:
            return False

        del database["entries"][
            cache_key
        ]

        self._write_database(
            database
        )

        return True

    def clear(self) -> None:
        """حذف جميع نتائج الأداء المحفوظة."""

        self._write_database(
            self._empty_database()
        )

    def count(self) -> int:
        """عدد النتائج المحفوظة."""

        database = self._read_database()

        return len(
            database["entries"]
        )

    def _remove_entry(
        self,
        database: dict,
        cache_key: str,
    ) -> None:
        """حذف سجل غير صالح أو منتهي."""

        database["entries"].pop(
            cache_key,
            None,
        )

        self._write_database(
            database
        )

    def _is_expired(
        self,
        entry: dict,
    ) -> bool:
        """فحص انتهاء صلاحية النتيجة."""

        fetched_at = str(
            entry.get(
                "fetched_at",
                "",
            )
        ).strip()

        if not fetched_at:
            return True

        try:
            fetched_time = (
                datetime.fromisoformat(
                    fetched_at.replace(
                        "Z",
                        "+00:00",
                    )
                )
            )

        except ValueError:
            return True

        if fetched_time.tzinfo is None:
            fetched_time = fetched_time.replace(
                tzinfo=timezone.utc
            )

        current_time = datetime.now(
            timezone.utc
        )

        return (
            current_time
            - fetched_time.astimezone(
                timezone.utc
            )
            > self._max_age
        )

    @staticmethod
    def _create_key(
        request: GamingPerformanceRequest,
    ) -> str:
        """إنشاء مفتاح فريد للطلب."""

        payload = {
            key: str(value).strip().casefold()
            for key, value in (
                request
                .to_api_payload()
                .items()
            )
        }

        encoded_payload = json.dumps(
            payload,
            ensure_ascii=True,
            sort_keys=True,
            separators=(
                ",",
                ":",
            ),
        ).encode(
            "utf-8"
        )

        return hashlib.sha256(
            encoded_payload
        ).hexdigest()

    def _read_database(self) -> dict:
        """قراءة ملف الكاش بأمان."""

        if not self._cache_path.exists():
            return self._empty_database()

        try:
            content = (
                self._cache_path
                .read_text(
                    encoding="utf-8"
                )
            )

            database = json.loads(
                content
            )

        except (
            OSError,
            json.JSONDecodeError,
        ):
            return self._empty_database()

        if not isinstance(
            database,
            dict,
        ):
            return self._empty_database()

        if (
            database.get(
                "schema_version"
            )
            != self.SCHEMA_VERSION
        ):
            return self._empty_database()

        entries = database.get(
            "entries"
        )

        if not isinstance(
            entries,
            dict,
        ):
            return self._empty_database()

        return database

    def _write_database(
        self,
        database: dict,
    ) -> None:
        """حفظ الكاش بطريقة آمنة."""

        self._cache_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        temporary_path = (
            self._cache_path.with_suffix(
                ".tmp"
            )
        )

        content = json.dumps(
            database,
            ensure_ascii=False,
            indent=2,
        )

        temporary_path.write_text(
            content,
            encoding="utf-8",
        )

        temporary_path.replace(
            self._cache_path
        )

    @classmethod
    def _empty_database(
        cls,
    ) -> dict:
        """إنشاء قاعدة كاش فارغة."""

        return {
            "schema_version": (
                cls.SCHEMA_VERSION
            ),
            "entries": {},
        }

    @staticmethod
    def _default_cache_path() -> Path:
        """المسار الافتراضي داخل AppData."""

        local_app_data = os.getenv(
            "LOCALAPPDATA"
        )

        if local_app_data:
            base_path = Path(
                local_app_data
            )

        else:
            base_path = (
                Path.home()
                / "AppData"
                / "Local"
            )

        return (
            base_path
            / "PixelGuardian"
            / "cache"
            / "gaming_performance.json"
        )

    @staticmethod
    def _optional_float(
        value,
    ) -> float | None:
        """تحويل قيمة اختيارية إلى float."""

        if value is None:
            return None

        try:
            return float(
                value
            )

        except (
            TypeError,
            ValueError,
        ):
            return None