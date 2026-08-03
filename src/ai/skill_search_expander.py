from __future__ import annotations

from src.ai.skill_dictionary import SKILL_SYNONYMS
from src.ai.skill_normalizer import SkillNormalizer


class SkillSearchExpander:
    """
    Produit les termes utilisables pour rechercher une compétence
    dans des annonces françaises ou internationales.
    """

    @staticmethod
    def expand(skills: list[str]) -> list[str]:
        expanded: set[str] = set()

        for skill in skills:
            canonical = SkillNormalizer.normalize(skill)

            if not canonical:
                continue

            expanded.add(canonical)

            for synonym in SKILL_SYNONYMS.get(canonical, []):
                normalized_synonym = str(
                    synonym or ""
                ).strip().casefold()

                if normalized_synonym:
                    expanded.add(normalized_synonym)

        return sorted(expanded)