from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class Experience:
    """
    Représente une expérience professionnelle.
    """

    company: str = ""

    title: str = ""

    location: str = ""

    period: str = ""

    description: str = ""