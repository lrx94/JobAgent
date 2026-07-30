from __future__ import annotations

from dataclasses import dataclass, field

from .experience import Experience
from .education import Education
from .certification import Certification
from .language import Language


@dataclass(slots=True)
class CV:
    """
    Représentation métier complète d'un CV.
    """

    # Informations générales
    summary: str = ""

    # Parcours professionnel
    experiences: list[Experience] = field(default_factory=list)

    # Formation
    education: list[Education] = field(default_factory=list)

    # Certifications
    certifications: list[Certification] = field(default_factory=list)

    # Langues
    languages: list[Language] = field(default_factory=list)

    # Compétences
    skills: list[str] = field(default_factory=list)

    # Centres d'intérêt
    interests: list[str] = field(default_factory=list)