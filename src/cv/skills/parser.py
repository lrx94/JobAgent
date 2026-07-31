from __future__ import annotations

from src.domain import Skill

from .extractor import SkillExtractor


class SkillParser:
    """
    Transforme un texte représentant une section "Compétences"
    en une liste d'objets Skill.

    Cette première version ne fait aucune normalisation
    ni classification.
    """

    def __init__(self) -> None:
        self.extractor = SkillExtractor()

    def parse(self, text: str) -> list[Skill]:
        lines = self.extractor.extract(text)

        skills: list[Skill] = []

        for line in lines:
            skills.append(Skill(name=line))

        return skills