from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


@dataclass(frozen=True, slots=True)
class CVDocument:
    """
    Métadonnées canoniques d'un CV appartenant à un utilisateur.
    """

    cv_id: str
    user_id: str
    title: str
    original_filename: str
    content_type: str
    size_bytes: int
    checksum: str
    document_path: Path
    created_at: datetime
    updated_at: datetime

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "cv_id",
            self._required_text(
                self.cv_id,
                "cv_id",
            ),
        )

        object.__setattr__(
            self,
            "user_id",
            self._required_text(
                self.user_id,
                "user_id",
            ),
        )

        object.__setattr__(
            self,
            "title",
            self._required_text(
                self.title,
                "title",
            ),
        )

        object.__setattr__(
            self,
            "original_filename",
            self._required_text(
                self.original_filename,
                "original_filename",
            ),
        )

        object.__setattr__(
            self,
            "content_type",
            self._required_text(
                self.content_type,
                "content_type",
            ).casefold(),
        )

        size_bytes = int(
            self.size_bytes
        )

        if size_bytes <= 0:
            raise ValueError(
                "CVDocument.size_bytes doit être supérieur à zéro."
            )

        object.__setattr__(
            self,
            "size_bytes",
            size_bytes,
        )

        checksum = self._required_text(
            self.checksum,
            "checksum",
        ).casefold()

        if (
            len(checksum) != 64
            or any(
                character
                not in "0123456789abcdef"
                for character in checksum
            )
        ):
            raise ValueError(
                "CVDocument.checksum doit être "
                "un SHA-256 hexadécimal."
            )

        object.__setattr__(
            self,
            "checksum",
            checksum,
        )

        object.__setattr__(
            self,
            "document_path",
            Path(
                self.document_path
            ),
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
    def filename(self) -> str:
        return self.document_path.name

    @property
    def extension(self) -> str:
        return self.document_path.suffix.casefold()

    def renamed(
        self,
        title: str,
        updated_at: datetime | None = None,
    ) -> CVDocument:
        return replace(
            self,
            title=title,
            updated_at=(
                updated_at
                or datetime.now(
                    timezone.utc
                )
            ),
        )

    def to_dict(
        self,
        include_document_path: bool = True,
    ) -> dict[str, Any]:
        data: dict[str, Any] = {
            "cv_id": self.cv_id,
            "user_id": self.user_id,
            "title": self.title,
            "original_filename": (
                self.original_filename
            ),
            "content_type": self.content_type,
            "size_bytes": self.size_bytes,
            "checksum": self.checksum,
            "created_at": (
                self.created_at.isoformat()
            ),
            "updated_at": (
                self.updated_at.isoformat()
            ),
        }

        if include_document_path:
            data["document_path"] = str(
                self.document_path
            )

        return data

    @classmethod
    def from_dict(
        cls,
        data: dict[str, Any],
        document_path: str | Path | None = None,
    ) -> CVDocument:
        if not isinstance(data, dict):
            raise TypeError(
                "data doit être un dictionnaire."
            )

        resolved_document_path = (
            Path(document_path)
            if document_path is not None
            else Path(
                str(
                    data.get(
                        "document_path",
                        "",
                    )
                )
            )
        )

        return cls(
            cv_id=str(
                data.get("cv_id", "")
            ),
            user_id=str(
                data.get("user_id", "")
            ),
            title=str(
                data.get("title", "")
            ),
            original_filename=str(
                data.get(
                    "original_filename",
                    "",
                )
            ),
            content_type=str(
                data.get(
                    "content_type",
                    "",
                )
            ),
            size_bytes=int(
                data.get(
                    "size_bytes",
                    0,
                )
            ),
            checksum=str(
                data.get(
                    "checksum",
                    "",
                )
            ),
            document_path=(
                resolved_document_path
            ),
            created_at=cls._parse_datetime(
                data.get("created_at")
            ),
            updated_at=cls._parse_datetime(
                data.get("updated_at")
            ),
        )

    @staticmethod
    def _required_text(
        value: Any,
        field_name: str,
    ) -> str:
        cleaned = str(
            value or ""
        ).strip()

        if not cleaned:
            raise ValueError(
                f"CVDocument.{field_name} est obligatoire."
            )

        return cleaned

    @staticmethod
    def _normalize_datetime(
        value: datetime,
        field_name: str,
    ) -> datetime:
        if not isinstance(
            value,
            datetime,
        ):
            raise TypeError(
                f"CVDocument.{field_name} doit être "
                "un datetime."
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
                "La date du CV est obligatoire."
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
                f"Date de CV invalide : {text}"
            ) from error

        if parsed.tzinfo is None:
            parsed = parsed.replace(
                tzinfo=timezone.utc
            )

        return parsed.astimezone(
            timezone.utc
        )