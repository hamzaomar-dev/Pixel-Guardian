from __future__ import annotations

from datetime import datetime, timezone

from core.models.game_library import (
    GameLibraryInventory,
    InstalledGame,
)
from infrastructure.providers.windows.epic_game_provider import (
    EpicGameProvider,
)
from infrastructure.providers.windows.steam_game_provider import (
    SteamGameProvider,
)


class GameLibraryService:
    """جمع الألعاب المثبتة من المتاجر المدعومة."""

    def __init__(self) -> None:
        self._steam_provider = (
            SteamGameProvider()
        )

        self._epic_provider = (
            EpicGameProvider()
        )

    def scan_installed_games(
        self,
    ) -> GameLibraryInventory:
        """فحص Steam وEpic وإرجاع مكتبة موحدة."""

        steam_inventory = (
            self._steam_provider.scan()
        )

        epic_inventory = (
            self._epic_provider.scan()
        )

        all_games = (
            list(steam_inventory.games)
            + list(epic_inventory.games)
        )

        unique_games: dict[
            tuple[str, str],
            InstalledGame,
        ] = {}

        for game in all_games:
            key = (
                game.platform.casefold(),
                game.game_id.casefold(),
            )

            unique_games[key] = game

        ordered_games = sorted(
            unique_games.values(),
            key=lambda game: (
                game.title.casefold(),
                game.platform.casefold(),
            ),
        )

        scanned_sources = tuple(
            dict.fromkeys(
                steam_inventory.scanned_sources
                + epic_inventory.scanned_sources
            )
        )

        warnings = tuple(
            steam_inventory.warnings
            + epic_inventory.warnings
        )

        return GameLibraryInventory(
            scanned_at=datetime.now(
                timezone.utc
            ).isoformat(),
            games=tuple(
                ordered_games
            ),
            scanned_sources=(
                scanned_sources
            ),
            warnings=warnings,
        )