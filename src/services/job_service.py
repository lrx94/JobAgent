from src.providers.france_travail import FranceTravailProvider
from src.matching.engine import MatchingEngine


class JobService:

    def __init__(self):

        self.providers = [
            FranceTravailProvider()
        ]

        self.engine = MatchingEngine()

    def search(self, profile):

        jobs = []

        keyword = profile.keywords[0] if profile.keywords else ""

        location = profile.locations[0] if profile.locations else ""

        for provider in self.providers:

            try:

                jobs.extend(
                    provider.search(
                        keyword,
                        location
                    )
                )

            except Exception as e:

                print(
                    f"{provider.__class__.__name__} : {e}"
                )

        # Matching
        for job in jobs:

            result = self.engine.match(
                profile,
                job
            )

            job.score = result.score

            job.matched_skills = result.matched_skills

            job.missing_skills = result.missing_skills

        jobs.sort(
            key=lambda j: j.score,
            reverse=True
        )

        return jobs