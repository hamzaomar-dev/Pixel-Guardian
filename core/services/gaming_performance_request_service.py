from __future__ import annotations

from core.models.online_gaming_performance import (
    GamingPerformanceRequest,
    GamingPreset,
    GamingResolution,
)
from core.services.hardware_name_parser import (
    HardwareNameParser,
)
from core.services.inventory_service import (
    InventoryService,
)


class GamingPerformanceRequestBuildError(
    RuntimeError
):
    """فشل تجهيز طلب تقييم أداء لعبة."""


class GamingPerformanceRequestService:
    """
    يقرأ CPU وGPU من الجهاز الحالي،
    ثم يجهز طلب الأداء الخاص باللعبة.
    """

    def __init__(
        self,
        inventory_service: InventoryService | None = None,
    ) -> None:
        self._inventory_service = (
            inventory_service
            or InventoryService()
        )

    def build(
        self,
        game: str,
        resolution: GamingResolution = (
            GamingResolution.FULL_HD
        ),
        preset: GamingPreset = (
            GamingPreset.HIGH
        ),
    ) -> GamingPerformanceRequest:
        """إنشاء طلب باستخدام قطع الجهاز الحالية."""

        game_name = str(
            game or ""
        ).strip()

        if not game_name:
            raise GamingPerformanceRequestBuildError(
                "The game name cannot be empty."
            )

        basic_result = (
            self._inventory_service
            .get_basic_system_info()
        )

        if (
            not basic_result.success
            or basic_result.data is None
        ):
            raise GamingPerformanceRequestBuildError(
                "Processor information could not "
                "be detected."
            )

        identity_result = (
            self._inventory_service
            .get_hardware_identity()
        )

        if (
            not identity_result.success
            or identity_result.data is None
        ):
            raise GamingPerformanceRequestBuildError(
                "Graphics card information could not "
                "be detected."
            )

        basic_info = basic_result.data

        cpu = HardwareNameParser.parse_cpu(
            raw_name=str(
                basic_info.cpu_name or ""
            ),
            physical_cores=(
                basic_info.physical_cores
            ),
            logical_cores=(
                basic_info.logical_cores
            ),
        )

        gpu_name = self._select_primary_gpu_name(
            identity_result.data.gpus
        )

        if not gpu_name:
            raise GamingPerformanceRequestBuildError(
                "No usable graphics card was detected."
            )

        gpu = HardwareNameParser.parse_gpu(
            raw_name=gpu_name
        )

        return GamingPerformanceRequest(
            cpu=cpu,
            gpu=gpu,
            game=game_name,
            resolution=resolution,
            preset=preset,
        )

    @classmethod
    def _select_primary_gpu_name(
        cls,
        gpus,
    ) -> str:
        """
        اختيار أفضل كرت حقيقي مكتشف.

        يعطي أولوية للكرت المنفصل عند وجود
        كرت مدمج وكرت منفصل في نفس الجهاز.
        """

        candidates: list[
            tuple[int, int, str]
        ] = []

        for index, gpu in enumerate(
            gpus or ()
        ):
            gpu_name = str(
                getattr(
                    gpu,
                    "name",
                    "",
                )
                or ""
            ).strip()

            if not gpu_name:
                continue

            if cls._is_virtual_gpu(
                gpu_name
            ):
                continue

            priority = cls._gpu_priority(
                gpu_name
            )

            candidates.append(
                (
                    priority,
                    -index,
                    gpu_name,
                )
            )

        if not candidates:
            return ""

        _priority, _index, gpu_name = max(
            candidates,
            key=lambda item: (
                item[0],
                item[1],
            ),
        )

        return gpu_name

    @staticmethod
    def _is_virtual_gpu(
        gpu_name: str,
    ) -> bool:
        """استبعاد كروت العرض الوهمية."""

        normalized_name = (
            gpu_name.casefold()
        )

        ignored_names = (
            "microsoft basic display",
            "microsoft remote display",
            "remote display",
            "virtual display",
            "parsec virtual",
            "vmware svga",
            "hyper-v",
            "citrix",
        )

        return any(
            ignored_name in normalized_name
            for ignored_name in ignored_names
        )

    @staticmethod
    def _gpu_priority(
        gpu_name: str,
    ) -> int:
        """تحديد أولوية اختيار كرت الشاشة."""

        normalized_name = (
            gpu_name.casefold()
        )

        discrete_markers = (
            "geforce rtx",
            "geforce gtx",
            "nvidia rtx",
            "nvidia gtx",
            "radeon rx",
            "intel arc a",
            "intel arc b",
            "quadro",
        )

        if any(
            marker in normalized_name
            for marker in discrete_markers
        ):
            return 100

        integrated_markers = (
            "intel uhd",
            "intel hd graphics",
            "intel iris",
            "radeon graphics",
            "vega graphics",
        )

        if any(
            marker in normalized_name
            for marker in integrated_markers
        ):
            return 30

        return 60