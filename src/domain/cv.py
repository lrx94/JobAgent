from __future__ import annotations

from dataclasses import dataclass, field

from .experience import Experience
from .education import Education
from .certification import Certification
from .language import Language
from .skill import Skill


@dataclass(slots=True)
class CV:
    """
    Modèle métier représentant un CV.
    """

    summary: str = ""

    experiences: list[Experience] = field(default_factory=list)

    education: list[Education] = field(default_factory=list)

    certifications: list[Certification] = field(default_factory=list)

    languages: list[Language] = field(default_factory=list)

    skills: list[Skill] = field(default_factory=list)

    interests: list[str] = field(default_factory=list)