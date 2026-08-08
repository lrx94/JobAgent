from __future__ import annotations

import tempfile
import unittest
from dataclasses import replace
from pathlib import Path

from src.domain import Job
from src.learning import (
    AssistedLearningService,
    LearningSuggestion,
    LearningSuggestionDetector,
    LearningSuggestionRepository,
    SuggestionStatus,
    SuggestionType,
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
        self.repository = repository

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

    def test_invalid_historical_candidate_is_hidden_but_decisions_remain(self):
        invalid = replace(
            LearningSuggestion(
                suggestion_id="invalid-candidate",
                observed_term="placeholder",
                normalized_term="placeholder",
                suggestion_type=SuggestionType.SKILL,
                occurrence_count=3,
                source_count=1,
                sources=("test",),
                contexts=(),
                confidence=0.5,
            ),
            observed_term=(
                "and tag RMmEwMTplMGE6ZWUwOmMxMjA6NjljMDplZThjOmJiMzpjNDk1"
            ),
            normalized_term="invalid tag",
            profile_id="daf",
        )
        self.repository.save_many([invalid])
        self.assertEqual(
            self.service.list_suggestions(profile_id="daf"),
            (),
        )

        for status in (
            SuggestionStatus.ACCEPTED,
            SuggestionStatus.REJECTED,
            SuggestionStatus.IGNORED,
        ):
            with self.subTest(status=status):
                decided = replace(
                    invalid,
                    suggestion_id=f"invalid-{status.value}",
                    status=status,
                )
                self.repository.save_many([decided])

        visible = self.service.list_suggestions(profile_id="daf")
        self.assertEqual(
            {item.status for item in visible},
            {
                SuggestionStatus.ACCEPTED,
                SuggestionStatus.REJECTED,
                SuggestionStatus.IGNORED,
            },
        )

    def test_historical_numeric_and_header_candidates_are_hidden(self):
        candidates = tuple(
            LearningSuggestion(
                suggestion_id=f"historical-{index}",
                observed_term=term,
                normalized_term=term.casefold(),
                suggestion_type=SuggestionType.SKILL,
                occurrence_count=3,
                source_count=1,
                sources=("test",),
                contexts=("Contexte historique",),
                confidence=0.5,
                profile_id="dsi",
            )
            for index, term in enumerate(
                ("10", "000", "Description du profil")
            )
        )
        self.repository.save_many(candidates)

        self.assertEqual(
            self.service.list_suggestions(profile_id="dsi"),
            (),
        )


if __name__ == "__main__":
    unittest.main()
