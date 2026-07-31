from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class Skill:
    """
    Représente une compétence extraite d'un CV ou d'une offre.
    """

    name: str
    category: str = ""
    confidence: float = 1.0

    def __str__(self) -> str:
        return self.name