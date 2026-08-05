from __future__ import annotations

import shutil

from src.storage.user_paths import UserStoragePaths


class ProfileDeleteService:
    """
    Supprime un profil utilisateur.
    """

    def __init__(
        self,
        storage_paths: UserStoragePaths,
    ) -> None:
        self.storage_paths = storage_paths

    def delete(
        self,
        profile_id: str,
    ) -> None:
        if not profile_id:
            raise ValueError(
                "profile_id ne peut pas être vide."
            )

        profile_directory = (
            self.storage_paths.profile_directory(
                profile_id
            )
        )

        if not profile_directory.exists():
            raise FileNotFoundError(
                profile_directory
            )

        shutil.rmtree(
            profile_directory
        )