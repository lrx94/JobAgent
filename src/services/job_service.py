from __future__ import annotations

from collections.abc import Iterable
from typing import Any

from src.domain import Job
from src.matching.engine import MatchingEngine
from src.profile import Profile
from src.providers.base import JobProvider
from src.providers.france_travail import (
    FranceTravailProvider,
)
from src.search_request import SearchRequest
from src.services.job_aggregator import (
    AggregationResult,
    JobAggregator,
)
from src.storage.repository import JobRepository


class JobService:
    """
    Orchestre la collecte, le matching et la persistance
    des offres d'emploi.

    La collecte multi-provider est déléguée à JobAggregator.

    JobService reste responsable :

    - de la construction du SearchRequest ;
    - du matching des offres avec le profil ;
    - de l'enrichissement des objets Job ;
    - de la persistance optionnelle des résultats ;
    - du tri final par score.

    Une erreur de persistance ne doit jamais empêcher
    la restitution des résultats de recherche.
    """

    def __init__(
        self,
        providers: Iterable[JobProvider] | None = None,
        engine: MatchingEngine | None = None,
        aggregator: JobAggregator | None = None,
        repository: JobRepository | None = None,
        persistence_enabled: bool = True,
    ) -> None:
        if aggregator is not None and providers is not None:
            raise ValueError(
                "Fournir soit providers, soit aggregator, "
                "mais pas les deux."
            )

        if aggregator is None:
            configured_providers = (
                list(providers)
                if providers is not None
                else [FranceTravailProvider()]
            )

            aggregator = JobAggregator(
                configured_providers
            )

        self.aggregator = aggregator
        self.engine = engine or MatchingEngine()

        # Compatibilité avec le code historique pouvant consulter
        # directement service.providers.
        self.providers = self.aggregator.registry.all()

        self.persistence_enabled = bool(
            persistence_enabled
        )

        self.repository = (
            repository
            if repository is not None
            else (
                JobRepository()
                if self.persistence_enabled
                else None
            )
        )

        self.provider_errors: list[str] = []
        self.persistence_errors: list[str] = []

        self.last_aggregation_result: (
            AggregationResult | None
        ) = None

        self._persistence_stats: dict[str, Any] = (
            self._empty_persistence_stats()
        )

    def search(
        self,
        profile: Profile,
    ) -> list[Job]:
        """
        Collecte, évalue, persiste et trie les offres
        pour un profil.
        """

        request = SearchRequest.from_profile(profile)

        jobs = self.search_jobs(request)

        for job in jobs:
            self._apply_matching(
                profile=profile,
                job=job,
            )

        self._persist_jobs(jobs)

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

        Cette méthode n'exécute ni le matching,
        ni la persistance.

        La déduplication, la validation des objets Job,
        l'isolation des erreurs et les statistiques sont
        gérées par JobAggregator.
        """

        aggregation_result = self.aggregator.collect(
            request
        )

        self.last_aggregation_result = (
            aggregation_result
        )

        self.provider_errors = (
            self._extract_provider_errors(
                aggregation_result
            )
        )

        return list(aggregation_result.jobs)

    @property
    def collection_stats(self) -> dict[str, Any]:
        """
        Retourne les statistiques de la dernière collecte.

        Avant la première collecte, retourne une structure vide
        mais stable pour faciliter son utilisation dans l'UI.
        """

        if self.last_aggregation_result is None:
            return {
                "total_collected": 0,
                "total_unique": 0,
                "duplicates_removed": 0,
                "invalid_jobs_removed": 0,
                "errors": 0,
                "successful_providers": 0,
                "failed_providers": 0,
                "providers": {},
            }

        return self.last_aggregation_result.to_dict()

    @property
    def persistence_stats(self) -> dict[str, Any]:
        """
        Retourne les statistiques de la dernière opération
        de persistance.

        Structure retournée :

        {
            "enabled": bool,
            "attempted": int,
            "saved": int,
            "failed": int,
        }
        """

        return dict(self._persistence_stats)

    def _apply_matching(
        self,
        profile: Profile,
        job: Job,
    ) -> None:
        """
        Applique le résultat du moteur de matching
        à une offre.
        """

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

    def _persist_jobs(
        self,
        jobs: Iterable[Job],
    ) -> None:
        """
        Persiste les offres une par une.

        Une erreur sur une offre est isolée afin que :

        - les offres suivantes puissent être enregistrées ;
        - les résultats restent retournés à l'utilisateur ;
        - le moteur de recherche ne dépende pas de SQLite.
        """

        job_list = list(jobs)

        self.persistence_errors = []
        self._persistence_stats = (
            self._empty_persistence_stats()
        )

        if not self.persistence_enabled:
            return

        self._persistence_stats["attempted"] = len(
            job_list
        )

        if self.repository is None:
            message = (
                "Persistance activée mais aucun repository "
                "n'est disponible."
            )

            self.persistence_errors.append(message)

            self._persistence_stats["failed"] = len(
                job_list
            )

            return

        for job in job_list:
            try:
                self.repository.save(job)

            except Exception as exc:
                self._persistence_stats["failed"] += 1

                self.persistence_errors.append(
                    f"{job.identity} : {exc}"
                )

                continue

            self._persistence_stats["saved"] += 1

    def _empty_persistence_stats(
        self,
    ) -> dict[str, Any]:
        """
        Produit une structure stable de statistiques.
        """

        return {
            "enabled": self.persistence_enabled,
            "attempted": 0,
            "saved": 0,
            "failed": 0,
        }

    @staticmethod
    def _extract_provider_errors(
        aggregation_result: AggregationResult,
    ) -> list[str]:
        """
        Convertit les erreurs de l'agrégateur dans le format
        historique de JobService.
        """

        errors: list[str] = []

        for provider_name, stats in (
            aggregation_result.provider_stats.items()
        ):
            if not stats.error:
                continue

            errors.append(
                f"{provider_name} : {stats.error}"
            )

        return errors