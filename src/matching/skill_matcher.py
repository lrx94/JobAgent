from src.ai import SemanticMatcher
from src.ai.skill_normalizer import SkillNormalizer

from .skill_dictionary import SKILL_ALIASES


class SkillMatcher:

    def match(self, profile_skills, text):
        """
        Retourne :
            matched : compétences identiques/synonymes
            partial : compétences proches (matching sémantique)
            missing : compétences absentes
        """

        text = text.lower()
        matched = []
        partial = []
        missing = []

        for skill in profile_skills:

            canonical = SkillNormalizer.normalize(skill)

            aliases = SKILL_ALIASES.get(
                canonical,
                [canonical],
            )

            # 1) Recherche exacte / synonymes
            found = False

            for alias in aliases:

                if alias.lower() in text:
                    matched.append(canonical)
                    found = True
                    break

            if found:
                continue

            # 2) Recherche de compétences proches
            related = []

            try:
                from src.ai.skill_graph import SKILL_GRAPH

                related = SKILL_GRAPH.get(
                    canonical,
                    {},
                ).get(
                   "related",
                    []
                )

            except Exception:
                related = []

            found_related = False
           
            for candidate in related:
                          
                if candidate.lower() in text:
                    score = SemanticMatcher.proximity(
                        canonical,
                        candidate,
                    )
           

                    if score >= 0.5:

                        if candidate not in partial:
                            partial.append({
                                "profile_skill": canonical,
                                "matched_skill": candidate,
                                "score": score,
                            })

                        found_related = True

            if found_related:
                continue

            missing.append(canonical)




        return matched, partial, missing