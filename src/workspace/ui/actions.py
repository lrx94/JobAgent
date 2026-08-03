from __future__ import annotations

from collections.abc import Iterable


class WorkspaceCVActions:
    """
    Façade légère pour les actions CV du Career Workspace.
    """

    def __init__(
        self,
        *,
        cv_service,
        association_service,
        association_repository,
        profile_service,
    ) -> None:
        self.cv_service = cv_service
        self.association_service = association_service
        self.association_repository = association_repository
        self.profile_service = profile_service

    def rename_cv(
        self,
        cv_id: str,
        new_title: str,
    ):
        return self.cv_service.rename_cv(
            cv_id,
            new_title,
        )

    def delete_cv(
        self,
        cv_id: str,
        *,
        force: bool = False,
    ):
        return self.association_service.delete_cv(
            cv_id,
            force=force,
        )

    def attach_cv(
        self,
        *,
        profile_id: str,
        cv_id: str,
        is_primary: bool = False,
    ):
        return self.association_service.attach_cv(
            profile_id=profile_id,
            cv_id=cv_id,
            is_primary=is_primary,
        )

    def detach_cv(
        self,
        *,
        profile_id: str,
        cv_id: str,
    ):
        return self.association_service.detach_cv(
            profile_id=profile_id,
            cv_id=cv_id,
        )

    def set_primary_cv(
        self,
        *,
        profile_id: str,
        cv_id: str,
    ):
        return self.association_service.set_primary_cv(
            profile_id=profile_id,
            cv_id=cv_id,
        )

    def associations_for_cv(
        self,
        cv_id: str,
    ):
        return list(
            self.association_repository.list_for_cv(
                cv_id
            )
        )

    def available_profile_ids(
        self,
        associated_profile_ids: Iterable[str],
    ) -> list[str]:
        associated = {
            str(profile_id)
            for profile_id in associated_profile_ids
        }

        return [
            profile_id
            for profile_id
            in self.profile_service.list_profiles()
            if profile_id not in associated
        ]
