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
    profile_id: str | None = None


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
        *,
        profile_id: str,
    ) -> WorkspaceLearningResult:
        normalized_profile_id = self._require_profile_id(profile_id)
        normalized_jobs = self._unique_jobs(
            jobs
        )

        try:
            detected = (
                self.learning_service
                .analyze_jobs(
                    normalized_jobs,
                    profile_id=normalized_profile_id,
                )
            )

            stored = (
                self.learning_service
                .list_suggestions(
                    profile_id=normalized_profile_id
                )
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
            profile_id=normalized_profile_id,
        )

    def analyze_search_result(
        self,
        search_result: Any,
        *,
        profile_id: str,
    ) -> WorkspaceLearningResult:
        """Analyse uniquement les offres validées par la pertinence Career."""

        relevant_jobs = getattr(search_result, "jobs", None)
        if relevant_jobs is None:
            raise WorkspaceLearningError(
                "Le résultat Career ne fournit pas ses offres pertinentes."
            )

        return self.analyze_jobs(
            relevant_jobs,
            profile_id=profile_id,
        )

    def list_suggestions(
        self,
        *,
        profile_id: str,
        status: SuggestionStatus | None = None,
    ) -> tuple[
        LearningSuggestion,
        ...
    ]:
        try:
            return (
                self.learning_service
                .list_suggestions(
                    status=status,
                    profile_id=self._require_profile_id(profile_id),
                )
            )
        except Exception as error:
            raise WorkspaceLearningError(
                "Impossible de charger "
                "les suggestions."
            ) from error

    def accept(
        self,
        profile_id: str,
        suggestion_id: str,
    ) -> LearningSuggestion:
        return self._change_status(
            action="accept",
            profile_id=profile_id,
            suggestion_id=suggestion_id,
        )

    def reject(
        self,
        profile_id: str,
        suggestion_id: str,
    ) -> LearningSuggestion:
        return self._change_status(
            action="reject",
            profile_id=profile_id,
            suggestion_id=suggestion_id,
        )

    def ignore(
        self,
        profile_id: str,
        suggestion_id: str,
    ) -> LearningSuggestion:
        return self._change_status(
            action="ignore",
            profile_id=profile_id,
            suggestion_id=suggestion_id,
        )

    def _change_status(
        self,
        *,
        action: str,
        profile_id: str,
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
                normalized_id,
                profile_id=self._require_profile_id(profile_id),
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

    @staticmethod
    def _require_profile_id(profile_id: str) -> str:
        normalized = str(profile_id or "").strip()
        if not normalized:
            raise WorkspaceLearningError(
                "Le profile_id Learning est obligatoire."
            )
        return normalized

