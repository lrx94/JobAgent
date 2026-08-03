from __future__ import annotations

from src.auth.models import (
    CurrentUser,
    Role,
)
from src.auth.services.authorization_service import (
    AuthorizationService,
)
from src.auth.user_context import (
    UserContext,
)


class AccessController:
    """
    Point d'entrée du contrôle d'accès JobAgent.

    Il transforme un CurrentUser brut en UserContext
    autorisé, exploitable par les services métier.
    """

    def __init__(
        self,
        authorization_service: AuthorizationService,
    ) -> None:
        if not isinstance(
            authorization_service,
            AuthorizationService,
        ):
            raise TypeError(
                "authorization_service doit être "
                "une instance de AuthorizationService."
            )

        self.authorization_service = (
            authorization_service
        )

    def create_context(
        self,
        user: CurrentUser,
    ) -> UserContext:
        """
        Crée un contexte sans imposer immédiatement
        l'autorisation.

        Cette méthode est utile pour les diagnostics
        et l'affichage d'une page d'accès refusé.
        """

        authorized_user = (
            self.authorization_service.authorize(
                user
            )
        )

        return UserContext(
            current_user=authorized_user
        )

    def require_access(
        self,
        user: CurrentUser,
    ) -> UserContext:
        """
        Retourne un contexte autorisé ou lève
        AuthenticationRequiredError / AccessDeniedError.
        """

        authorized_user = (
            self.authorization_service
            .require_allowed(user)
        )

        return UserContext(
            current_user=authorized_user
        )

    def require_role(
        self,
        user: CurrentUser,
        role: Role,
    ) -> UserContext:
        """
        Exige l'accès à JobAgent et un rôle précis.
        """

        authorized_user = (
            self.authorization_service
            .require_role(
                user=user,
                role=role,
            )
        )

        return UserContext(
            current_user=authorized_user
        )