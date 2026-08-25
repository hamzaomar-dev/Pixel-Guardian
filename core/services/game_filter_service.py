from __future__ import annotations

from core.models.game_library import InstalledGame


class GameFilterService:
    """البحث والفلترة داخل مكتبة الألعاب."""

    @staticmethod
    def filter_games(
        games: tuple[InstalledGame, ...],
        search_text: str = "",
        platform: str = "all",
    ) -> tuple[InstalledGame, ...]:
        """فلترة الألعاب حسب النص والمتجر."""

        normalized_search = (
            search_text.strip().casefold()
        )

        normalized_platform = (
            platform.strip().casefold()
        )

        filtered_games: list[
            InstalledGame
        ] = []

        for game in games:
            if (
                normalized_platform
                and normalized_platform != "all"
                and game.platform.casefold()
                != normalized_platform
            ):
                continue

            searchable_text = " ".join(
                (
                    game.title,
                    game.platform,
                    game.install_path,
                )
            ).casefold()

            if (
                normalized_search
                and normalized_search
                not in searchable_text
            ):
                continue

            filtered_games.append(
                game
            )

        return tuple(
            sorted(
                filtered_games,
                key=lambda game: (
                    game.title.casefold(),
                    game.platform.casefold(),
                ),
            )
        )

    @staticmethod
    def available_platforms(
        games: tuple[InstalledGame, ...],
    ) -> tuple[str, ...]:
        """إرجاع المتاجر الموجودة داخل نتيجة الفحص."""

        platforms = sorted(
            {
                game.platform
                for game in games
                if game.platform.strip()
            },
            key=str.casefold,
        )

        return (
            "All",
            *platforms,
        )