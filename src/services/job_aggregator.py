from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Iterable

from src.domain import Job
from src.providers.registry import ProviderRegistry
from src.search_request import SearchRequest


@dataclass
class ProviderCollectionStats:
    """Statistiques de collecte d'un provider."""

    provider: str
    collected: int = 0
    accepted: int = 0
    duplicates: int = 0
    invalid: int = 0
    error: str | None = None

    @property
    def succeeded(self) -> bool:
        return self.error is None


@dataclass
class AggregationResult:
    """Résultat complet d'une collecte multi-providers."""

    jobs: list[Job] = field(default_factory=list)

    provider_stats: dict[
        str,
        ProviderCollectionStats,
    ] = field(default_factory=dict)

    total_collected: int = 0
    duplicates_removed: int = 0
    invalid_jobs_removed: int = 0
    errors: int = 0

    @property
    def total_unique(self) -> int:
        return len(self.jobs)

    @property
    def successful_providers(self) -> int:
        return sum(
            1
            for stats in self.provider_stats.values()
            if stats.succeeded
        )

    @property
    def failed_providers(self) -> int:
        return self.errors

    def to_dict(self) -> dict[str, Any]:
        """Retourne les statistiques sous forme de dictionnaire."""

        return {
            "total_collected": self.total_collected,
            "total_unique": self.total_unique,
            "duplicates_removed": self.duplicates_removed,
            "invalid_jobs_removed": self.invalid_jobs_removed,
            "errors": self.errors,
            "successful_providers": self.successful_providers,
            "failed_providers": self.failed_providers,
            "providers": {
                provider_name: {
                    "collected": stats.collected,
                    "accepted": stats.accepted,
                    "duplicates": stats.duplicates,
                    "invalid": stats.invalid,
                    "error": stats.error,
                }
                for provider_name, stats
                in self.provider_stats.items()
            },
        }


class JobAggregator:
    """
    Agrège les offres provenant de plusieurs providers.

    Une erreur sur un provider n'interrompt pas la collecte
    des autres providers.
    """

    def __init__(
        self,
        providers: ProviderRegistry | Iterable[Any] | None = None,
    ) -> None:
        if isinstance(providers, ProviderRegistry):
            self.registry = providers
        else:
            self.registry = ProviderRegistry(providers or [])

    def collect(
        self,
        request: SearchRequest,
    ) -> AggregationResult:
        """Interroge tous les providers enregistrés."""

        if not isinstance(request, SearchRequest):
            raise TypeError(
                "request doit être une instance de SearchRequest."
            )

        result = AggregationResult()
        seen_identities: set[str] = set()

        for provider in self.registry:
            provider_name = ProviderRegistry.provider_name(
                provider
            )

            stats = ProviderCollectionStats(
                provider=provider_name
            )

            result.provider_stats[provider_name] = stats

            try:
                provider_jobs = provider.search(request)

                if provider_jobs is None:
                    provider_jobs = []

                jobs = list(provider_jobs)

                stats.collected = len(jobs)
                result.total_collected += len(jobs)

                for job in jobs:
                    if not isinstance(job, Job):
                        stats.invalid += 1
                        result.invalid_jobs_removed += 1
                        continue

                    identity = self._identity(job)

                    if identity in seen_identities:
                        stats.duplicates += 1
                        result.duplicates_removed += 1
                        continue

                    seen_identities.add(identity)
                    result.jobs.append(job)
                    stats.accepted += 1

            except Exception as error:
                stats.error = str(error)
                result.errors += 1

                print(f"{provider_name} : {error}")

        return result

    @staticmethod
    def _identity(job: Job) -> str:
        """
        Retourne une identité normalisée pour dédupliquer une offre.
        """

        identity = getattr(job, "identity", None)

        if identity:
            return str(identity).strip().casefold()

        if job.url:
            return str(job.url).strip().casefold()

        return "|".join(
            [
                job.title.strip().casefold(),
                job.company.strip().casefold(),
                job.location.strip().casefold(),
            ]
        )