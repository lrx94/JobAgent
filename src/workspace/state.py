from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Any

from src.storage.user_paths import (
    UserStoragePaths,
)
from src.workspace.exceptions import (
    WorkspaceSelectionError,
)


@dataclass(frozen=True, slots=True)
class WorkspaceState:
    """
    État de navigation du Career Workspace.

    Cet objet ne dépend pas de Streamlit. Une couche UI peut
    le sérialiser dans st.session_state.
    """

    selected_profile_id: str | None = None
    selected_cv_id: str | None = None
    selected_job_id: str | None = None
    active_view: str = "overview"

    ALLOWED_VIEWS = frozenset(
        {
            "overview",
            "skills",
            "cvs",
            "jobs",
            "matching",
            "applications",
            "settings",
        }
    )

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "selected_profile_id",
            self._optional_identifier(
                self.selected_profile_id,
                "selected_profile_id",
            ),
        )

        object.__setattr__(
            self,
            "selected_cv_id",
            self._optional_identifier(
                self.selected_cv_id,
                "selected_cv_id",
            ),
        )

        object.__setattr__(
            self,
            "selected_job_id",
            self._optional_identifier(
                self.selected_job_id,
                "selected_job_id",
            ),
        )

        normalized_view = str(
            self.active_view or ""
        ).strip().casefold()

        if normalized_view not in self.ALLOWED_VIEWS:
            raise WorkspaceSelectionError(
                "Vue Workspace inconnue : "
                f"{self.active_view!r}."
            )

        object.__setattr__(
            self,
            "active_view",
            normalized_view,
        )

    @property
    def has_profile_selection(self) -> bool:
        return self.selected_profile_id is not None

    @property
    def has_cv_selection(self) -> bool:
        return self.selected_cv_id is not None

    @property
    def has_job_selection(self) -> bool:
        return self.selected_job_id is not None

    def select_profile(
        self,
        profile_id: str | None,
        clear_cv: bool = True,
    ) -> WorkspaceState:
        return replace(
            self,
            selected_profile_id=profile_id,
            selected_cv_id=(
                None
                if clear_cv
                else self.selected_cv_id
            ),
        )

    def select_cv(
        self,
        cv_id: str | None,
    ) -> WorkspaceState:
        return replace(
            self,
            selected_cv_id=cv_id,
        )

    def select_job(
        self,
        job_id: str | None,
    ) -> WorkspaceState:
        return replace(
            self,
            selected_job_id=job_id,
        )

    def change_view(
        self,
        view: str,
    ) -> WorkspaceState:
        return replace(
            self,
            active_view=view,
        )

    def clear_selection(
        self,
    ) -> WorkspaceState:
        return WorkspaceState(
            active_view=self.active_view
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "selected_profile_id": (
                self.selected_profile_id
            ),
            "selected_cv_id": self.selected_cv_id,
            "selected_job_id": (
                self.selected_job_id
            ),
            "active_view": self.active_view,
        }

    @classmethod
    def from_dict(
        cls,
        data: dict[str, Any] | None,
    ) -> WorkspaceState:
        if data is None:
            return cls()

        if not isinstance(data, dict):
            raise TypeError(
                "L'état du Workspace doit être "
                "un dictionnaire."
            )

        return cls(
            selected_profile_id=(
                data.get(
                    "selected_profile_id"
                )
            ),
            selected_cv_id=(
                data.get(
                    "selected_cv_id"
                )
            ),
            selected_job_id=(
                data.get(
                    "selected_job_id"
                )
            ),
            active_view=str(
                data.get(
                    "active_view",
                    "overview",
                )
            ),
        )

    @staticmethod
    def _optional_identifier(
        value: str | None,
        field_name: str,
    ) -> str | None:
        if value is None:
            return None

        cleaned = str(value).strip()

        if not cleaned:
            return None

        try:
            return (
                UserStoragePaths
                .validate_identifier(
                    cleaned,
                    field_name=field_name,
                )
            )
        except ValueError as error:
            raise WorkspaceSelectionError(
                str(error)
            ) from error