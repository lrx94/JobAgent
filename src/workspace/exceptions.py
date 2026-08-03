from __future__ import annotations


class WorkspaceError(Exception):
    """
    Erreur de base du Career Workspace.
    """


class WorkspaceConfigurationError(
    WorkspaceError
):
    """
    La configuration du Workspace est invalide.
    """


class WorkspaceAccessError(
    WorkspaceError
):
    """
    Le Workspace ne peut pas être ouvert avec
    le contexte utilisateur fourni.
    """


class WorkspaceSelectionError(
    WorkspaceError
):
    """
    Une sélection du Workspace est invalide.
    """


class WorkspaceResourceNotFoundError(
    WorkspaceError
):
    """
    Une ressource sélectionnée n'existe pas
    dans l'espace utilisateur.
    """