from __future__ import annotations

from typing import Protocol, runtime_checkable


@runtime_checkable
class AuthorizationRepository(Protocol):
    """
    Contrat de lecture des utilisateurs autorisés.

    Une implémentation peut s'appuyer sur :

    - un fichier JSON ;
    - les secrets Streamlit ;
    - PostgreSQL ;
    - un annuaire ;
    - une API externe.
    """

    def is_allowed_email(
        self,
        email: str,
    ) -> bool:
        """
        Retourne True lorsque l'adresse est autorisée.
        """

        ...

    def allowed_emails(
        self,
    ) -> set[str]:
        """
        Retourne une copie des adresses autorisées.
        """

        ...