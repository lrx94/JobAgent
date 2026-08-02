from __future__ import annotations

from dataclasses import replace

from src.auth.exceptions import (
    AccessDeniedError,
    AuthenticationRequiredError,
)
from src.auth.models import (
    CurrentUser,
    Role,
)
from src.auth.repositories.authorization_repository import (
    AuthorizationRepository,
)


class AuthorizationService:
    """
    Applique les règles métier d'autorisation.

    Ce service ne connaît ni Streamlit, ni Google,
    ni la technologie de stockage utilisée.
    """

    def __init__(
        self,
        repository: AuthorizationRepository,
    ) -> None:
        if not isinstance(
            repository,
            AuthorizationRepository,
        ):
            raise TypeError(
                "repository doit respecter "
                "AuthorizationRepository."
            )

        self.repository = repository

    def is_allowed(
        self,
        user: CurrentUser,
    ) -> bool:
        self._require_user_type(user)

        if not user.authenticated:
            return False

        return self.repository.is_allowed_email(
            user.email
        )

    def authorize(
        self,
        user: CurrentUser,
    ) -> CurrentUser:
        """
        Retourne une nouvelle instance de CurrentUser
        avec le statut authorized calculé.
        """

        self._require_user_type(user)

        return replace(
            user,
            authorized=self.is_allowed(user),
        )

    def require_allowed(
        self,
        user: CurrentUser,
    ) -> CurrentUser:
        """
        Retourne l'utilisateur autorisé ou lève
        une exception métier explicite.
        """

        self._require_user_type(user)

        if not user.authenticated:
            raise AuthenticationRequiredError(
                "Une authentification est requise."
            )

        authorized_user = self.authorize(
            user
        )

        if not authorized_user.authorized:
            raise AccessDeniedError(
                "Ce compte n'est pas autorisé "
                "à accéder à JobAgent."
            )

        return authorized_user

    def has_role(
        self,
        user: CurrentUser,
        role: Role,
    ) -> bool:
        self._require_user_type(user)
        self._require_role_type(role)

        return user.has_role(role)

    def require_role(
        self,
        user: CurrentUser,
        role: Role,
    ) -> CurrentUser:
        authorized_user = self.require_allowed(
            user
        )

        self._require_role_type(role)

        if not authorized_user.has_role(role):
            raise AccessDeniedError(
                f"Le rôle {role.value!r} est requis."
            )

        return authorized_user

    @staticmethod
    def _require_user_type(
        user: CurrentUser,
    ) -> None:
        if not isinstance(
            user,
            CurrentUser,
        ):
            raise TypeError(
                "user doit être une instance "
                "de CurrentUser."
            )

    @staticmethod
    def _require_role_type(
        role: Role,
    ) -> None:
        if not isinstance(role, Role):
            raise TypeError(
                "role doit être une instance de Role."
            )