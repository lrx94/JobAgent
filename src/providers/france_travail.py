from __future__ import annotations

from src.domain import Job
from src.providers.base import JobProvider
from src.search_request import SearchRequest


class FranceTravailProvider(JobProvider):
    """
    Fournisseur France Travail simulé.

    La connexion à l'API réelle sera réalisée dans un sprint
    ultérieur. Ce fournisseur valide pour l'instant le contrat
    SearchRequest -> list[Job].
    """

    def search(
        self,
        request: SearchRequest,
    ) -> list[Job]:
        keyword = (
            request.primary_keyword
            or "Python"
        )

        location = (
            request.primary_location
            or "France"
        )

        return [
            Job(
                external_id="demo-france-travail-1",
                title="Développeur Python IA",
                company="Entreprise Demo",
                location=location,
                description=(
                    "Recherche développeur Python "
                    "spécialisé en intelligence artificielle."
                ),
                url="https://example.com/job1",
                source="France Travail",
                contract_type="CDI",
                remote_type=(
                    "hybrid"
                    if request.remote
                    else "unknown"
                ),
                salary_min=request.salary_min,
                skills=[
                    keyword,
                    "Python",
                    "Intelligence artificielle",
                ],
                raw_data={
                    "provider_mode": "demo",
                    "requested_keyword": keyword,
                    "requested_location": location,
                },
            ),
            Job(
                external_id="demo-france-travail-2",
                title="Data Engineer",
                company="Entreprise Demo 2",
                location=location,
                description=(
                    "Conception de pipelines de données "
                    "avec Python, SQL et technologies cloud."
                ),
                url="https://example.com/job2",
                source="France Travail",
                contract_type="CDI",
                remote_type=(
                    "remote"
                    if request.remote
                    else "unknown"
                ),
                salary_min=request.salary_min,
                skills=[
                    "Python",
                    "SQL",
                    "Data Engineering",
                ],
                raw_data={
                    "provider_mode": "demo",
                    "requested_keyword": keyword,
                    "requested_location": location,
                },
            ),
        ]