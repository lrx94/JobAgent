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

        relevant_jobs = self.filter_jobs(
            jobs=jobs,
            role_terms=role_terms,
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
        )

    def filter_jobs(
        self,
        jobs: list[Job],
        role_terms: list[str],
    ) -> list[Job]:
        relevant_jobs: list[Job] = []

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

            enough_skills = (
                len(matched_skills)
                >= self.minimum_skill_matches
            )

            if (
                job.score > 0
                and (
                    title_match
                    or enough_skills
                )
            ):
                relevant_jobs.append(
                    job
                )

        relevant_jobs.sort(
            key=lambda item: item.score,
            reverse=True,
        )

        return relevant_jobs

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