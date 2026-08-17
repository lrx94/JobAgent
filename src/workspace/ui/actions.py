from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from typing import Any, MutableMapping

from src.career.search_workflow import CareerSearchResult
from src.workspace.search import (
    WorkspaceSearchCache,
    WorkspaceSearchError,
)


@dataclass(frozen=True, slots=True)
class ProfileSearchAvailability:
    result: CareerSearchResult | None
    searched: bool = False
    error: str | None = None


def run_profile_search(
    session_state: MutableMapping[str, Any],
    *,
    profile_id: str,
    search_service: Any,
    dependent_cache_keys: Iterable[str] = (),
    failure_cache_key: str | None = None,
) -> CareerSearchResult:
    """Exécute puis publie atomiquement une recherche pour un profil."""

    normalized_profile_id = str(profile_id or "").strip()
    if not normalized_profile_id:
        raise ValueError("profile_id est obligatoire.")

    result = search_service.search(normalized_profile_id)
    WorkspaceSearchCache.set(
        session_state,
        normalized_profile_id,
        result,
    )
    for key in dependent_cache_keys:
        session_state.pop(str(key), None)
    if failure_cache_key is not None:
        session_state.pop(failure_cache_key, None)
    return result


def ensure_profile_search(
    session_state: MutableMapping[str, Any],
    *,
    profile_id: str,
    search_service: Any,
    dependent_cache_keys: Iterable[str] = (),
    failure_cache_key: str,
) -> ProfileSearchAvailability:
    """Réutilise le résultat du profil ou initialise sa recherche une fois."""

    cached = WorkspaceSearchCache.get(session_state, profile_id)
    if cached is not None:
        return ProfileSearchAvailability(result=cached)

    previous_error = session_state.get(failure_cache_key)
    if previous_error is not None:
        return ProfileSearchAvailability(
            result=None,
            error=str(previous_error),
        )

    try:
        result = run_profile_search(
            session_state,
            profile_id=profile_id,
            search_service=search_service,
            dependent_cache_keys=dependent_cache_keys,
            failure_cache_key=failure_cache_key,
        )
    except WorkspaceSearchError as error:
        message = str(error)
        session_state[failure_cache_key] = message
        return ProfileSearchAvailability(result=None, error=message)

    return ProfileSearchAvailability(result=result, searched=True)


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
    """Active un profil sans mélanger ni perdre ses résultats en cache."""

    previous = WorkspaceSearchCache.activate_profile(
        session_state,
        profile_id,
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
