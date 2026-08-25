from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class InstalledGame:
    """بيانات لعبة مثبتة على الجهاز."""

    game_id: str
    title: str
    platform: str
    install_path: str
    size_bytes: int = 0
    executable_path: str | None = None
    launcher_uri: str | None = None

    @property
    def size_mb(self) -> float:
        """حجم اللعبة بالميجابايت."""

        return self.size_bytes / (
            1024 ** 2
        )

    @property
    def size_gb(self) -> float:
        """حجم اللعبة بالجيجابايت."""

        return self.size_bytes / (
            1024 ** 3
        )


@dataclass(frozen=True, slots=True)
class GameLibraryInventory:
    """نتيجة فحص مكتبة الألعاب."""

    scanned_at: str

    games: tuple[
        InstalledGame,
        ...
    ]

    scanned_sources: tuple[
        str,
        ...
    ] = ()

    warnings: tuple[
        str,
        ...
    ] = ()

    @property
    def total_games(self) -> int:
        """إجمالي الألعاب المكتشفة."""

        return len(
            self.games
        )

    @property
    def steam_games(self) -> int:
        """عدد ألعاب Steam."""

        return sum(
            1
            for game in self.games
            if game.platform.lower()
            == "steam"
        )

    @property
    def epic_games(self) -> int:
        """عدد ألعاب Epic Games."""

        return sum(
            1
            for game in self.games
            if game.platform.lower()
            == "epic games"
        )

    @property
    def total_size_bytes(self) -> int:
        """إجمالي أحجام الألعاب المكتشفة."""

        return sum(
            max(
                0,
                game.size_bytes,
            )
            for game in self.games
        )