from __future__ import annotations

from collections.abc import Iterable

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

        self.repository.save_many(
            suggestions
        )

        return suggestions

    def list_suggestions(
        self,
        *,
        status: SuggestionStatus | None = None,
    ) -> tuple[LearningSuggestion, ...]:
        suggestions = (
            self.repository.list_all()
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
    ) -> LearningSuggestion:
        return self.repository.change_status(
            suggestion_id=suggestion_id,
            status=SuggestionStatus.ACCEPTED,
        )

    def reject(
        self,
        suggestion_id: str,
    ) -> LearningSuggestion:
        return self.repository.change_status(
            suggestion_id=suggestion_id,
            status=SuggestionStatus.REJECTED,
        )

    def ignore(
        self,
        suggestion_id: str,
    ) -> LearningSuggestion:
        return self.repository.change_status(
            suggestion_id=suggestion_id,
            status=SuggestionStatus.IGNORED,
        )