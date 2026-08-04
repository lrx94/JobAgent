from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable

from src.domain import Job
from src.learning import (
    AssistedLearningService,
    LearningSuggestion,
    SuggestionStatus,
)


class WorkspaceLearningError(
    RuntimeError
):
    """
    Une opération du Learning Engine Workspace a échoué.
    """


@dataclass(
    frozen=True,
    slots=True,
)
class WorkspaceLearningSummary:
    total: int
    candidate: int
    accepted: int
    rejected: int
    ignored: int

    @classmethod
    def from_suggestions(
        cls,
        suggestions: Iterable[
            LearningSuggestion
        ],
    ) -> WorkspaceLearningSummary:
        values = tuple(
            suggestions or ()
        )

        return cls(
            total=len(values),
            candidate=sum(
                item.status
                == SuggestionStatus.CANDIDATE
                for item in values
            ),
            accepted=sum(
                item.status
                == SuggestionStatus.ACCEPTED
                for item in values
            ),
            rejected=sum(
                item.status
                == SuggestionStatus.REJECTED
                for item in values
            ),
            ignored=sum(
                item.status
                == SuggestionStatus.IGNORED
                for item in values
            ),
        )


@dataclass(
    frozen=True,
    slots=True,
)
class WorkspaceLearningResult:
    detected: tuple[
        LearningSuggestion,
        ...
    ]
    stored: tuple[
        LearningSuggestion,
        ...
    ]
    summary: WorkspaceLearningSummary


class WorkspaceLearningService:
    """
    Adaptateur Workspace du Learning Engine.

    Ce service :
    - reçoit des offres déjà collectées ;
    - déclenche l'observation et la détection ;
    - expose les suggestions persistées ;
    - ne modifie aucun référentiel.
    """

    def __init__(
        self,
        *,
        user_id: str,
        learning_service: AssistedLearningService,
    ) -> None:
        normalized_user_id = str(
            user_id or ""
        ).strip()

        if not normalized_user_id:
            raise ValueError(
                "user_id est obligatoire."
            )

        if not isinstance(
            learning_service,
            AssistedLearningService,
        ):
            raise TypeError(
                "learning_service doit être un "
                "AssistedLearningService."
            )

        self._user_id = normalized_user_id
        self.learning_service = learning_service
       

    @property
    def user_id(self) -> str:
        return self._user_id  

    def analyze_jobs(
        self,
        jobs: Iterable[Job],
    ) -> WorkspaceLearningResult:
        normalized_jobs = self._unique_jobs(
            jobs
        )

        try:
            detected = (
                self.learning_service
                .analyze_jobs(
                    normalized_jobs
                )
            )

            stored = (
                self.learning_service
                .list_suggestions()
            )

        except Exception as error:
            raise WorkspaceLearningError(
                "L'analyse d'apprentissage "
                "des offres a échoué."
            ) from error

        return WorkspaceLearningResult(
            detected=tuple(detected),
            stored=tuple(stored),
            summary=(
                WorkspaceLearningSummary
                .from_suggestions(
                    stored
                )
            ),
        )

    def list_suggestions(
        self,
        *,
        status: SuggestionStatus | None = None,
    ) -> tuple[
        LearningSuggestion,
        ...
    ]:
        try:
            return (
                self.learning_service
                .list_suggestions(
                    status=status
                )
            )
        except Exception as error:
            raise WorkspaceLearningError(
                "Impossible de charger "
                "les suggestions."
            ) from error

    def accept(
        self,
        suggestion_id: str,
    ) -> LearningSuggestion:
        return self._change_status(
            action="accept",
            suggestion_id=suggestion_id,
        )

    def reject(
        self,
        suggestion_id: str,
    ) -> LearningSuggestion:
        return self._change_status(
            action="reject",
            suggestion_id=suggestion_id,
        )

    def ignore(
        self,
        suggestion_id: str,
    ) -> LearningSuggestion:
        return self._change_status(
            action="ignore",
            suggestion_id=suggestion_id,
        )

    def _change_status(
        self,
        *,
        action: str,
        suggestion_id: str,
    ) -> LearningSuggestion:
        normalized_id = str(
            suggestion_id or ""
        ).strip()

        if not normalized_id:
            raise WorkspaceLearningError(
                "Le suggestion_id est obligatoire."
            )

        method = getattr(
            self.learning_service,
            action,
            None,
        )

        if not callable(method):
            raise WorkspaceLearningError(
                "Action Learning Engine inconnue."
            )

        try:
            return method(
                normalized_id
            )
        except Exception as error:
            raise WorkspaceLearningError(
                "Impossible de modifier "
                "le statut de la suggestion."
            ) from error

    @staticmethod
    def _unique_jobs(
        jobs: Iterable[Job] | None,
    ) -> tuple[Job, ...]:
        result: list[Job] = []
        seen_objects: set[int] = set()

        for job in jobs or ():
            if not isinstance(
                job,
                Job,
            ):
                raise TypeError(
                    "Toutes les offres doivent "
                    "être des Job."
                )

            identity = id(job)

            if identity in seen_objects:
                continue

            seen_objects.add(identity)
            result.append(job)

        return tuple(result)

    

        