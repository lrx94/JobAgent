from __future__ import annotations

from src.domain import Job
from src.matching.engine import MatchingEngine
from src.profile import Profile
from src.providers.base import JobProvider
from src.providers.france_travail import (
    FranceTravailProvider,
)
from src.search_request import SearchRequest


class JobService:
    """
    Orchestre la recherche multi-provider et le matching.
    """

    def __init__(
        self,
        providers: list[JobProvider] | None = None,
        engine: MatchingEngine | None = None,
    ) -> None:
        self.providers = (
            list(providers)
            if providers is not None
            else [FranceTravailProvider()]
        )

        self.engine = engine or MatchingEngine()

        self.provider_errors: list[str] = []

    def search(
        self,
        profile: Profile,
    ) -> list[Job]:
        request = SearchRequest.from_profile(
            profile
        )

        jobs = self.search_jobs(request)

        for job in jobs:
            result = self.engine.match(
                profile,
                job,
            )

            job.score = result.score
            job.matched_skills = list(
                result.matched_skills
            )
            job.missing_skills = list(
                result.missing_skills
            )
            job.match_details = dict(
                result.details or {}
            )

            explanation = getattr(
                result,
                "explanation",
                "",
            )

            if explanation:
                job.explanation = explanation

        jobs.sort(
            key=lambda job: job.score,
            reverse=True,
        )

        return jobs

    def search_jobs(
        self,
        request: SearchRequest,
    ) -> list[Job]:
        """
        Exécute uniquement la collecte des offres.

        Cette méthode permettra plus tard de stocker les annonces
        brutes avant de lancer ou de rejouer le matching.
        """

        jobs: list[Job] = []
        self.provider_errors = []

        for provider in self.providers:
            try:
                provider_jobs = provider.search(
                    request
                )

                for job in provider_jobs or []:
                    if not isinstance(job, Job):
                        raise TypeError(
                            f"{provider.name} a retourné "
                            "un élément qui n'est pas un Job."
                        )

                    jobs.append(job)

            except Exception as error:
                message = (
                    f"{provider.name} : {error}"
                )

                self.provider_errors.append(message)
                print(message)

        return self._deduplicate(jobs)

    @staticmethod
    def _deduplicate(
        jobs: list[Job],
    ) -> list[Job]:
        unique_jobs: list[Job] = []
        seen: set[str] = set()

        for job in jobs:
            identity = job.identity

            if identity in seen:
                continue

            seen.add(identity)
            unique_jobs.append(job)

        return unique_jobs