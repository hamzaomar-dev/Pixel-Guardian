from __future__ import annotations

import os
import re
import winreg
from datetime import datetime, timezone
from pathlib import Path

from core.models.game_library import (
    GameLibraryInventory,
    InstalledGame,
)


class SteamGameProvider:
    """اكتشاف ألعاب Steam المثبتة بطريقة قراءة فقط."""

    def scan(self) -> GameLibraryInventory:
        """فحص مكتبات Steam وإرجاع الألعاب المكتشفة."""

        steam_root = self._find_steam_root()

        if steam_root is None:
            return GameLibraryInventory(
                scanned_at=self._current_time(),
                games=(),
                scanned_sources=(),
                warnings=(
                    "Steam installation was not found.",
                ),
            )

        warnings: list[str] = []
        sources: list[str] = []

        library_roots = (
            self._find_library_roots(
                steam_root=steam_root,
                warnings=warnings,
            )
        )

        games: list[InstalledGame] = []

        for library_root in library_roots:
            steamapps_path = (
                library_root
                / "steamapps"
            )

            if not steamapps_path.is_dir():
                continue

            sources.append(
                str(steamapps_path)
            )

            try:
                manifest_files = list(
                    steamapps_path.glob(
                        "appmanifest_*.acf"
                    )
                )

            except OSError as error:
                warnings.append(
                    "Could not read Steam manifests from "
                    f"{steamapps_path}: {error}"
                )
                continue

            for manifest_path in manifest_files:
                try:
                    game = self._read_manifest(
                        manifest_path=manifest_path,
                        steamapps_path=steamapps_path,
                    )

                except Exception as error:
                    warnings.append(
                        "Could not read Steam manifest "
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
                game.game_id
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
            scanned_sources=tuple(
                dict.fromkeys(sources)
            ),
            warnings=tuple(warnings),
        )

    def _find_steam_root(
        self,
    ) -> Path | None:
        """محاولة معرفة مجلد تثبيت Steam."""

        registry_locations = (
            (
                winreg.HKEY_CURRENT_USER,
                r"Software\Valve\Steam",
            ),
            (
                winreg.HKEY_LOCAL_MACHINE,
                r"SOFTWARE\WOW6432Node\Valve\Steam",
            ),
            (
                winreg.HKEY_LOCAL_MACHINE,
                r"SOFTWARE\Valve\Steam",
            ),
        )

        for hive, key_path in registry_locations:
            try:
                with winreg.OpenKey(
                    hive,
                    key_path,
                ) as registry_key:

                    for value_name in (
                        "SteamPath",
                        "InstallPath",
                    ):
                        try:
                            value, _ = (
                                winreg.QueryValueEx(
                                    registry_key,
                                    value_name,
                                )
                            )

                        except OSError:
                            continue

                        steam_path = Path(
                            os.path.expandvars(
                                str(value)
                            )
                        )

                        if steam_path.is_dir():
                            return steam_path

            except OSError:
                continue

        possible_paths = (
            Path(
                os.environ.get(
                    "PROGRAMFILES(X86)",
                    r"C:\Program Files (x86)",
                )
            )
            / "Steam",
            Path(
                os.environ.get(
                    "PROGRAMFILES",
                    r"C:\Program Files",
                )
            )
            / "Steam",
        )

        for possible_path in possible_paths:
            if possible_path.is_dir():
                return possible_path

        return None

    def _find_library_roots(
        self,
        steam_root: Path,
        warnings: list[str],
    ) -> tuple[Path, ...]:
        """قراءة جميع مكتبات Steam الإضافية."""

        library_roots: list[Path] = [
            steam_root
        ]

        library_file = (
            steam_root
            / "steamapps"
            / "libraryfolders.vdf"
        )

        if not library_file.is_file():
            return tuple(
                library_roots
            )

        try:
            file_content = (
                library_file.read_text(
                    encoding="utf-8",
                    errors="replace",
                )
            )

        except OSError as error:
            warnings.append(
                "Could not read Steam library file: "
                f"{error}"
            )

            return tuple(
                library_roots
            )

        modern_path_pattern = re.compile(
            r'"path"\s*"([^"]+)"',
            re.IGNORECASE,
        )

        legacy_path_pattern = re.compile(
            r'"\d+"\s*"([A-Za-z]:\\\\[^"]+)"'
        )

        detected_paths = [
            match.group(1)
            for match
            in modern_path_pattern.finditer(
                file_content
            )
        ]

        detected_paths.extend(
            match.group(1)
            for match
            in legacy_path_pattern.finditer(
                file_content
            )
        )

        for detected_path in detected_paths:
            normalized_path = (
                detected_path.replace(
                    "\\\\",
                    "\\",
                )
            )

            library_path = Path(
                os.path.expandvars(
                    normalized_path
                )
            )

            if (
                library_path.is_dir()
                and library_path
                not in library_roots
            ):
                library_roots.append(
                    library_path
                )

        return tuple(
            library_roots
        )

    def _read_manifest(
        self,
        manifest_path: Path,
        steamapps_path: Path,
    ) -> InstalledGame | None:
        """قراءة ملف appmanifest للعبة واحدة."""

        manifest_content = (
            manifest_path.read_text(
                encoding="utf-8",
                errors="replace",
            )
        )

        manifest_values = dict(
            re.findall(
                r'"([^"]+)"\s*"([^"]*)"',
                manifest_content,
            )
        )

        app_id = manifest_values.get(
            "appid",
            "",
        ).strip()

        title = manifest_values.get(
            "name",
            "",
        ).strip()

        install_directory = (
            manifest_values.get(
                "installdir",
                "",
            ).strip()
        )

        if not (
            app_id
            and title
            and install_directory
        ):
            return None

        install_path = (
            steamapps_path
            / "common"
            / install_directory
        )

        try:
            size_bytes = int(
                manifest_values.get(
                    "SizeOnDisk",
                    "0",
                )
                or 0
            )

        except ValueError:
            size_bytes = 0

        return InstalledGame(
            game_id=app_id,
            title=title,
            platform="Steam",
            install_path=str(
                install_path
            ),
            size_bytes=max(
                0,
                size_bytes,
            ),
            executable_path=None,
            launcher_uri=(
                f"steam://rungameid/{app_id}"
            ),
        )

    @staticmethod
    def _current_time() -> str:
        """إرجاع وقت الفحص الحالي."""

        return datetime.now(
            timezone.utc
        ).isoformat()