from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class SuggestionType(StrEnum):
    SKILL = "skill"
    ALIAS = "alias"
    CONCEPT = "concept"
    ROLE = "role"


class SuggestionStatus(StrEnum):
    CANDIDATE = "candidate"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    IGNORED = "ignored"


@dataclass(
    frozen=True,
    slots=True,
)
class LearningObservation:
    """
    Observation issue d'un CV ou d'une annonce.

    Le texte complet n'est pas conservé : uniquement
    un court contexte facilitant la validation humaine.
    """

    term: str
    source: str
    reference_id: str | None = None
    context: str = ""

    def __post_init__(self) -> None:
        term = str(
            self.term or ""
        ).strip()

        source = str(
            self.source or "unknown"
        ).strip().casefold()

        reference_id = (
            str(self.reference_id).strip()
            if self.reference_id is not None
            else None
        )

        context = " ".join(
            str(
                self.context or ""
            ).split()
        )

        if not term:
            raise ValueError(
                "LearningObservation.term est obligatoire."
            )

        if not source:
            source = "unknown"

        if not reference_id:
            reference_id = None

        object.__setattr__(
            self,
            "term",
            term,
        )

        object.__setattr__(
            self,
            "source",
            source,
        )

        object.__setattr__(
            self,
            "reference_id",
            reference_id,
        )

        object.__setattr__(
            self,
            "context",
            context,
        )


@dataclass(
    frozen=True,
    slots=True,
)
class LearningSuggestion:
    """
    Proposition d'enrichissement soumise à validation.

    Cette structure ne modifie jamais un catalogue.
    """

    suggestion_id: str
    observed_term: str
    normalized_term: str
    suggestion_type: SuggestionType

    occurrence_count: int
    source_count: int
    sources: tuple[str, ...]
    contexts: tuple[str, ...]

    confidence: float
    canonical_target: str | None = None
    status: SuggestionStatus = (
        SuggestionStatus.CANDIDATE
    )
    profile_id: str | None = None

    def __post_init__(self) -> None:
        suggestion_id = str(
            self.suggestion_id or ""
        ).strip()

        observed_term = str(
            self.observed_term or ""
        ).strip()

        normalized_term = str(
            self.normalized_term or ""
        ).strip()

        if not suggestion_id:
            raise ValueError(
                "suggestion_id est obligatoire."
            )

        if not observed_term:
            raise ValueError(
                "observed_term est obligatoire."
            )

        if not normalized_term:
            raise ValueError(
                "normalized_term est obligatoire."
            )

        object.__setattr__(
            self,
            "suggestion_id",
            suggestion_id,
        )

        object.__setattr__(
            self,
            "observed_term",
            observed_term,
        )

        object.__setattr__(
            self,
            "normalized_term",
            normalized_term,
        )

        object.__setattr__(
            self,
            "occurrence_count",
            max(
                1,
                int(self.occurrence_count),
            ),
        )

        object.__setattr__(
            self,
            "source_count",
            max(
                1,
                int(self.source_count),
            ),
        )

        object.__setattr__(
            self,
            "sources",
            self._normalize_values(
                self.sources
            ),
        )

        object.__setattr__(
            self,
            "contexts",
            self._normalize_values(
                self.contexts
            ),
        )

        object.__setattr__(
            self,
            "confidence",
            max(
                0.0,
                min(
                    float(self.confidence),
                    1.0,
                ),
            ),
        )

        canonical_target = (
            str(self.canonical_target).strip()
            if self.canonical_target is not None
            else None
        )

        if not canonical_target:
            canonical_target = None

        object.__setattr__(
            self,
            "canonical_target",
            canonical_target,
        )

        profile_id = (
            str(self.profile_id).strip()
            if self.profile_id is not None
            else None
        )
        object.__setattr__(
            self,
            "profile_id",
            profile_id or None,
        )

    @staticmethod
    def _normalize_values(
        values,
    ) -> tuple[str, ...]:
        result: list[str] = []
        seen: set[str] = set()

        for value in values or ():
            cleaned = str(
                value or ""
            ).strip()

            if not cleaned:
                continue

            identity = cleaned.casefold()

            if identity in seen:
                continue

            seen.add(identity)
            result.append(cleaned)

        return tuple(result)
