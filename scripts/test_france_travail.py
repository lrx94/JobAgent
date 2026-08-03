
from __future__ import annotations

from src.providers.france_travail import (
    FranceTravailProvider,
)
from src.search_request import SearchRequest


def main() -> None:
    provider = FranceTravailProvider()

    if not provider.configured:
        print(
            "France Travail n'est pas configuré."
        )
        print(
            "Définissez FRANCE_TRAVAIL_CLIENT_ID "
            "et FRANCE_TRAVAIL_CLIENT_SECRET."
        )
        return

    jobs = provider.search(
        SearchRequest(
            keywords=[
                "Directeur de projet"
            ],
            locations=["Paris"],
            page_size=20,
        )
    )

    print(
        f"{len(jobs)} offre(s) reçue(s)"
    )

    for job in jobs:
        print("-" * 80)
        print(job.title)
        print(job.company)
        print(job.location)
        print(job.contract_type)
        print(job.salary_min)
        print(job.url)


if __name__ == "__main__":
    main()