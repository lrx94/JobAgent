"""
Domain models.

Ce package contient uniquement les objets métier utilisés
par l'application. Aucune logique de parsing ne doit se trouver ici.
"""

from .cv import CV
from .experience import Experience
from .education import Education
from .certification import Certification
from .education_result import EducationResult
from .language import Language

__all__ = [
    "CV",
    "Experience",
    "Education",
    "Certification",
    "EducationResult",
    "Language",
]