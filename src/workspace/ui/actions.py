from __future__ import annotations

from collections.abc import Iterable
from typing import Any, MutableMapping

from src.workspace.search import WorkspaceSearchCache


def finalize_onboarding_session(
    session_state: MutableMapping[str, Any],
    *,
    profile_id: str,
    selected_profile_key: str,
    keys_to_clear: Iterable[str],
    generation_key: str | None = None,
) -> None:
    """Sélectionne le profil créé et efface tout état de soumission obsolète."""

    session_state[selected_profile_key] = profile_id
    for key in keys_to_clear:
        session_state.pop(key, None)
    if generation_key is not None:
        session_state[generation_key] = int(
            session_state.get(generation_key, 0)
        ) + 1


def synchronize_profile_selection(
    session_state: MutableMapping[str, Any],
    *,
    profile_id: str | None,
    learning_result_key_prefix: str,
) -> str | None:
    """Invalide les résultats transitoires appartenant à l'ancien profil."""

    previous = WorkspaceSearchCache.activate_profile(
        session_state,
        profile_id,
    )
    normalized = str(profile_id or "").strip() or None
    if previous is not None and previous != normalized:
        session_state.pop(
            f"{learning_result_key_prefix}_{previous}",
            None,
        )
    return previous


def get_profile_learning_result(
    session_state: MutableMapping[str, Any],
    *,
    profile_id: str,
    learning_result_key_prefix: str,
) -> Any | None:
    """Refuse un résultat Learning absent ou attribué à un autre profil."""

    key = f"{learning_result_key_prefix}_{profile_id}"
    result = session_state.get(key)
    if result is None:
        return None

    if getattr(result, "profile_id", None) != profile_id:
        session_state.pop(key, None)
        return None

    return result


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
