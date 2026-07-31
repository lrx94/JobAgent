from __future__ import annotations

from dataclasses import dataclass
from typing import Literal


SaveAction = Literal[
    "inserted",
    "updated",
    "unchanged",
]


@dataclass(frozen=True, slots=True)
class RepositorySaveResult:
    """
    Résultat immuable d'une sauvegarde dans JobRepository.

    Attributes:
        action:
            Nature de l'opération réalisée.

        job_id:
            Identifiant SQLite de l'offre.

        identity:
            Identité canonique de l'offre.

        seen_count:
            Nombre total d'observations de l'offre.
    """

    action: SaveAction
    job_id: int
    identity: str
    seen_count: int

    @property
    def is_inserted(self) -> bool:
        return self.action == "inserted"

    @property
    def is_updated(self) -> bool:
        return self.action == "updated"

    @property
    def is_unchanged(self) -> bool:
        return self.action == "unchanged"

    def to_dict(self) -> dict[str, object]:
        return {
            "action": self.action,
            "job_id": self.job_id,
            "identity": self.identity,
            "seen_count": self.seen_count,
        }