from .skill_dictionary import SKILL_SYNONYMS


class SkillNormalizer:

    @staticmethod
    def normalize(skill: str) -> str:

        skill = skill.lower().strip()

        for canonical, synonyms in SKILL_SYNONYMS.items():

            if skill == canonical:
                return canonical

            if skill in synonyms:
                return canonical

        return skill