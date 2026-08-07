from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field
from typing import Any

from src.career.job_role_catalog import (
    JOB_ROLE_CATALOG,
)
from src.career.models import (
    RoleSuggestion,
)
from src.career.provider_advisor import (
    ProviderAdvisor,
    ProviderStatus,
)
from src.domain import Job
from src.profile import Profile
from src.services.job_service import JobService
from src.providers.provider_selector import (
    ProviderSelectionResult,
    ProviderSelector,
)


@dataclass(frozen=True, slots=True)
class JobFilterDiagnostic:
    """Décision explicable prise par le filtre Career pour une offre."""

    job_identity: str
    score: int
    exact_match_count: int
    semantic_match_count: int
    title_match: bool
    accepted: bool
    rejection_reason: str | None = None


@dataclass(slots=True)
class CareerFilterDiagnostics:
    """Diagnostics individuels et agrégés d'un filtrage Career."""

    jobs: list[JobFilterDiagnostic] = field(default_factory=list)

    @property
    def total_processed(self) -> int:
        return len(self.jobs)

    @property
    def total_accepted(self) -> int:
        return sum(item.accepted for item in self.jobs)

    @property
    def total_rejected(self) -> int:
        return self.total_processed - self.total_accepted

    @property
    def rejection_reasons(self) -> dict[str, int]:
        counts: dict[str, int] = {}

        for item in self.jobs:
            if item.rejection_reason is None:
                continue

            counts[item.rejection_reason] = (
                counts.get(item.rejection_reason, 0) + 1
            )

        return counts

@dataclass(slots=True)
class CareerSearchResult:
    """
    Résultat de recherche depuis un profil métier.
    """
    provider_selection: (
        ProviderSelectionResult | None
    ) = None
    jobs: list[Job] = field(
        default_factory=list
    )
    all_jobs: list[Job] = field(
        default_factory=list
    )
    provider_statuses: list[
        ProviderStatus
    ] = field(
        default_factory=list
    )
    collection_stats: dict[
        str,
        Any,
    ] = field(
        default_factory=dict
    )
    provider_errors: list[str] = field(
        default_factory=list
    )
    filter_diagnostics: CareerFilterDiagnostics = field(
        default_factory=CareerFilterDiagnostics
    )

    @property
    def total_collected(self) -> int:
        return len(self.all_jobs)

    @property
    def total_relevant(self) -> int:
        return len(self.jobs)


class CareerSearchWorkflow:
    """
    Lance une recherche depuis un profil généré par un CV.

    Une annonce est retenue si :

    - son titre correspond au métier choisi ;
    - ou elle possède suffisamment de compétences communes.
    """

    def __init__(
        self,
        job_service: JobService | None = None,
        provider_advisor: (
            ProviderAdvisor | None
        ) = None,
        minimum_skill_matches: int = 2,
        provider_selector: ProviderSelector | None = None,
    ) -> None:
        self.job_service = (
            job_service
            or JobService()
        )

        self.provider_advisor = (
            provider_advisor
            or ProviderAdvisor()
        )

        self.minimum_skill_matches = max(
            1,
            int(
                minimum_skill_matches
            ),
        )
        self.provider_selector = (
            provider_selector
            or ProviderSelector()
        )

    def search(
        self,
        profile: Profile,
        selected_role: (
            RoleSuggestion | None
        ) = None,
    ) -> CareerSearchResult:
        if not isinstance(
            profile,
            Profile,
        ):
            raise TypeError(
                "profile doit être une instance "
                "de Profile."
            )

        available_provider_names = [
            getattr(
                provider,
                "name",
                provider.__class__.__name__,
            )
            for provider
            in self.job_service.providers
        ]
        provider_selection = (
            self.provider_selector.select(
                selected_role=selected_role,
                available_provider_names=(
                    available_provider_names
                ),
                remote_requested=bool(
                    profile.remote
                ),
            )
        )
        recommended_providers = (
            list(
                selected_role
                .preferred_providers
            )
            if selected_role is not None
            else []
        )

        provider_statuses = (
            self.provider_advisor.evaluate(
                recommended_providers=(
                    recommended_providers
                ),
                available_provider_names=(
                    available_provider_names
                ),
            )
        )

        jobs = self.job_service.search(
            profile
        )

        role_terms = self.role_terms(
            selected_role
        )

        relevant_jobs, filter_diagnostics = (
            self._filter_jobs_with_diagnostics(
            jobs=jobs,
            role_terms=role_terms,
            )
        )

        return CareerSearchResult(
            jobs=relevant_jobs,
            all_jobs=list(jobs),
            provider_statuses=(
                provider_statuses
            ),
            collection_stats=dict(
                self.job_service
                .collection_stats
            ),
            provider_errors=list(
                self.job_service
                .provider_errors
            ),
            provider_selection=provider_selection,
            filter_diagnostics=filter_diagnostics,
        )

    def filter_jobs(
        self,
        jobs: list[Job],
        role_terms: list[str],
    ) -> list[Job]:
        relevant_jobs, _ = self._filter_jobs_with_diagnostics(
            jobs=jobs,
            role_terms=role_terms,
        )
        return relevant_jobs

    def _filter_jobs_with_diagnostics(
        self,
        jobs: list[Job],
        role_terms: list[str],
    ) -> tuple[list[Job], CareerFilterDiagnostics]:
        relevant_jobs: list[Job] = []
        diagnostics = CareerFilterDiagnostics()

        for job in jobs:
            matched_skills = (
                self._normalize_list(
                    getattr(
                        job,
                        "matched_skills",
                        [],
                    )
                )
            )

            title_match = any(
                self.contains_phrase(
                    text=job.title,
                    phrase=term,
                )
                for term in role_terms
            )

            semantic_match_count = self._semantic_match_count(job)
            enough_skills = (
                len(matched_skills) + semantic_match_count
                >= self.minimum_skill_matches
            )
            accepted = job.score > 0 and (title_match or enough_skills)

            rejection_reason = None
            if job.score <= 0:
                rejection_reason = "zero_score"
            elif not accepted:
                rejection_reason = "insufficient_relevance_evidence"

            diagnostics.jobs.append(
                JobFilterDiagnostic(
                    job_identity=str(job.identity),
                    score=int(job.score),
                    exact_match_count=len(matched_skills),
                    semantic_match_count=semantic_match_count,
                    title_match=title_match,
                    accepted=accepted,
                    rejection_reason=rejection_reason,
                )
            )

            if accepted:
                relevant_jobs.append(
                    job
                )

        relevant_jobs.sort(
            key=lambda item: item.score,
            reverse=True,
        )

        return relevant_jobs, diagnostics

    @staticmethod
    def _semantic_match_count(job: Job) -> int:
        details = getattr(job, "match_details", {}) or {}
        semantic_matches = details.get("semantic_matches", [])
        return len(semantic_matches) if isinstance(semantic_matches, list) else 0

    @staticmethod
    def role_terms(
        selected_role: (
            RoleSuggestion | None
        ),
    ) -> list[str]:
        if selected_role is None:
            return []

        for role in JOB_ROLE_CATALOG:
            if (
                role.role_id
                == selected_role.role_id
            ):
                return [
                    role.label,
                    *role.aliases,
                ]

        return [
            selected_role.label,
        ]

    @classmethod
    def contains_phrase(
        cls,
        text: str,
        phrase: str,
    ) -> bool:
        normalized_text = (
            cls.normalize_text(text)
        )

        normalized_phrase = (
            cls.normalize_text(phrase)
        )

        if not normalized_phrase:
            return False

        pattern = (
            r"(?<!\w)"
            + re.escape(
                normalized_phrase
            )
            + r"(?!\w)"
        )

        return (
            re.search(
                pattern,
                normalized_text,
            )
            is not None
        )

    @staticmethod
    def normalize_text(
        value: str,
    ) -> str:
        text = str(
            value or ""
        ).strip().casefold()

        decomposed = unicodedata.normalize(
            "NFKD",
            text,
        )

        without_accents = "".join(
            character
            for character in decomposed
            if not unicodedata.combining(
                character
            )
        )

        return " ".join(
            without_accents.split()
        )

    @classmethod
    def _normalize_list(
        cls,
        values,
    ) -> list[str]:
        normalized: list[str] = []
        seen: set[str] = set()

        for value in values or []:
            cleaned = cls.normalize_text(
                value
            )

            if not cleaned:
                continue

            if cleaned in seen:
                continue

            seen.add(cleaned)
            normalized.append(
                cleaned
            )

        return normalized
