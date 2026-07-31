from __future__ import annotations

from src.domain import Skill

from .extractor import SkillExtractor


class SkillParser:
    """
    Transforme une section de compétences en objets métier Skill.

    La préparation et la reconstruction du texte sont déléguées
    au SkillExtractor.
    """

    def __init__(self) -> None:
        self.extractor = SkillExtractor()

    def parse(self, text: str) -> list[Skill]:
        lines = self.extractor.extract(text)

        return [
            Skill(name=line)
            for line in lines
        ]