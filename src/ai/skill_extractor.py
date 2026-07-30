"""
Extraction intelligente des compétences.

Utilise :

- SkillNormalizer
- SKILL_SYNONYMS
- SKILL_GRAPH
"""

import re

from src.ai.skill_dictionary import SKILL_SYNONYMS
from src.ai.skill_graph import SKILL_GRAPH
from src.ai.skill_normalizer import SkillNormalizer


class SkillExtractor:

    def extract(self, text: str) -> list[str]:

        text = text.lower()

        found = set()

        # Toutes les compétences connues
        skills = (
            set(SKILL_SYNONYMS.keys())
            | set(SKILL_GRAPH.keys())
        )

        for skill in sorted(skills):

            canonical = SkillNormalizer.normalize(skill)

            candidates = [canonical]
            candidates.extend(
                SKILL_SYNONYMS.get(
                    canonical,
                    [],
                )
            )

            related = SKILL_GRAPH.get(
                canonical,
                {},
            ).get(
                "related",
                [],
            )

            candidates.extend(related)

            for candidate in candidates:

                pattern = (
                    rf"\b{re.escape(candidate.lower())}\b"
                )

                if re.search(
                    pattern,
                    text,
                    re.IGNORECASE,
                ):
                    found.add(canonical)
                    break

        return sorted(found)