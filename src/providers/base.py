from __future__ import annotations

from abc import ABC, abstractmethod

from src.domain import Job
from src.search_request import SearchRequest


class JobProvider(ABC):
    """
    Contrat commun de tous les fournisseurs d'annonces.
    """

    @property
    def name(self) -> str:
        return self.__class__.__name__

    @abstractmethod
    def search(
        self,
        request: SearchRequest,
    ) -> list[Job]:
        """
        Recherche et retourne des offres normalisées.

        Chaque fournisseur doit convertir ses données propres
        en objets Job canoniques.
        """

        raise NotImplementedError