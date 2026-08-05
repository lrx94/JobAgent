from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from src.learning import (
    LearningObservationOrigin,
    LearningSuggestion,
    LearningSuggestionRepository,
    SuggestionStatus,
    SuggestionType,
)


class TestLearningSuggestionRepository(
    unittest.TestCase
):

    def setUp(self) -> None:
        self.temporary_directory = (
            tempfile.TemporaryDirectory()
        )

        self.repository = (
            LearningSuggestionRepository(
                Path(
                    self.temporary_directory.name
                )
                / "suggestions.json"
            )
        )

    def tearDown(self) -> None:
        self.temporary_directory.cleanup()

    @staticmethod
    def suggestion(
        *,
        occurrence_count: int = 5,
    ) -> LearningSuggestion:
        return LearningSuggestion(
            suggestion_id="skill-fabric",
            observed_term="Microsoft Fabric",
            normalized_term="microsoft fabric",
            suggestion_type=(
                SuggestionType.SKILL
            ),
            occurrence_count=(
                occurrence_count
            ),
            source_count=2,
            sources=(
                "france travail",
                "remoteok",
            ),
            contexts=(
                "Microsoft Fabric requis.",
            ),
            confidence=0.8,
        )

    def test_saves_and_loads_suggestion(
        self,
    ):
        self.repository.save_many(
            [self.suggestion()]
        )

        result = (
            self.repository.list_all()
        )

        self.assertEqual(
            len(result),
            1,
        )

        self.assertEqual(
            result[0].observed_term,
            "Microsoft Fabric",
        )

    def test_status_is_persisted(
        self,
    ):
        self.repository.save_many(
            [self.suggestion()]
        )

        self.repository.change_status(
            suggestion_id="skill-fabric",
            status=(
                SuggestionStatus.ACCEPTED
            ),
        )

        result = self.repository.get(
            "skill-fabric"
        )

        self.assertEqual(
            result.status,
            SuggestionStatus.ACCEPTED,
        )

    def test_human_status_survives_refresh(
        self,
    ):
        self.repository.save_many(
            [self.suggestion()]
        )

        self.repository.change_status(
            suggestion_id="skill-fabric",
            status=(
                SuggestionStatus.REJECTED
            ),
        )

        self.repository.save_many(
            [
                self.suggestion(
                    occurrence_count=12
                )
            ]
        )

        result = self.repository.get(
            "skill-fabric"
        )

        self.assertEqual(
            result.status,
            SuggestionStatus.REJECTED,
        )

        self.assertEqual(
            result.occurrence_count,
            12,
        )

    def test_unknown_suggestion_is_rejected(
        self,
    ):
        with self.assertRaises(KeyError):
            self.repository.change_status(
                suggestion_id="unknown",
                status=(
                    SuggestionStatus.ACCEPTED
                ),
            )

    def test_persists_suggestion_origins(
        self,
    ) -> None:
        suggestion = LearningSuggestion(
            suggestion_id="skill-finops",
            observed_term="FinOps",
            normalized_term="finops",
            suggestion_type=(
                SuggestionType.SKILL
            ),
            occurrence_count=3,
            source_count=2,
            sources=(
                "france travail",
                "remoteok",
            ),
            contexts=(),
            confidence=0.7,
            origins=(
                LearningObservationOrigin
                .JOB_ANALYZER,
                LearningObservationOrigin
                .RAW_TEXT_FALLBACK,
            ),
        )

        self.repository.save_many(
            (suggestion,)
        )

        loaded = self.repository.list_all()

        self.assertEqual(
            loaded[0].origins,
            suggestion.origins,
        )
if __name__ == "__main__":
    unittest.main()