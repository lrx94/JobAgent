from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class Certification:
    """
    Représente une certification professionnelle.
    """

    year: str = ""

    organization: str = ""

    name: str = ""

    description: str = ""