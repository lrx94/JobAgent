from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from src.auth.user_context import (
    UserContext,
)
from src.cvs.exceptions import (
    CVNotFoundError,
    CVStorageError,
    ProfileCVAssociationError,
    ProfileCVAssociationNotFoundError,
    ProfileNotFoundError,
)
from src.cvs.profile_cv_models import (
    ProfileCVAssociation,
)
from src.cvs.repository import (
    CVRepository,
)
from src.storage.user_paths import (
    UserStoragePaths,
)


class ProfileCVRepository:
    """
    Repository d'associations profils/CV isolé
    par utilisateur.

    Le fichier JSON est privé à l'utilisateur courant.
    """

    FILENAME = "profile_cv_associations.json"
    FORMAT_VERSION = 1

    def __init__(
        self,
        user_context: UserContext,
        cv_repository: CVRepository,
        storage_root: str | Path = (
            Path("data")
            / "users"
        ),
        create_directories: bool = True,
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

        if not isinstance(
            cv_repository,
            CVRepository,
        ):
            raise TypeError(
                "cv_repository doit être une instance "
                "de CVRepository."
            )

        if (
            cv_repository.user_id
            != user_context.user_id
        ):
            raise ProfileCVAssociationError(
                "Le repository CV n'appartient pas "
                "au même utilisateur."
            )

        self.user_context = user_context
        self.cv_repository = cv_repository

        self.paths = UserStoragePaths(
            user_id=user_context.user_id,
            root_directory=storage_root,
        )

        if create_directories:
            self.paths.ensure_directories()

    @property
    def user_id(self) -> str:
        return self.user_context.user_id

    @property
    def associations_file(self) -> Path:
        return (
            self.paths.user_directory
            / self.FILENAME
        ).resolve()

    def attach(
        self,
        profile_id: str,
        cv_id: str,
        is_primary: bool = False,
    ) -> ProfileCVAssociation:
        normalized_profile_id = (
            self._require_profile(
                profile_id
            )
        )

        document = self.cv_repository.get(
            cv_id
        )

        associations = self.list_all()

        profile_associations_before = [
            item
            for item in associations
            if (
                item.profile_id
                == normalized_profile_id
            )
        ]

        existing = next(
            (
                item
                for item in associations
                if (
                    item.profile_id
                    == normalized_profile_id
                    and item.cv_id
                    == document.cv_id
                )
            ),
            None,
        )

        now = datetime.now(
            timezone.utc
        )

        if existing is None:
            association = ProfileCVAssociation(
                user_id=self.user_id,
                profile_id=(
                    normalized_profile_id
                ),
                cv_id=document.cv_id,
                is_primary=False,
                created_at=now,
                updated_at=now,
            )

            associations.append(
                association
            )
        else:
            association = existing

        must_be_primary = (
            is_primary
            or not profile_associations_before
        )

        if must_be_primary:
            associations = (
                self._set_primary_in_collection(
                    associations=associations,
                    profile_id=(
                        normalized_profile_id
                    ),
                    cv_id=document.cv_id,
                )
            )

            association = next(
                item
                for item in associations
                if (
                    item.profile_id
                    == normalized_profile_id
                    and item.cv_id
                    == document.cv_id
                )
            )

        self._write_all(
            associations
        )

        return association

    def detach(
        self,
        profile_id: str,
        cv_id: str,
    ) -> ProfileCVAssociation:
        normalized_profile_id = (
            UserStoragePaths
            .validate_identifier(
                profile_id,
                field_name="profile_id",
            )
        )

        normalized_cv_id = (
            UserStoragePaths
            .validate_identifier(
                cv_id,
                field_name="cv_id",
            )
        )

        associations = self.list_all()

        removed = next(
            (
                item
                for item in associations
                if (
                    item.profile_id
                    == normalized_profile_id
                    and item.cv_id
                    == normalized_cv_id
                )
            ),
            None,
        )

        if removed is None:
            raise (
                ProfileCVAssociationNotFoundError(
                    "L'association profil/CV "
                    "n'existe pas."
                )
            )

        remaining = [
            item
            for item in associations
            if item.identity != removed.identity
        ]

        profile_associations = [
            item
            for item in remaining
            if (
                item.profile_id
                == normalized_profile_id
            )
        ]

        if (
            removed.is_primary
            and profile_associations
        ):
            replacement = min(
                profile_associations,
                key=lambda item: (
                    item.created_at,
                    item.cv_id,
                ),
            )

            remaining = [
                (
                    item.with_primary_status(
                        item.identity
                        == replacement.identity
                    )
                    if (
                        item.profile_id
                        == normalized_profile_id
                    )
                    else item
                )
                for item in remaining
            ]

        self._write_all(
            remaining
        )

        return removed

    def set_primary(
        self,
        profile_id: str,
        cv_id: str,
    ) -> ProfileCVAssociation:
        normalized_profile_id = (
            self._require_profile(
                profile_id
            )
        )

        self.cv_repository.get(
            cv_id
        )

        associations = self.list_all()

        target = next(
            (
                item
                for item in associations
                if (
                    item.profile_id
                    == normalized_profile_id
                    and item.cv_id
                    == cv_id
                )
            ),
            None,
        )

        if target is None:
            raise (
                ProfileCVAssociationNotFoundError(
                    "Le CV doit être associé au profil "
                    "avant de devenir principal."
                )
            )

        updated = self._set_primary_in_collection(
            associations=associations,
            profile_id=normalized_profile_id,
            cv_id=cv_id,
        )

        self._write_all(
            updated
        )

        return next(
            item
            for item in updated
            if (
                item.profile_id
                == normalized_profile_id
                and item.cv_id == cv_id
            )
        )

    def list_all(
        self,
    ) -> list[ProfileCVAssociation]:
        if not self.associations_file.exists():
            return []

        try:
            data = json.loads(
                self.associations_file.read_text(
                    encoding="utf-8"
                )
            )
        except json.JSONDecodeError as error:
            raise CVStorageError(
                "Le fichier d'associations "
                "contient un JSON invalide."
            ) from error
        except OSError as error:
            raise CVStorageError(
                "Impossible de lire les associations."
            ) from error

        if not isinstance(data, dict):
            raise CVStorageError(
                "Le format des associations "
                "est invalide."
            )

        values = data.get(
            "associations",
            [],
        )

        if not isinstance(values, list):
            raise CVStorageError(
                "Le champ associations doit "
                "être une liste."
            )

        result: list[
            ProfileCVAssociation
        ] = []

        for value in values:
            if not isinstance(value, dict):
                continue

            association = (
                ProfileCVAssociation
                .from_dict(value)
            )

            if (
                association.user_id
                != self.user_id
            ):
                continue

            result.append(
                association
            )

        result.sort(
            key=lambda item: (
                item.profile_id,
                not item.is_primary,
                item.created_at,
                item.cv_id,
            )
        )

        return result

    def list_for_profile(
        self,
        profile_id: str,
        associations: (
            list[ProfileCVAssociation]
            | None
        ) = None,
    ) -> list[ProfileCVAssociation]:
        normalized_profile_id = (
            UserStoragePaths
            .validate_identifier(
                profile_id,
                field_name="profile_id",
            )
        )

        source = (
            associations
            if associations is not None
            else self.list_all()
        )

        return [
            item
            for item in source
            if (
                item.profile_id
                == normalized_profile_id
            )
        ]

    def list_for_cv(
        self,
        cv_id: str,
    ) -> list[ProfileCVAssociation]:
        normalized_cv_id = (
            UserStoragePaths
            .validate_identifier(
                cv_id,
                field_name="cv_id",
            )
        )

        return [
            item
            for item in self.list_all()
            if item.cv_id == normalized_cv_id
        ]

    def get_primary(
        self,
        profile_id: str,
    ) -> ProfileCVAssociation | None:
        for association in (
            self.list_for_profile(
                profile_id
            )
        ):
            if association.is_primary:
                return association

        return None

    def is_cv_in_use(
        self,
        cv_id: str,
    ) -> bool:
        return bool(
            self.list_for_cv(cv_id)
        )

    def remove_profile(
        self,
        profile_id: str,
    ) -> list[ProfileCVAssociation]:
        normalized_profile_id = (
            UserStoragePaths
            .validate_identifier(
                profile_id,
                field_name="profile_id",
            )
        )

        associations = self.list_all()

        removed = [
            item
            for item in associations
            if (
                item.profile_id
                == normalized_profile_id
            )
        ]

        remaining = [
            item
            for item in associations
            if (
                item.profile_id
                != normalized_profile_id
            )
        ]

        self._write_all(
            remaining
        )

        return removed

    def _require_profile(
        self,
        profile_id: str,
    ) -> str:
        normalized_profile_id = (
            UserStoragePaths
            .validate_identifier(
                profile_id,
                field_name="profile_id",
            )
        )

        profile_directory = (
            self.paths.profile_directory(
                normalized_profile_id
            )
        )

        config_file = (
            self.paths.profile_config_file(
                normalized_profile_id
            )
        )

        if (
            not profile_directory.is_dir()
            or not config_file.is_file()
        ):
            raise ProfileNotFoundError(
                "Le profil demandé n'existe pas."
            )

        return normalized_profile_id

    def _write_all(
        self,
        associations: list[
            ProfileCVAssociation
        ],
    ) -> None:
        self.paths.assert_owned_path(
            self.associations_file
        )

        payload: dict[str, Any] = {
            "version": self.FORMAT_VERSION,
            "user_id": self.user_id,
            "associations": [
                item.to_dict()
                for item in associations
            ],
        }

        temporary_file = (
            self.associations_file
            .with_suffix(".tmp")
        )

        try:
            temporary_file.write_text(
                json.dumps(
                    payload,
                    ensure_ascii=False,
                    indent=2,
                    sort_keys=True,
                )
                + "\n",
                encoding="utf-8",
            )

            temporary_file.replace(
                self.associations_file
            )
        except OSError as error:
            temporary_file.unlink(
                missing_ok=True
            )

            raise CVStorageError(
                "Impossible d'enregistrer "
                "les associations profils/CV."
            ) from error

    @staticmethod
    def _set_primary_in_collection(
        associations: list[
            ProfileCVAssociation
        ],
        profile_id: str,
        cv_id: str,
    ) -> list[ProfileCVAssociation]:
        now = datetime.now(
            timezone.utc
        )

        return [
            (
                item.with_primary_status(
                    is_primary=(
                        item.cv_id == cv_id
                    ),
                    updated_at=now,
                )
                if item.profile_id == profile_id
                else item
            )
            for item in associations
        ]