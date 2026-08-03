from __future__ import annotations

from pathlib import Path
from typing import Any

from src.auth.user_context import UserContext
from src.career.cv_profile_service import (
    CVProfileService,
)
from src.storage.user_paths import (
    UserStoragePaths,
)


class UserCVProfileService(CVProfileService):
    """
    Version isolée par utilisateur de CVProfileService.

    Le moteur métier reste celui de CVProfileService,
    mais son répertoire de profils est automatiquement
    limité à l'espace privé du UserContext courant.
    """

    def __init__(
        self,
        user_context: UserContext,
        storage_root: str | Path = (
            Path("data") / "users"
        ),
        create_directories: bool = True,
        **service_options: Any,
    ) -> None:
        if not isinstance(
            user_context,
            UserContext,
        ):
            raise TypeError(
                "user_context doit être une instance "
                "de UserContext."
            )

        user_context.require_authorized()

        self.user_context = user_context

        self.storage_paths = UserStoragePaths(
            user_id=user_context.user_id,
            root_directory=storage_root,
        )

        if create_directories:
            self.storage_paths.ensure_directories()

        super().__init__(
            profiles_directory=(
                self.storage_paths
                .profiles_directory
            ),
            **service_options,
        )

    @property
    def user_id(self) -> str:
        return self.user_context.user_id

   
    def assert_profile_path_owned(
        self,
        candidate: str | Path,
    ) -> Path:
        """
        Vérifie qu'un chemin appartient à l'utilisateur
        et se trouve dans son répertoire de profils.
        """

        resolved = (
            self.storage_paths
            .assert_owned_path(candidate)
        )

        profiles_root = (
            self.profiles_directory.resolve()
        )

        if (
            resolved != profiles_root
            and profiles_root
            not in resolved.parents
        ):
            raise ValueError(
                "Le chemin n'appartient pas au "
                "répertoire de profils utilisateur."
            )

        return resolved