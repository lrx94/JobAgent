from __future__ import annotations

from dataclasses import dataclass, replace
from pathlib import Path

from src.auth.user_context import (
    UserContext,
)
from src.workspace.exceptions import (
    WorkspaceAccessError,
    WorkspaceResourceNotFoundError,
)
from src.workspace.services import (
    WorkspaceServices,
)
from src.workspace.state import (
    WorkspaceState,
)


@dataclass(frozen=True, slots=True)
class Workspace:
    """
    Porte d'entrée unique du Career Workspace.
    """

    user_context: UserContext
    services: WorkspaceServices
    state: WorkspaceState

    def __post_init__(self) -> None:
        if not isinstance(
            self.user_context,
            UserContext,
        ):
            raise TypeError(
                "user_context doit être "
                "un UserContext."
            )

        self.user_context.require_authorized()

        if not isinstance(
            self.services,
            WorkspaceServices,
        ):
            raise TypeError(
                "services doit être "
                "un WorkspaceServices."
            )

        if not isinstance(
            self.state,
            WorkspaceState,
        ):
            raise TypeError(
                "state doit être un WorkspaceState."
            )

        if (
            self.services.user_id
            != self.user_context.user_id
        ):
            raise WorkspaceAccessError(
                "Le Workspace et le contexte "
                "n'appartiennent pas au même "
                "utilisateur."
            )

    @property
    def user_id(self) -> str:
        return self.user_context.user_id

    @property
    def storage_directory(self) -> Path:
        return (
            self.services
            .paths
            .user_directory
        )

    @property
    def profile_service(self):
        return self.services.profile_service

    @property
    def cv_service(self):
        return self.services.cv_service

    @property
    def association_service(self):
        return (
            self.services
            .association_service
        )

    @property
    def association_repository(self):
        return (
            self.services
            .association_repository
        )

    @property
    def cv_repository(self):
        return self.services.cv_repository

    def with_state(
        self,
        state: WorkspaceState,
    ) -> Workspace:
        return replace(
            self,
            state=state,
        )

    def select_profile(
        self,
        profile_id: str,
    ) -> Workspace:
        available_profiles = set(
            self.profile_service.list_profiles()
        )

        if profile_id not in available_profiles:
            raise WorkspaceResourceNotFoundError(
                "Le profil demandé n'existe pas "
                "dans le Workspace."
            )

        return self.with_state(
            self.state.select_profile(
                profile_id
            )
        )

    def select_cv(
        self,
        cv_id: str,
    ) -> Workspace:
        if not self.cv_repository.exists(
            cv_id
        ):
            raise WorkspaceResourceNotFoundError(
                "Le CV demandé n'existe pas "
                "dans le Workspace."
            )

        return self.with_state(
            self.state.select_cv(cv_id)
        )

    def change_view(
        self,
        view: str,
    ) -> Workspace:
        return self.with_state(
            self.state.change_view(view)
        )