from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path

from core.models.game_library import (
    GameLibraryInventory,
    InstalledGame,
)


class EpicGameProvider:
    """اكتشاف ألعاب Epic Games المثبتة بطريقة قراءة فقط."""

    def scan(self) -> GameLibraryInventory:
        """فحص ملفات Epic Manifest وإرجاع الألعاب المكتشفة."""

        manifests_directory = (
            self._find_manifests_directory()
        )

        if manifests_directory is None:
            return GameLibraryInventory(
                scanned_at=self._current_time(),
                games=(),
                scanned_sources=(),
                warnings=(
                    "Epic Games manifest directory "
                    "was not found.",
                ),
            )

        games: list[InstalledGame] = []
        warnings: list[str] = []

        try:
            manifest_files = list(
                manifests_directory.glob(
                    "*.item"
                )
            )

        except OSError as error:
            return GameLibraryInventory(
                scanned_at=self._current_time(),
                games=(),
                scanned_sources=(
                    str(manifests_directory),
                ),
                warnings=(
                    "Could not list Epic Games "
                    f"manifest files: {error}",
                ),
            )

        for manifest_path in manifest_files:
            try:
                game = self._read_manifest(
                    manifest_path
                )

            except Exception as error:
                warnings.append(
                    "Could not read Epic Games manifest "
                    f"{manifest_path.name}: {error}"
                )
                continue

            if game is not None:
                games.append(game)

        unique_games: dict[
            str,
            InstalledGame,
        ] = {}

        for game in games:
            unique_games[
                game.game_id.casefold()
            ] = game

        ordered_games = sorted(
            unique_games.values(),
            key=lambda game: (
                game.title.casefold()
            ),
        )

        return GameLibraryInventory(
            scanned_at=self._current_time(),
            games=tuple(ordered_games),
            scanned_sources=(
                str(manifests_directory),
            ),
            warnings=tuple(warnings),
        )

    @staticmethod
    def _find_manifests_directory(
    ) -> Path | None:
        """تحديد مجلد ملفات Epic Games Manifest."""

        program_data = Path(
            os.environ.get(
                "PROGRAMDATA",
                r"C:\ProgramData",
            )
        )

        manifests_directory = (
            program_data
            / "Epic"
            / "EpicGamesLauncher"
            / "Data"
            / "Manifests"
        )

        if manifests_directory.is_dir():
            return manifests_directory

        return None

    def _read_manifest(
        self,
        manifest_path: Path,
    ) -> InstalledGame | None:
        """قراءة ملف Manifest خاص بلعبة واحدة."""

        manifest_content = (
            manifest_path.read_text(
                encoding="utf-8-sig",
                errors="replace",
            )
        )

        payload = json.loads(
            manifest_content
        )

        if not isinstance(
            payload,
            dict,
        ):
            return None

        title = str(
            payload.get(
                "DisplayName",
                "",
            )
        ).strip()

        install_location = str(
            payload.get(
                "InstallLocation",
                "",
            )
        ).strip()

        app_name = str(
            payload.get(
                "AppName",
                "",
            )
        ).strip()

        catalog_item_id = str(
            payload.get(
                "CatalogItemId",
                "",
            )
        ).strip()

        if not (
            title
            and install_location
        ):
            return None

        if self._is_incomplete_install(
            payload
        ):
            return None

        if not self._is_application(
            payload
        ):
            return None

        game_id = (
            catalog_item_id
            or app_name
            or manifest_path.stem
        )

        install_path = Path(
            os.path.expandvars(
                install_location
            )
        )

        launch_executable = str(
            payload.get(
                "LaunchExecutable",
                "",
            )
        ).strip()

        executable_path: str | None = None

        if launch_executable:
            executable_path = str(
                install_path
                / launch_executable
            )

        size_bytes = self._read_size(
            payload
        )

        return InstalledGame(
            game_id=game_id,
            title=title,
            platform="Epic Games",
            install_path=str(
                install_path
            ),
            size_bytes=size_bytes,
            executable_path=(
                executable_path
            ),
            launcher_uri=None,
        )

    @staticmethod
    def _is_incomplete_install(
        payload: dict,
    ) -> bool:
        """معرفة هل تثبيت اللعبة غير مكتمل."""

        value = payload.get(
            "bIsIncompleteInstall",
            False,
        )

        if isinstance(
            value,
            bool,
        ):
            return value

        return str(value).strip().casefold() in {
            "true",
            "1",
            "yes",
        }

    @staticmethod
    def _is_application(
        payload: dict,
    ) -> bool:
        """استبعاد الملفات التي ليست تطبيقات كاملة."""

        value = payload.get(
            "bIsApplication",
            True,
        )

        if isinstance(
            value,
            bool,
        ):
            return value

        return str(value).strip().casefold() not in {
            "false",
            "0",
            "no",
        }

    @staticmethod
    def _read_size(
        payload: dict,
    ) -> int:
        """قراءة الحجم المسجل داخل Manifest."""

        possible_values = (
            payload.get(
                "InstallSize",
                0,
            ),
            payload.get(
                "DownloadSize",
                0,
            ),
        )

        for value in possible_values:
            try:
                parsed_size = int(
                    value or 0
                )

            except (
                TypeError,
                ValueError,
            ):
                continue

            if parsed_size > 0:
                return parsed_size

        return 0

    @staticmethod
    def _current_time() -> str:
        """إرجاع وقت الفحص الحالي."""

        return datetime.now(
            timezone.utc
        ).isoformat()