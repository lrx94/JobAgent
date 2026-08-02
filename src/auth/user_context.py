from __future__ import annotations

from dataclasses import dataclass

from src.auth.exceptions import (
    AccessDeniedError,
    AuthenticationRequiredError,
)
from src.auth.models import (
    CurrentUser,
    Role,
)


@dataclass(frozen=True, slots=True)
class UserContext:
    """
    Contexte utilisateur transmis aux services métier.

    Ce modèle ne dépend pas de Streamlit.
    """

    current_user: CurrentUser

    def __post_init__(self) -> None:
        if not isinstance(
            self.current_user,
            CurrentUser,
        ):
            raise TypeError(
                "current_user doit être une instance "
                "de CurrentUser."
            )

    @property
    def user_id(self) -> str:
        return self.current_user.user_id

    @property
    def subject(self) -> str:
        return self.current_user.subject

    @property
    def email(self) -> str:
        return self.current_user.email

    @property
    def display_name(self) -> str:
        return self.current_user.display_name

    @property
    def roles(self) -> tuple[Role, ...]:
        return self.current_user.roles

    @property
    def authenticated(self) -> bool:
        return self.current_user.authenticated

    @property
    def authorized(self) -> bool:
        return self.current_user.authorized

    @property
    def can_access_application(self) -> bool:
        return (
            self.current_user
            .can_access_application
        )

    def require_authenticated(self) -> None:
        if self.authenticated:
            return

        raise AuthenticationRequiredError(
            "Une authentification est requise."
        )

    def require_authorized(self) -> None:
        self.require_authenticated()

        if self.authorized:
            return

        raise AccessDeniedError(
            "L'utilisateur n'est pas autorisé "
            "à accéder à JobAgent."
        )

    def has_role(
        self,
        role: Role,
    ) -> bool:
        return self.current_user.has_role(
            role
        )

    def require_role(
        self,
        role: Role,
    ) -> None:
        self.require_authorized()

        if self.has_role(role):
            return

        raise AccessDeniedError(
            f"Le rôle {role.value!r} est requis."
        )