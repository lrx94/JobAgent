from __future__ import annotations


class CVError(Exception):
    """
    Erreur de base du domaine CV.
    """


class CVNotFoundError(CVError):
    """
    Le CV demandé n'existe pas dans l'espace utilisateur.
    """


class InvalidCVError(CVError):
    """
    Le document ou ses métadonnées sont invalides.
    """


class DuplicateCVError(CVError):
    """
    Un document identique est déjà enregistré.
    """


class CVStorageError(CVError):
    """
    Une opération de stockage du CV a échoué.
    """


class CVStillInUseError(CVError):
    """
    Le CV ne peut pas être supprimé car il est encore utilisé.
    """