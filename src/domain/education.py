from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class Education:
    """
    Représente un diplôme ou une formation académique.
    """

    year: str = ""

    school: str = ""

    degree: str = ""

    description: str = ""