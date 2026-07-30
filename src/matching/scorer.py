class Scorer:

    def skill_score(self, matched, total):

        if total == 0:
            return 0

        return round(len(matched) / total * 100)

    def location_score(self, profile, job):

        if not profile.locations:
            return 100

        for location in profile.locations:
            if location.lower() in job.location.lower():
                return 100

        return 0

    def remote_score(self, profile, job):

        if profile.remote and job.remote:
            return 100

        if not profile.remote:
            return 100

        return 0

    def salary_score(self, profile, job):

        if profile.salary_min == 0:
            return 100

        if job.salary >= profile.salary_min:
            return 100

        return round(job.salary / profile.salary_min * 100)

    def global_score(
        self,
        skill,
        location,
        remote,
        salary
    ):

        return round(
            skill * 0.50 +
            location * 0.20 +
            remote * 0.15 +
            salary * 0.15
        )