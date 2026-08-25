from __future__ import annotations

import json
import re
import socket
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from core.models.online_gaming_performance import (
    GamingLookupStatus,
    GamingPerformanceRequest,
    GamingResultSource,
    OnlineGamingPerformanceResult,
)
from core.services.online_gaming_performance_provider import (
    OnlineGamingPerformanceProvider,
)


class FpsHqPerformanceProvider(
    OnlineGamingPerformanceProvider
):
    """جلب توقعات FPS من خدمة FPSHQ الرسمية."""

    BASE_URL = "https://fpshq.com/api/v1"
    SOURCE_URL = "https://fpshq.com/"
    DEFAULT_TIMEOUT_SECONDS = 15

    GAME_ALIASES = {
        "gta v": "Grand Theft Auto V",
        "gta 5": "Grand Theft Auto V",
        "gtav": "Grand Theft Auto V",
        "grand theft auto 5": "Grand Theft Auto V",
        "gta iv": "Grand Theft Auto IV",
        "gta 4": "Grand Theft Auto IV",
        "gta vi": "Grand Theft Auto VI",
        "gta 6": "Grand Theft Auto VI",
        "cs2": "Counter-Strike 2",
        "cs 2": "Counter-Strike 2",
        "rdr2": "Red Dead Redemption 2",
        "rdr 2": "Red Dead Redemption 2",
    }

    def __init__(
        self,
        timeout_seconds: int = (
            DEFAULT_TIMEOUT_SECONDS
        ),
    ) -> None:
        self._timeout_seconds = max(
            3,
            int(timeout_seconds),
        )

    @property
    def provider_id(self) -> str:
        """معرف داخلي ثابت للمصدر."""

        return "fpshq"

    @property
    def provider_name(self) -> str:
        """اسم المصدر الذي سيظهر للمستخدم."""

        return "FPSHQ"

    def lookup(
        self,
        request: GamingPerformanceRequest,
    ) -> OnlineGamingPerformanceResult:
        """البحث عن اللعبة والكرت ثم طلب توقع FPS."""

        try:
            return self._lookup(
                request
            )

        except FpsHqProviderError as error:
            return self.create_error_result(
                request=request,
                status=error.status,
                message=error.message,
            )

    def _lookup(
        self,
        request: GamingPerformanceRequest,
    ) -> OnlineGamingPerformanceResult:
        """تنفيذ طلب FPSHQ بعد معالجة أخطائه المعروفة."""

        game_slug = self._resolve_slug(
            query=request.game,
            item_type="game",
        )

        if not game_slug:
            return self.create_error_result(
                request=request,
                status=GamingLookupStatus.NOT_FOUND,
                message=(
                    "The selected game was not found "
                    "in the FPSHQ database."
                ),
            )

        gpu_slug = self._resolve_slug(
            query=request.gpu_query_name,
            item_type="gpu",
        )

        if not gpu_slug:
            return self.create_error_result(
                request=request,
                status=GamingLookupStatus.NOT_FOUND,
                message=(
                    "The detected graphics card was "
                    "not found in the FPSHQ database."
                ),
            )

        payload = self._request_json(
            endpoint="/fps",
            parameters={
                "game": game_slug,
                "gpu": gpu_slug,
                "res": request.resolution.value,
                "preset": (
                    request.preset.value.lower()
                ),
            },
        )

        if not isinstance(payload, dict):
            return self.create_error_result(
                request=request,
                status=GamingLookupStatus.ERROR,
                message=(
                    "FPSHQ returned an invalid "
                    "response format."
                ),
            )

        if payload.get("ok") is False:
            return self.create_error_result(
                request=request,
                status=self._status_from_payload(
                    payload
                ),
                message=self._error_message(
                    payload
                ),
            )

        average_fps = self._to_float(
            payload.get("fps")
        )

        if average_fps is None:
            return self.create_error_result(
                request=request,
                status=GamingLookupStatus.ERROR,
                message=(
                    "FPSHQ did not return a valid "
                    "average FPS value."
                ),
            )

        minimum_fps = self._to_float(
            payload.get("fps_min")
        )

        maximum_fps = self._to_float(
            payload.get("fps_max")
        )

        source_value = str(
            payload.get(
                "source",
                GamingResultSource.UNKNOWN.value,
            )
        ).strip().lower()

        try:
            result_source = GamingResultSource(
                source_value
            )
        except ValueError:
            result_source = (
                GamingResultSource.UNKNOWN
            )

        return OnlineGamingPerformanceResult(
            request=request,
            status=GamingLookupStatus.SUCCESS,
            average_fps=average_fps,
            minimum_fps=minimum_fps,
            maximum_fps=maximum_fps,
            one_percent_low_fps=None,
            verdict=str(
                payload.get("verdict", "")
            ).strip(),
            result_source=result_source,
            provider_id=self.provider_id,
            provider_name=self.provider_name,
            source_url=self.SOURCE_URL,
            message=(
                "Gaming performance data was "
                "retrieved from FPSHQ."
            ),
        )

    def _resolve_slug(
        self,
        query: str,
        item_type: str,
    ) -> str | None:
        """تحويل اسم اللعبة أو الكرت إلى slug رسمي."""

        for search_query in self._search_queries(
            query=query,
            item_type=item_type,
        ):
            payload = self._request_json(
                endpoint="/search",
                parameters={
                    "q": search_query,
                    "type": item_type,
                    "limit": 20,
                },
            )

            items = self._extract_search_items(
                payload
            )

            selected_item = self._select_best_item(
                items=items,
                query=search_query,
            )

            if selected_item is None:
                continue

            slug = selected_item.get("slug")

            if isinstance(slug, str):
                clean_slug = slug.strip()

                if clean_slug:
                    return clean_slug

        return None

    def _search_queries(
        self,
        query: str,
        item_type: str,
    ) -> tuple[str, ...]:
        """إنشاء صيغ بحث بديلة للأسماء المختصرة."""

        clean_query = " ".join(
            str(query or "").split()
        )

        if not clean_query:
            return ()

        candidates: list[str] = []

        def add(value: str) -> None:
            cleaned = " ".join(
                str(value or "").split()
            )

            if (
                cleaned
                and cleaned.casefold()
                not in {
                    item.casefold()
                    for item in candidates
                }
            ):
                candidates.append(
                    cleaned
                )

        add(clean_query)

        normalized = self._normalize_name(
            clean_query
        )

        if item_type == "game":
            alias = self.GAME_ALIASES.get(
                normalized
            )

            if alias:
                add(alias)

            if normalized.startswith("gta "):
                gta_suffix = normalized[4:].strip()

                add(
                    f"Grand Theft Auto {gta_suffix.upper()}"
                )

        if item_type == "gpu":
            without_vendor = re.sub(
                r"^(amd|nvidia|intel)\s+",
                "",
                clean_query,
                flags=re.IGNORECASE,
            ).strip()

            add(without_vendor)

            simplified = re.sub(
                r"\b(graphics|series|desktop|laptop|gpu)\b",
                " ",
                without_vendor,
                flags=re.IGNORECASE,
            )

            add(
                " ".join(
                    simplified.split()
                )
            )

            model_match = re.search(
                r"\b(?:rx|rtx|gtx|arc)\s*[a-z]?\s*\d{3,4}"
                r"(?:\s*(?:xt|xtx|super|ti))?\b",
                clean_query,
                flags=re.IGNORECASE,
            )

            if model_match:
                add(
                    model_match.group(0)
                )

        return tuple(
            candidates
        )

    @classmethod
    def _select_best_item(
        cls,
        items: list[dict[str, Any]],
        query: str,
    ) -> dict[str, Any] | None:
        """اختيار أقرب نتيجة بحث بدل أخذ أول نتيجة عشوائيًا."""

        if not items:
            return None

        normalized_query = cls._normalize_name(
            query
        )

        best_item: dict[str, Any] | None = None
        best_score = -1

        query_tokens = set(
            normalized_query.split()
        )

        for item in items:
            item_name = cls._item_name(
                item
            )

            slug = item.get("slug")

            if (
                not item_name
                or not isinstance(slug, str)
                or not slug.strip()
            ):
                continue

            normalized_name = cls._normalize_name(
                item_name
            )

            score = 0

            if normalized_name == normalized_query:
                score += 1000

            if normalized_query in normalized_name:
                score += 300

            if normalized_name in normalized_query:
                score += 200

            item_tokens = set(
                normalized_name.split()
            )

            score += len(
                query_tokens & item_tokens
            ) * 40

            if score > best_score:
                best_score = score
                best_item = item

        return best_item

    @staticmethod
    def _normalize_name(
        value: str,
    ) -> str:
        """توحيد الاسم للمقارنة والبحث."""

        normalized = re.sub(
            r"[^a-z0-9]+",
            " ",
            str(value or "").casefold(),
        )

        return " ".join(
            normalized.split()
        )

    def _request_json(
        self,
        endpoint: str,
        parameters: dict[str, object],
    ) -> Any:
        """إرسال GET وإرجاع JSON مع معالجة أخطاء الشبكة."""

        query_string = urlencode(
            parameters
        )

        url = (
            f"{self.BASE_URL}"
            f"{endpoint}"
            f"?{query_string}"
        )

        request = Request(
            url=url,
            headers={
                "Accept": "application/json",
                "User-Agent": (
                    "PixelGuardian/1.0 "
                    "(FPSHQ integration)"
                ),
            },
            method="GET",
        )

        try:
            with urlopen(
                request,
                timeout=self._timeout_seconds,
            ) as response:
                raw_body = response.read()

        except HTTPError as error:
            self._raise_http_error(
                error
            )

        except (
            URLError,
            ConnectionError,
            socket.timeout,
        ) as error:
            reason = getattr(
                error,
                "reason",
                error,
            )

            if isinstance(
                reason,
                socket.timeout,
            ):
                raise TimeoutError(
                    "FPSHQ request timed out."
                ) from error

            raise ConnectionError(
                "Could not connect to FPSHQ."
            ) from error

        try:
            return json.loads(
                raw_body.decode("utf-8")
            )

        except (
            UnicodeDecodeError,
            json.JSONDecodeError,
        ) as error:
            raise RuntimeError(
                "FPSHQ returned invalid JSON."
            ) from error

    def _raise_http_error(
        self,
        error: HTTPError,
    ) -> None:
        """تحويل HTTP status إلى أخطاء تفهمها الخدمة."""

        status_code = int(
            error.code
        )

        if status_code in {
            408,
            504,
        }:
            raise TimeoutError(
                "FPSHQ request timed out."
            ) from error

        if status_code in {
            401,
            403,
        }:
            raise FpsHqProviderError(
                status=(
                    GamingLookupStatus.UNAUTHORIZED
                ),
                message=(
                    "FPSHQ rejected the request."
                ),
            ) from error

        if status_code == 404:
            raise FpsHqProviderError(
                status=GamingLookupStatus.NOT_FOUND,
                message=(
                    "The requested FPSHQ resource "
                    "was not found."
                ),
            ) from error

        if status_code == 429:
            raise FpsHqProviderError(
                status=(
                    GamingLookupStatus.RATE_LIMITED
                ),
                message=(
                    "FPSHQ request limit was reached. "
                    "Please try again later."
                ),
            ) from error

        if 500 <= status_code <= 599:
            raise ConnectionError(
                "FPSHQ is temporarily unavailable."
            ) from error

        raise RuntimeError(
            "FPSHQ request failed with HTTP "
            f"status {status_code}."
        ) from error

    @staticmethod
    def _extract_search_items(
        payload: Any,
    ) -> list[dict[str, Any]]:
        """استخراج نتائج البحث من أي تركيب JSON شائع."""

        collected: list[dict[str, Any]] = []

        def walk(value: Any) -> None:
            if isinstance(value, list):
                for item in value:
                    walk(item)
                return

            if not isinstance(value, dict):
                return

            if isinstance(
                value.get("slug"),
                str,
            ):
                collected.append(
                    value
                )

            for nested_value in value.values():
                if isinstance(
                    nested_value,
                    (list, dict),
                ):
                    walk(
                        nested_value
                    )

        walk(payload)

        unique_items: list[
            dict[str, Any]
        ] = []

        seen_slugs: set[str] = set()

        for item in collected:
            slug = str(
                item.get("slug", "")
            ).strip()

            if (
                not slug
                or slug.casefold() in seen_slugs
            ):
                continue

            seen_slugs.add(
                slug.casefold()
            )
            unique_items.append(
                item
            )

        return unique_items

    @staticmethod
    def _item_name(
        item: dict[str, Any],
    ) -> str:
        """استخراج الاسم المعروض من نتيجة البحث."""

        for key in (
            "name",
            "title",
            "label",
        ):
            value = item.get(key)

            if isinstance(value, str):
                clean_value = value.strip()

                if clean_value:
                    return clean_value

        return ""

    @staticmethod
    def _to_float(
        value: object,
    ) -> float | None:
        """تحويل قيمة JSON إلى رقم آمن."""

        if value is None:
            return None

        try:
            return max(
                0.0,
                float(value),
            )
        except (
            TypeError,
            ValueError,
        ):
            return None

    @staticmethod
    def _status_from_payload(
        payload: dict[str, Any],
    ) -> GamingLookupStatus:
        """استنتاج حالة الخطأ من جواب FPSHQ."""

        message = FpsHqPerformanceProvider._error_message(
            payload
        ).casefold()

        if (
            "not found" in message
            or "unknown" in message
        ):
            return GamingLookupStatus.NOT_FOUND

        if (
            "rate" in message
            and "limit" in message
        ):
            return GamingLookupStatus.RATE_LIMITED

        if (
            "unauthorized" in message
            or "forbidden" in message
        ):
            return GamingLookupStatus.UNAUTHORIZED

        return GamingLookupStatus.ERROR

    @staticmethod
    def _error_message(
        payload: dict[str, Any],
    ) -> str:
        """قراءة رسالة الخطأ من JSON."""

        for key in (
            "message",
            "error",
            "detail",
        ):
            value = payload.get(key)

            if isinstance(value, str):
                clean_value = value.strip()

                if clean_value:
                    return clean_value

        return (
            "FPSHQ could not provide gaming "
            "performance data for this request."
        )


class FpsHqProviderError(RuntimeError):
    """خطأ FPSHQ يحمل حالة مفهومة للبرنامج."""

    def __init__(
        self,
        status: GamingLookupStatus,
        message: str,
    ) -> None:
        super().__init__(
            message
        )

        self.status = status
        self.message = message