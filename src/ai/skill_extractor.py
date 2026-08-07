"""
Extraction factuelle des compétences présentes dans un texte.

L'extracteur recherche uniquement :
- le nom canonique d'une compétence ;
- ses synonymes déclarés.

Le graphe de compétences n'est pas utilisé ici, car une compétence
proche ne doit pas être considérée comme réellement présente dans le CV.
"""

from __future__ import annotations

import re

from src.ai.skill_dictionary import SKILL_SYNONYMS
from src.ai.skill_normalizer import SkillNormalizer


class SkillExtractor:
    """
    Extrait les compétences explicitement présentes dans un texte.
    """

    def extract(self, text: str) -> list[str]:
        if not text:
            return []

        normalized_text = re.sub(
            r"\s+",
            " ",
            text.casefold(),
        ).strip()
        found: set[str] = set()

        for skill in sorted(SKILL_SYNONYMS):
            canonical = SkillNormalizer.normalize(skill)

            candidates = [
                canonical,
                *SKILL_SYNONYMS.get(canonical, []),
            ]

            for candidate in candidates:
                normalized_candidate = re.sub(
                    r"\s+",
                    " ",
                    str(candidate or "").casefold(),
                ).strip()

                if not normalized_candidate:
                    continue

                pattern = (
                    r"(?<!\w)"
                    + re.escape(normalized_candidate)
                    + r"(?!\w)"
                )

                if re.search(pattern, normalized_text):
                    found.add(canonical)
                    break

        return sorted(found)