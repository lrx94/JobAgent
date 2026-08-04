from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from src.domain import Job
from src.learning import (
    AssistedLearningService,
    LearningSuggestionDetector,
    LearningSuggestionRepository,
    SuggestionStatus,
)


class TestAssistedLearningService(
    unittest.TestCase
):

    def setUp(self) -> None:
        self.temporary_directory = (
            tempfile.TemporaryDirectory()
        )

        detector = (
            LearningSuggestionDetector(
                known_terms=(
                    "Azure",
                    "ITIL",
                ),
                minimum_occurrences=2,
            )
        )

        repository = (
            LearningSuggestionRepository(
                Path(
                    self.temporary_directory.name
                )
                / "suggestions.json"
            )
        )

        self.service = (
            AssistedLearningService(
                detector=detector,
                repository=repository,
            )
        )

    def tearDown(self) -> None:
        self.temporary_directory.cleanup()

    @staticmethod
    def job(
        external_id: str,
    ) -> Job:
        return Job(
            title="Data Engineer",
            company="Example",
            location="Remote",
            description=(
                "Maîtrise de Microsoft Fabric."
            ),
            source="France Travail",
            external_id=external_id,
            skills=[
                "Microsoft Fabric",
            ],
        )

    def test_analyzes_and_persists_jobs(
        self,
    ):
        suggestions = (
            self.service.analyze_jobs(
                [
                    self.job("ft-1"),
                    self.job("ft-2"),
                ]
            )
        )

        suggestions_by_term = {
            item.normalized_term: item
            for item in suggestions
        }

        self.assertIn(
            "microsoft fabric",
            suggestions_by_term,
        )

        fabric = suggestions_by_term[
            "microsoft fabric"
        ]

        self.assertEqual(
            fabric.occurrence_count,
            2,
        )

        stored = (
            self.service.list_suggestions()
        )

        stored_by_term = {
            item.normalized_term: item
            for item in stored
        }

        self.assertIn(
            "microsoft fabric",
            stored_by_term,
        )

    def test_accepts_suggestion(
        self,
    ):
        suggestion = (
            self.service.analyze_jobs(
                [
                    self.job("ft-1"),
                    self.job("ft-2"),
                ]
            )[0]
        )

        accepted = self.service.accept(
            suggestion.suggestion_id
        )

        self.assertEqual(
            accepted.status,
            SuggestionStatus.ACCEPTED,
        )

    def test_filters_by_status(
        self,
    ):
        suggestion = (
            self.service.analyze_jobs(
                [
                    self.job("ft-1"),
                    self.job("ft-2"),
                ]
            )[0]
        )

        self.service.ignore(
            suggestion.suggestion_id
        )

        ignored = (
            self.service.list_suggestions(
                status=(
                    SuggestionStatus.IGNORED
                )
            )
        )

        self.assertEqual(
            len(ignored),
            1,
        )


if __name__ == "__main__":
    unittest.main()