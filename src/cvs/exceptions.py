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

class CVTooLargeError(InvalidCVError):
    """
    Le fichier CV dépasse la taille maximale autorisée.
    """


class CVAnalysisError(CVError):
    """
    L’analyse du contenu du CV a échoué.
    """
class ProfileCVAssociationError(CVError):
    """
    Une association entre un profil et un CV est invalide.
    """


class ProfileCVAssociationNotFoundError(
    ProfileCVAssociationError
):
    """
    L'association demandée n'existe pas.
    """


class ProfileNotFoundError(
    ProfileCVAssociationError
):
    """
    Le profil demandé n'existe pas dans l'espace utilisateur.
    """