from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path

from src.learning.models import (
    LearningSuggestion,
    SuggestionStatus,
    SuggestionType,
)


class LearningSuggestionRepository:
    """
    Persistance JSON des suggestions d'un utilisateur.

    L'écriture est atomique afin de limiter les risques
    de corruption du fichier.
    """

    def __init__(
        self,
        file_path: str | Path,
    ) -> None:
        self.file_path = (
            Path(file_path)
            .expanduser()
            .resolve()
        )

        self.file_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

    def list_all(
        self,
    ) -> tuple[LearningSuggestion, ...]:
        payload = self._read_payload()

        suggestions = [
            self._deserialize(item)
            for item in payload.get(
                "suggestions",
                [],
            )
            if isinstance(item, dict)
        ]

        suggestions.sort(
            key=lambda item: (
                item.status.value,
                -item.confidence,
                -item.occurrence_count,
                item.normalized_term,
            )
        )

        return tuple(suggestions)

    def get(
        self,
        suggestion_id: str,
    ) -> LearningSuggestion | None:
        normalized_id = str(
            suggestion_id or ""
        ).strip()

        return next(
            (
                item
                for item in self.list_all()
                if item.suggestion_id
                == normalized_id
            ),
            None,
        )

    def save_many(
        self,
        suggestions: tuple[
            LearningSuggestion,
            ...
        ]
        | list[LearningSuggestion],
    ) -> tuple[LearningSuggestion, ...]:
        existing = {
            item.suggestion_id: item
            for item in self.list_all()
        }

        for suggestion in suggestions or ():
            if not isinstance(
                suggestion,
                LearningSuggestion,
            ):
                raise TypeError(
                    "Toutes les suggestions doivent être "
                    "des LearningSuggestion."
                )

            previous = existing.get(
                suggestion.suggestion_id
            )

            if previous is None:
                existing[
                    suggestion.suggestion_id
                ] = suggestion
                continue

            existing[
                suggestion.suggestion_id
            ] = self._merge(
                previous=previous,
                current=suggestion,
            )

        result = tuple(
            sorted(
                existing.values(),
                key=lambda item: (
                    item.normalized_term,
                    item.suggestion_id,
                ),
            )
        )

        self._write(result)
        return result

    def change_status(
        self,
        *,
        suggestion_id: str,
        status: SuggestionStatus,
    ) -> LearningSuggestion:
        if not isinstance(
            status,
            SuggestionStatus,
        ):
            raise TypeError(
                "status doit être un SuggestionStatus."
            )

        suggestions = {
            item.suggestion_id: item
            for item in self.list_all()
        }

        normalized_id = str(
            suggestion_id or ""
        ).strip()

        current = suggestions.get(
            normalized_id
        )

        if current is None:
            raise KeyError(
                "Suggestion inconnue : "
                f"{normalized_id!r}."
            )

        updated = replace(
            current,
            status=status,
        )

        suggestions[
            normalized_id
        ] = updated

        self._write(
            tuple(suggestions.values())
        )

        return updated

    @staticmethod
    def _merge(
        *,
        previous: LearningSuggestion,
        current: LearningSuggestion,
    ) -> LearningSuggestion:
        """
        Les décisions humaines sont conservées lors
        d'une nouvelle campagne d'observation.
        """

        preserved_status = (
            previous.status
            if previous.status
            != SuggestionStatus.CANDIDATE
            else current.status
        )

        return LearningSuggestion(
            suggestion_id=(
                current.suggestion_id
            ),
            observed_term=(
                current.observed_term
            ),
            normalized_term=(
                current.normalized_term
            ),
            suggestion_type=(
                current.suggestion_type
            ),
            occurrence_count=(
                current.occurrence_count
            ),
            source_count=(
                current.source_count
            ),
            sources=current.sources,
            contexts=current.contexts,
            confidence=current.confidence,
            canonical_target=(
                previous.canonical_target
                or current.canonical_target
            ),
            status=preserved_status,
        )

    def _read_payload(
        self,
    ) -> dict:
        if not self.file_path.exists():
            return {
                "version": 1,
                "suggestions": [],
            }

        try:
            payload = json.loads(
                self.file_path.read_text(
                    encoding="utf-8"
                )
            )
        except (
            OSError,
            json.JSONDecodeError,
        ) as error:
            raise RuntimeError(
                "Le référentiel de suggestions "
                "est illisible."
            ) from error

        if not isinstance(payload, dict):
            raise RuntimeError(
                "Le référentiel de suggestions "
                "est invalide."
            )

        return payload

    def _write(
        self,
        suggestions: tuple[
            LearningSuggestion,
            ...
        ],
    ) -> None:
        payload = {
            "version": 1,
            "suggestions": [
                self._serialize(item)
                for item in suggestions
            ],
        }

        temporary_path = (
            self.file_path
            .with_suffix(
                self.file_path.suffix
                + ".tmp"
            )
        )

        temporary_path.write_text(
            json.dumps(
                payload,
                ensure_ascii=False,
                indent=2,
                sort_keys=True,
            ),
            encoding="utf-8",
        )

        temporary_path.replace(
            self.file_path
        )

    @staticmethod
    def _serialize(
        suggestion: LearningSuggestion,
    ) -> dict[str, object]:
        return {
            "suggestion_id": (
                suggestion.suggestion_id
            ),
            "observed_term": (
                suggestion.observed_term
            ),
            "normalized_term": (
                suggestion.normalized_term
            ),
            "suggestion_type": (
                suggestion.suggestion_type.value
            ),
            "occurrence_count": (
                suggestion.occurrence_count
            ),
            "source_count": (
                suggestion.source_count
            ),
            "sources": list(
                suggestion.sources
            ),
            "contexts": list(
                suggestion.contexts
            ),
            "confidence": (
                suggestion.confidence
            ),
            "canonical_target": (
                suggestion.canonical_target
            ),
            "status": suggestion.status.value,
        }

    @staticmethod
    def _deserialize(
        payload: dict,
    ) -> LearningSuggestion:
        return LearningSuggestion(
            suggestion_id=payload.get(
                "suggestion_id",
                "",
            ),
            observed_term=payload.get(
                "observed_term",
                "",
            ),
            normalized_term=payload.get(
                "normalized_term",
                "",
            ),
            suggestion_type=SuggestionType(
                payload.get(
                    "suggestion_type",
                    SuggestionType.SKILL.value,
                )
            ),
            occurrence_count=payload.get(
                "occurrence_count",
                1,
            ),
            source_count=payload.get(
                "source_count",
                1,
            ),
            sources=tuple(
                payload.get(
                    "sources",
                    (),
                )
            ),
            contexts=tuple(
                payload.get(
                    "contexts",
                    (),
                )
            ),
            confidence=payload.get(
                "confidence",
                0.0,
            ),
            canonical_target=payload.get(
                "canonical_target"
            ),
            status=SuggestionStatus(
                payload.get(
                    "status",
                    SuggestionStatus.CANDIDATE.value,
                )
            ),
        )