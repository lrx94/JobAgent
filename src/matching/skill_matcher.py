class SkillMatcher:

    def match(self, profile_skills, job_text):

        matched = []
        missing = []

        job_lower = job_text.lower()

        for skill in profile_skills:

            if skill.lower() in job_lower:
                matched.append(skill)
            else:
                missing.append(skill)

        return matched, missing