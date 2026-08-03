from __future__ import annotations

from collections.abc import Iterable
from typing import Any

from src.domain import Job
from src.matching.engine import MatchingEngine
from src.profile import Profile
from src.providers.base import JobProvider
from src.search_request import SearchRequest
from src.services.job_aggregator import (
    AggregationResult,
    JobAggregator,
)
from src.storage.repository import JobRepository
from src.storage.save_result import (
    RepositorySaveResult,
)
from src.utils.json_utils import (
    to_json_compatible,
)
from src.providers.provider_factory import (
    build_default_providers,
)
class JobService:
    """
    Orchestre collecte, matching et persistance.

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
                else build_default_providers()
            )

            aggregator = JobAggregator(
                configured_providers
            )

        self.aggregator = aggregator
        self.engine = engine or MatchingEngine()

        self.providers = (
            self.aggregator.registry.all()
        )

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

        self.last_save_results: list[
            RepositorySaveResult
        ] = []

        self._persistence_stats = (
            self._empty_persistence_stats()
        )

        self._persistence_actions = (
            self._empty_persistence_actions()
        )

    def search(
        self,
        profile: Profile,
    ) -> list[Job]:
        """
        Collecte, évalue, persiste et trie les offres.
        """

        request = SearchRequest.from_profile(
            profile
        )

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
        """

        aggregation_result = (
            self.aggregator.collect(request)
        )

        self.last_aggregation_result = (
            aggregation_result
        )

        self.provider_errors = (
            self._extract_provider_errors(
                aggregation_result
            )
        )

        return list(
            aggregation_result.jobs
        )

    @property
    def collection_stats(self) -> dict[str, Any]:
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

        return (
            self.last_aggregation_result.to_dict()
        )

    @property
    def persistence_stats(self) -> dict[str, Any]:
        """
        Statistiques compatibles avec la V3.8.
        """

        return dict(
            self._persistence_stats
        )

    @property
    def persistence_actions(self) -> dict[str, int]:
        """
        Répartition des actions de sauvegarde V3.9.
        """

        return dict(
            self._persistence_actions
        )

    def _apply_matching(
            self,
            profile: Profile,
            job: Job,
        ) -> None:
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

            serialized_details = (
                to_json_compatible(
                    result.details or {}
                )
            )

            job.match_details = (
                serialized_details
                if isinstance(
                    serialized_details,
                    dict,
                )
                else {
                    "value": serialized_details,
                }
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
        job_list = list(jobs)

        self.persistence_errors = []
        self.last_save_results = []

        self._persistence_stats = (
            self._empty_persistence_stats()
        )

        self._persistence_actions = (
            self._empty_persistence_actions()
        )

        if not self.persistence_enabled:
            return

        self._persistence_stats[
            "attempted"
        ] = len(job_list)

        if self.repository is None:
            message = (
                "Persistance activée mais aucun "
                "repository n'est disponible."
            )

            self.persistence_errors.append(
                message
            )

            self._persistence_stats[
                "failed"
            ] = len(job_list)

            return

        for job in job_list:
            try:
                save_result = (
                    self.repository.save(job)
                )

            except Exception as exc:
                self._persistence_stats[
                    "failed"
                ] += 1

                self.persistence_errors.append(
                    f"{job.identity} : {exc}"
                )

                continue

            self._persistence_stats[
                "saved"
            ] += 1

            if isinstance(
                save_result,
                RepositorySaveResult,
            ):
                self.last_save_results.append(
                    save_result
                )

                self._persistence_actions[
                    save_result.action
                ] += 1
            else:
                # Compatibilité avec les repositories de test
                # V3.8 dont save() retourne None.
                self._persistence_actions[
                    "unknown"
                ] += 1

    def _empty_persistence_stats(
        self,
    ) -> dict[str, Any]:
        return {
            "enabled": self.persistence_enabled,
            "attempted": 0,
            "saved": 0,
            "failed": 0,
        }

    @staticmethod
    def _empty_persistence_actions(
    ) -> dict[str, int]:
        return {
            "inserted": 0,
            "updated": 0,
            "unchanged": 0,
            "unknown": 0,
        }

    @staticmethod
    def _extract_provider_errors(
        aggregation_result: AggregationResult,
    ) -> list[str]:
        errors: list[str] = []

        for provider_name, stats in (
            aggregation_result
            .provider_stats
            .items()
        ):
            if not stats.error:
                continue

            errors.append(
                f"{provider_name} : {stats.error}"
            )

        return errors