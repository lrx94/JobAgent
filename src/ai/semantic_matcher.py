from .skill_normalizer import SkillNormalizer
from .skill_graph import SKILL_GRAPH


class SemanticMatcher:

    @staticmethod
    def normalize(skills: list[str]) -> list[str]:

        normalized = []

        for skill in skills:

            normalized.append(
                SkillNormalizer.normalize(skill)
            )

        return list(set(normalized))

    @staticmethod
    def similarity(
        profile_skills: list[str],
        job_skills: list[str],
    ):

        profile = set(
            SemanticMatcher.normalize(profile_skills)
        )

        job = set(
            SemanticMatcher.normalize(job_skills)
        )

        common = profile.intersection(job)

        missing = job.difference(profile)

        return {
            "matched": list(common),
            "missing": list(missing),
            "score": len(common),
        }

    @staticmethod
    def proximity(profile_skill: str, detected_skill: str) -> float:

        profile = SkillNormalizer.normalize(profile_skill)
        detected = SkillNormalizer.normalize(detected_skill)

        if profile == detected:
            return 1.0

        related = SKILL_GRAPH.get(
            profile,
            {}
        ).get(
            "related",
            set()
        )

        if detected in related:
            return 0.5

        return 0.0