from __future__ import annotations


class AuthenticationError(Exception):
    """
    Erreur de base du domaine d'authentification.
    """


class AuthenticationRequiredError(
    AuthenticationError
):
    """
    Aucun utilisateur authentifié n'est disponible.
    """


class AccessDeniedError(
    AuthenticationError
):
    """
    L'utilisateur n'est pas autorisé à accéder
    à la ressource demandée.
    """


class UserInactiveError(
    AuthenticationError
):
    """
    Le compte utilisateur est inactif.
    """


class AuthorizationConfigurationError(
    AuthenticationError
):
    """
    La configuration d'autorisation est invalide.
    """


class AuthenticationConfigurationError(
    AuthenticationError
):
    """
    La configuration OIDC est absente ou invalide.
    """


class IdentityClaimsError(
    AuthenticationError
):
    """
    Les claims OIDC reçus ne permettent pas
    d'identifier correctement l'utilisateur.
    """