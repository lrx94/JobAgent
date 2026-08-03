from __future__ import annotations

from dataclasses import dataclass, field

from .education import Education
from .certification import Certification


@dataclass(slots=True)
class EducationResult:
    """
    Résultat du parsing de la section Formation.

    Un même parser extrait :
        - les formations académiques
        - les certifications professionnelles
    """

    education: list[Education] = field(default_factory=list)

    certifications: list[Certification] = field(default_factory=list)