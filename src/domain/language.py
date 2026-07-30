from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class Language:
    """
    Représente une langue maîtrisée par le candidat.
    """

    name: str = ""

    level: str = ""