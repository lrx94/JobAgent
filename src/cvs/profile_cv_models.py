from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime, timezone
from typing import Any

from src.storage.user_paths import (
    UserStoragePaths,
)


@dataclass(frozen=True, slots=True)
class ProfileCVAssociation:
    """
    Association entre un profil et un CV appartenant
    au même utilisateur.
    """

    user_id: str
    profile_id: str
    cv_id: str
    is_primary: bool
    created_at: datetime
    updated_at: datetime

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "user_id",
            UserStoragePaths.validate_identifier(
                self.user_id,
                field_name="user_id",
            ),
        )

        object.__setattr__(
            self,
            "profile_id",
            UserStoragePaths.validate_identifier(
                self.profile_id,
                field_name="profile_id",
            ),
        )

        object.__setattr__(
            self,
            "cv_id",
            UserStoragePaths.validate_identifier(
                self.cv_id,
                field_name="cv_id",
            ),
        )

        object.__setattr__(
            self,
            "is_primary",
            bool(self.is_primary),
        )

        object.__setattr__(
            self,
            "created_at",
            self._normalize_datetime(
                self.created_at,
                "created_at",
            ),
        )

        object.__setattr__(
            self,
            "updated_at",
            self._normalize_datetime(
                self.updated_at,
                "updated_at",
            ),
        )

        if self.updated_at < self.created_at:
            raise ValueError(
                "updated_at ne peut pas être antérieur "
                "à created_at."
            )

    @property
    def identity(self) -> str:
        return (
            f"{self.profile_id}:"
            f"{self.cv_id}"
        )

    def with_primary_status(
        self,
        is_primary: bool,
        updated_at: datetime | None = None,
    ) -> ProfileCVAssociation:
        return replace(
            self,
            is_primary=is_primary,
            updated_at=(
                updated_at
                or datetime.now(
                    timezone.utc
                )
            ),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "user_id": self.user_id,
            "profile_id": self.profile_id,
            "cv_id": self.cv_id,
            "is_primary": self.is_primary,
            "created_at": (
                self.created_at.isoformat()
            ),
            "updated_at": (
                self.updated_at.isoformat()
            ),
        }

    @classmethod
    def from_dict(
        cls,
        data: dict[str, Any],
    ) -> ProfileCVAssociation:
        if not isinstance(data, dict):
            raise TypeError(
                "data doit être un dictionnaire."
            )

        return cls(
            user_id=str(
                data.get("user_id", "")
            ),
            profile_id=str(
                data.get("profile_id", "")
            ),
            cv_id=str(
                data.get("cv_id", "")
            ),
            is_primary=bool(
                data.get("is_primary", False)
            ),
            created_at=cls._parse_datetime(
                data.get("created_at")
            ),
            updated_at=cls._parse_datetime(
                data.get("updated_at")
            ),
        )

    @staticmethod
    def _normalize_datetime(
        value: datetime,
        field_name: str,
    ) -> datetime:
        if not isinstance(value, datetime):
            raise TypeError(
                f"{field_name} doit être un datetime."
            )

        if value.tzinfo is None:
            return value.replace(
                tzinfo=timezone.utc
            )

        return value.astimezone(
            timezone.utc
        )

    @staticmethod
    def _parse_datetime(
        value: Any,
    ) -> datetime:
        text = str(
            value or ""
        ).strip()

        if not text:
            raise ValueError(
                "La date de l'association "
                "est obligatoire."
            )

        try:
            parsed = datetime.fromisoformat(
                text.replace(
                    "Z",
                    "+00:00",
                )
            )
        except ValueError as error:
            raise ValueError(
                "Date d'association invalide."
            ) from error

        if parsed.tzinfo is None:
            parsed = parsed.replace(
                tzinfo=timezone.utc
            )

        return parsed.astimezone(
            timezone.utc
        )