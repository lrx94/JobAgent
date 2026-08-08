from __future__ import annotations

from collections.abc import Iterable
from dataclasses import replace

from src.domain import Job
from src.learning.detector import (
    LearningSuggestionDetector,
)
from src.learning.job_observer import (
    JobLearningObservationExtractor,
)
from src.learning.models import (
    LearningSuggestion,
    SuggestionStatus,
)
from src.learning.repository import (
    LearningSuggestionRepository,
)


class AssistedLearningService:
    """
    Orchestre observation, détection et persistance.

    Aucune méthode ne publie directement une suggestion
    dans les catalogues de compétences ou de concepts.
    """

    def __init__(
        self,
        *,
        detector: LearningSuggestionDetector,
        repository: LearningSuggestionRepository,
        job_observer: (
            JobLearningObservationExtractor
            | None
        ) = None,
    ) -> None:
        if not isinstance(
            detector,
            LearningSuggestionDetector,
        ):
            raise TypeError(
                "detector doit être un "
                "LearningSuggestionDetector."
            )

        if not isinstance(
            repository,
            LearningSuggestionRepository,
        ):
            raise TypeError(
                "repository doit être un "
                "LearningSuggestionRepository."
            )

        self.detector = detector
        self.repository = repository
        self.job_observer = (
            job_observer
            or JobLearningObservationExtractor()
        )

    def analyze_jobs(
        self,
        jobs: Iterable[Job],
        *,
        profile_id: str | None = None,
    ) -> tuple[LearningSuggestion, ...]:
        observations = (
            self.job_observer.extract(
                jobs
            )
        )

        suggestions = (
            self.detector.detect(
                observations
            )
        )

        if profile_id is not None:
            normalized_profile_id = str(profile_id).strip()
            if not normalized_profile_id:
                raise ValueError("profile_id ne peut pas être vide.")
            suggestions = tuple(
                replace(item, profile_id=normalized_profile_id)
                for item in suggestions
            )

        self.repository.save_many(
            suggestions
        )

        return suggestions

    def list_suggestions(
        self,
        *,
        status: SuggestionStatus | None = None,
        profile_id: str | None = None,
    ) -> tuple[LearningSuggestion, ...]:
        suggestions = (
            self.repository.list_all(profile_id=profile_id)
        )

        suggestions = tuple(
            item for item in suggestions
            if item.status != SuggestionStatus.CANDIDATE
            or self.detector.is_quality_term(item.observed_term)
        )

        if status is None:
            return suggestions

        return tuple(
            item
            for item in suggestions
            if item.status == status
        )

    def accept(
        self,
        suggestion_id: str,
        *,
        profile_id: str | None = None,
    ) -> LearningSuggestion:
        return self.repository.change_status(
            suggestion_id=suggestion_id,
            status=SuggestionStatus.ACCEPTED,
            profile_id=profile_id,
        )

    def reject(
        self,
        suggestion_id: str,
        *,
        profile_id: str | None = None,
    ) -> LearningSuggestion:
        return self.repository.change_status(
            suggestion_id=suggestion_id,
            status=SuggestionStatus.REJECTED,
            profile_id=profile_id,
        )

    def ignore(
        self,
        suggestion_id: str,
        *,
        profile_id: str | None = None,
    ) -> LearningSuggestion:
        return self.repository.change_status(
            suggestion_id=suggestion_id,
            status=SuggestionStatus.IGNORED,
            profile_id=profile_id,
        )
