from __future__ import annotations

from src.ai.skill_dictionary import SKILL_SYNONYMS


class SkillNormalizer:
    """
    Normalise une compétence ou un synonyme vers son nom canonique.
    """

    @staticmethod
    def normalize(skill: str) -> str:
        normalized = str(skill or "").strip().casefold()

        if not normalized:
            return ""

        for canonical, synonyms in SKILL_SYNONYMS.items():
            canonical_normalized = canonical.strip().casefold()

            if normalized == canonical_normalized:
                return canonical

            for synonym in synonyms:
                if normalized == str(synonym).strip().casefold():
                    return canonical

        return normalized