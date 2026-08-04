from __future__ import annotations

import unittest

from src.learning import (
    LearningObservation,
    LearningSuggestion,
    SuggestionStatus,
    SuggestionType,
)


class TestLearningModels(
    unittest.TestCase
):

    def test_observation_is_normalized(
        self,
    ):
        observation = LearningObservation(
            term=" Microsoft Fabric ",
            source=" France Travail ",
            reference_id=" job-123 ",
            context=(
                "  Maîtrise de Microsoft "
                "Fabric requise. "
            ),
        )

        self.assertEqual(
            observation.term,
            "Microsoft Fabric",
        )

        self.assertEqual(
            observation.source,
            "france travail",
        )

        self.assertEqual(
            observation.reference_id,
            "job-123",
        )

        self.assertEqual(
            observation.context,
            "Maîtrise de Microsoft Fabric requise.",
        )

    def test_empty_term_is_rejected(
        self,
    ):
        with self.assertRaises(ValueError):
            LearningObservation(
                term="",
                source="job",
            )

    def test_suggestion_is_bounded(
        self,
    ):
        suggestion = LearningSuggestion(
            suggestion_id="skill-123",
            observed_term="Fabric",
            normalized_term="fabric",
            suggestion_type=(
                SuggestionType.SKILL
            ),
            occurrence_count=0,
            source_count=0,
            sources=(
                "France Travail",
                "france travail",
            ),
            contexts=(
                "Contexte",
                "contexte",
            ),
            confidence=2.0,
            status=(
                SuggestionStatus.CANDIDATE
            ),
        )

        self.assertEqual(
            suggestion.occurrence_count,
            1,
        )

        self.assertEqual(
            suggestion.source_count,
            1,
        )

        self.assertEqual(
            suggestion.confidence,
            1.0,
        )

        self.assertEqual(
            suggestion.sources,
            (
                "France Travail",
            ),
        )


if __name__ == "__main__":
    unittest.main()