from __future__ import annotations

from core.models.game_readiness import (
    GameReadinessReport,
)
from infrastructure.providers.windows.game_readiness_provider import (
    WindowsGameReadinessProvider,
)


class GameReadinessService:
    """خدمة فحص جاهزية Windows للألعاب."""

    def __init__(self) -> None:
        self._provider = (
            WindowsGameReadinessProvider()
        )

    def scan_game_readiness(
        self,
    ) -> GameReadinessReport:
        """فحص إعدادات Windows المتعلقة بالألعاب."""

        return self._provider.scan()