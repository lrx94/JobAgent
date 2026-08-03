from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True, slots=True)
class WorkspaceCVItem:
    """
    Représentation d'un CV dans l'interface Workspace.
    """

    cv_id: str
    title: str
    original_filename: str
    size_bytes: int
    is_primary: bool = False

    def __post_init__(self) -> None:
        if not str(self.cv_id or "").strip():
            raise ValueError(
                "WorkspaceCVItem.cv_id est obligatoire."
            )

        if not str(self.title or "").strip():
            raise ValueError(
                "WorkspaceCVItem.title est obligatoire."
            )

        object.__setattr__(
            self,
            "cv_id",
            str(self.cv_id).strip(),
        )

        object.__setattr__(
            self,
            "title",
            str(self.title).strip(),
        )

        object.__setattr__(
            self,
            "original_filename",
            str(self.original_filename or "").strip(),
        )

        object.__setattr__(
            self,
            "size_bytes",
            max(0, int(self.size_bytes)),
        )

        object.__setattr__(
            self,
            "is_primary",
            bool(self.is_primary),
        )


@dataclass(frozen=True, slots=True)
class WorkspaceProfileItem:
    """
    Profil utilisateur accompagné de ses CV associés.
    """

    profile_id: str
    display_name: str
    config: dict[str, Any] = field(
        default_factory=dict
    )
    cvs: tuple[WorkspaceCVItem, ...] = ()

    def __post_init__(self) -> None:
        if not str(self.profile_id or "").strip():
            raise ValueError(
                "WorkspaceProfileItem.profile_id "
                "est obligatoire."
            )

        object.__setattr__(
            self,
            "profile_id",
            str(self.profile_id).strip(),
        )

        object.__setattr__(
            self,
            "display_name",
            (
                str(self.display_name or "").strip()
                or str(self.profile_id).strip()
            ),
        )

        object.__setattr__(
            self,
            "config",
            dict(self.config or {}),
        )

        object.__setattr__(
            self,
            "cvs",
            tuple(self.cvs or ()),
        )

    @property
    def primary_cv(self) -> WorkspaceCVItem | None:
        for cv in self.cvs:
            if cv.is_primary:
                return cv

        return None

    @property
    def cv_count(self) -> int:
        return len(self.cvs)


@dataclass(frozen=True, slots=True)
class WorkspaceSnapshot:
    """
    Photographie des données nécessaires à l'interface.
    """

    profiles: tuple[WorkspaceProfileItem, ...] = ()
    unassigned_cvs: tuple[WorkspaceCVItem, ...] = ()

    @property
    def profile_count(self) -> int:
        return len(self.profiles)

    @property
    def cv_count(self) -> int:
        associated_ids = {
            cv.cv_id
            for profile in self.profiles
            for cv in profile.cvs
        }

        unassigned_ids = {
            cv.cv_id
            for cv in self.unassigned_cvs
        }

        return len(
            associated_ids | unassigned_ids
        )

    def get_profile(
        self,
        profile_id: str,
    ) -> WorkspaceProfileItem | None:
        normalized = str(
            profile_id or ""
        ).strip()

        for profile in self.profiles:
            if profile.profile_id == normalized:
                return profile

        return None