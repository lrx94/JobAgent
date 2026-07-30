from src.domain import Job
from src.providers.base import JobProvider

class FranceTravailProvider(JobProvider):

    def search(self, keyword: str, location: str):
        return [
            Job(
                title="Développeur Python IA",
                company="Entreprise Demo",
                location=location,
                description="Recherche développeur Python spécialisé IA.",
                url="https://example.com/job1",
                source="France Travail"
            ),
            Job(
                title="Data Engineer",
                company="Entreprise Demo 2",
                location=location,
                description="Pipeline de données et IA.",
                url="https://example.com/job2",
                source="France Travail"
            )
        ]