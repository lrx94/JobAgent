from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class Role(str, Enum):
    """
    Rôles applicatifs reconnus par JobAgent.
    """

    USER = "user"
    ADMIN = "admin"
    BETA_TESTER = "beta_tester"


@dataclass(frozen=True, slots=True)
class CurrentUser:
    """
    Représente l'utilisateur courant dans JobAgent.

    Ce modèle est indépendant de Streamlit et du fournisseur
    d'identité utilisé pour l'authentification.
    """

    user_id: str
    subject: str
    email: str
    display_name: str

    authenticated: bool = False
    authorized: bool = False

    roles: tuple[Role, ...] = field(
        default_factory=tuple
    )

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "user_id",
            self._clean_required(
                self.user_id,
                "user_id",
            ),
        )

        object.__setattr__(
            self,
            "subject",
            self._clean_required(
                self.subject,
                "subject",
            ),
        )

        object.__setattr__(
            self,
            "email",
            self._normalize_email(
                self.email
            ),
        )

        object.__setattr__(
            self,
            "display_name",
            self._clean_display_name(
                self.display_name,
                self.email,
            ),
        )

        object.__setattr__(
            self,
            "authenticated",
            bool(self.authenticated),
        )

        object.__setattr__(
            self,
            "authorized",
            bool(self.authorized),
        )

        object.__setattr__(
            self,
            "roles",
            self._normalize_roles(
                self.roles
            ),
        )

    @property
    def is_admin(self) -> bool:
        return Role.ADMIN in self.roles

    @property
    def is_beta_tester(self) -> bool:
        return Role.BETA_TESTER in self.roles

    @property
    def is_user(self) -> bool:
        return Role.USER in self.roles

    @property
    def can_access_application(self) -> bool:
        return (
            self.authenticated
            and self.authorized
        )

    def has_role(
        self,
        role: Role,
    ) -> bool:
        return role in self.roles

    @staticmethod
    def _clean_required(
        value: str,
        field_name: str,
    ) -> str:
        cleaned = str(
            value or ""
        ).strip()

        if not cleaned:
            raise ValueError(
                f"CurrentUser.{field_name} "
                "est obligatoire."
            )

        return cleaned

    @staticmethod
    def _normalize_email(
        value: str,
    ) -> str:
        cleaned = str(
            value or ""
        ).strip().casefold()

        if not cleaned:
            raise ValueError(
                "CurrentUser.email est obligatoire."
            )

        if "@" not in cleaned:
            raise ValueError(
                "CurrentUser.email est invalide."
            )

        return cleaned

    @staticmethod
    def _clean_display_name(
        value: str,
        email: str,
    ) -> str:
        cleaned = str(
            value or ""
        ).strip()

        if cleaned:
            return cleaned

        return email.split(
            "@",
            maxsplit=1,
        )[0]

    @staticmethod
    def _normalize_roles(
        roles: tuple[Role, ...]
        | list[Role]
        | tuple[str, ...]
        | list[str],
    ) -> tuple[Role, ...]:
        normalized: list[Role] = []
        seen: set[Role] = set()

        for value in roles or ():
            if isinstance(value, Role):
                role = value
            else:
                try:
                    role = Role(
                        str(value).strip().casefold()
                    )
                except ValueError as error:
                    raise ValueError(
                        f"Rôle inconnu : {value}"
                    ) from error

            if role in seen:
                continue

            seen.add(role)
            normalized.append(role)

        return tuple(normalized)