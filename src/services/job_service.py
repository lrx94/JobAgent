from src.providers.france_travail import FranceTravailProvider


class JobService:

    def __init__(self):
        self.providers = [
            FranceTravailProvider(),
        ]

    def search(self, keyword: str, location: str):

        jobs = []

        for provider in self.providers:

            try:
                jobs.extend(
                    provider.search(keyword, location)
                )

            except Exception as e:
                print(
                    f"Erreur provider {provider.__class__.__name__}: {e}"
                )

        return jobs