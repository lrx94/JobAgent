from __future__ import annotations

from src.cvs.exceptions import (
    CVStillInUseError,
)
from src.cvs.models import (
    CVDocument,
)
from src.cvs.profile_cv_models import (
    ProfileCVAssociation,
)
from src.cvs.profile_cv_repository import (
    ProfileCVRepository,
)
from src.cvs.repository import (
    CVRepository,
)


class ProfileCVService:
    """
    Service métier des associations profils/CV.
    """

    def __init__(
        self,
        association_repository: (
            ProfileCVRepository
        ),
        cv_repository: CVRepository,
    ) -> None:
        if not isinstance(
            association_repository,
            ProfileCVRepository,
        ):
            raise TypeError(
                "association_repository doit être "
                "un ProfileCVRepository."
            )

        if not isinstance(
            cv_repository,
            CVRepository,
        ):
            raise TypeError(
                "cv_repository doit être "
                "un CVRepository."
            )

        if (
            association_repository.user_id
            != cv_repository.user_id
        ):
            raise ValueError(
                "Les repositories doivent appartenir "
                "au même utilisateur."
            )

        self.association_repository = (
            association_repository
        )

        self.cv_repository = cv_repository

    @property
    def user_id(self) -> str:
        return self.cv_repository.user_id

    def attach_cv(
        self,
        profile_id: str,
        cv_id: str,
        is_primary: bool = False,
    ) -> ProfileCVAssociation:
        return (
            self.association_repository
            .attach(
                profile_id=profile_id,
                cv_id=cv_id,
                is_primary=is_primary,
            )
        )

    def detach_cv(
        self,
        profile_id: str,
        cv_id: str,
    ) -> ProfileCVAssociation:
        return (
            self.association_repository
            .detach(
                profile_id=profile_id,
                cv_id=cv_id,
            )
        )

    def set_primary_cv(
        self,
        profile_id: str,
        cv_id: str,
    ) -> ProfileCVAssociation:
        return (
            self.association_repository
            .set_primary(
                profile_id=profile_id,
                cv_id=cv_id,
            )
        )

    def list_profile_associations(
        self,
        profile_id: str,
    ) -> list[ProfileCVAssociation]:
        return (
            self.association_repository
            .list_for_profile(profile_id)
        )

    def list_profile_cvs(
        self,
        profile_id: str,
    ) -> list[CVDocument]:
        documents: list[CVDocument] = []

        for association in (
            self.list_profile_associations(
                profile_id
            )
        ):
            documents.append(
                self.cv_repository.get(
                    association.cv_id
                )
            )

        return documents

    def list_profiles_for_cv(
        self,
        cv_id: str,
    ) -> list[str]:
        return [
            item.profile_id
            for item in (
                self.association_repository
                .list_for_cv(cv_id)
            )
        ]

    def get_primary_cv(
        self,
        profile_id: str,
    ) -> CVDocument | None:
        association = (
            self.association_repository
            .get_primary(profile_id)
        )

        if association is None:
            return None

        return self.cv_repository.get(
            association.cv_id
        )

    def delete_cv(
        self,
        cv_id: str,
        force: bool = False,
    ) -> CVDocument:
        associations = (
            self.association_repository
            .list_for_cv(cv_id)
        )

        if associations and not force:
            profile_ids = sorted(
                {
                    item.profile_id
                    for item in associations
                }
            )

            raise CVStillInUseError(
                "Le CV est encore associé aux profils : "
                + ", ".join(profile_ids)
            )

        if force:
            for association in list(
                associations
            ):
                self.association_repository.detach(
                    profile_id=(
                        association.profile_id
                    ),
                    cv_id=association.cv_id,
                )

        return self.cv_repository.delete(
            cv_id
        )