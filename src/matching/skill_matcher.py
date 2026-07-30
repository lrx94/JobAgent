from .skill_dictionary import SKILL_ALIASES


class SkillMatcher:

    def match(self, profile_skills, text):

        text = text.lower()

        matched = []
        missing = []

        for skill in profile_skills:

            canonical = skill.lower()

            aliases = SKILL_ALIASES.get(
                canonical,
                [canonical]
            )

            found = any(
                alias in text
                for alias in aliases
            )

            if found:
                matched.append(skill)
            else:
                missing.append(skill)

        return matched, missing