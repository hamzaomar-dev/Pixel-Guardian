from __future__ import annotations

import os
from pathlib import Path

from core.models.game_library import InstalledGame


class GameActionError(RuntimeError):
    """خطأ أثناء تنفيذ أمر متعلق بلعبة."""


class GameActionService:
    """فتح مجلدات الألعاب وتشغيل الألعاب المكتشفة."""

    def open_install_folder(
        self,
        game: InstalledGame,
    ) -> None:
        """فتح مجلد تثبيت اللعبة في File Explorer."""

        install_path = self._normalize_path(
            game.install_path
        )

        if not install_path.is_dir():
            raise GameActionError(
                "The game installation folder "
                "does not exist."
            )

        self._open_target(
            str(install_path)
        )

    def launch_game(
        self,
        game: InstalledGame,
    ) -> None:
        """تشغيل اللعبة من المتجر أو الملف التنفيذي."""

        launcher_uri = (
            game.launcher_uri.strip()
            if game.launcher_uri
            else ""
        )

        if launcher_uri:
            if not self._is_supported_launcher_uri(
                launcher_uri
            ):
                raise GameActionError(
                    "The game launcher address "
                    "is not supported."
                )

            self._open_target(
                launcher_uri
            )
            return

        if game.executable_path:
            executable_path = self._normalize_path(
                game.executable_path
            )

            if executable_path.is_file():
                self._open_target(
                    str(executable_path)
                )
                return

        raise GameActionError(
            "Pixel Guardian could not find "
            "a valid way to launch this game."
        )

    @staticmethod
    def _normalize_path(
        value: str,
    ) -> Path:
        """تنظيف وتحويل مسار Windows."""

        expanded_value = os.path.expandvars(
            os.path.expanduser(
                value.strip()
            )
        )

        return Path(
            expanded_value
        )

    @staticmethod
    def _is_supported_launcher_uri(
        launcher_uri: str,
    ) -> bool:
        """السماح بعناوين تشغيل المتاجر المعروفة فقط."""

        normalized_uri = (
            launcher_uri.casefold()
        )

        return normalized_uri.startswith(
            (
                "steam://",
                "com.epicgames.launcher://",
            )
        )

    @staticmethod
    def _open_target(
        target: str,
    ) -> None:
        """فتح المسار أو عنوان المتجر بواسطة Windows."""

        startfile = getattr(
            os,
            "startfile",
            None,
        )

        if startfile is None:
            raise GameActionError(
                "This operation is only supported "
                "on Windows."
            )

        try:
            startfile(target)

        except OSError as error:
            raise GameActionError(
                f"Windows could not open the target: {error}"
            ) from error