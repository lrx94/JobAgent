from __future__ import annotations

import unittest

from src.learning import (
    LearningObservation,
    LearningSuggestionDetector,
)


class TestLearningSuggestionDetector(
    unittest.TestCase
):

    def setUp(self) -> None:
        self.detector = (
            LearningSuggestionDetector(
                known_terms=(
                    "Azure",
                    "ITIL",
                    "Gestion de projet",
                ),
                minimum_occurrences=3,
                minimum_sources=1,
            )
        )

    @staticmethod
    def observation(
        term: str,
        *,
        source: str = "France Travail",
        reference_id: str | None = None,
        context: str = "",
    ) -> LearningObservation:
        return LearningObservation(
            term=term,
            source=source,
            reference_id=reference_id,
            context=context,
        )

    def test_detects_frequent_unknown_term(
        self,
    ):
        observations = (
            self.observation(
                "Microsoft Fabric",
                reference_id="ft-1",
                context=(
                    "Microsoft Fabric requis."
                ),
            ),
            self.observation(
                "microsoft fabric",
                reference_id="ft-2",
                context=(
                    "Expérience Microsoft Fabric."
                ),
            ),
            self.observation(
                "Microsoft-Fabric",
                source="RemoteOK",
                reference_id="remote-1",
                context=(
                    "Microsoft-Fabric platform."
                ),
            ),
        )

        suggestions = self.detector.detect(
            observations
        )

        self.assertEqual(
            len(suggestions),
            1,
        )

        suggestion = suggestions[0]

        self.assertEqual(
            suggestion.normalized_term,
            "microsoft fabric",
        )

        self.assertEqual(
            suggestion.occurrence_count,
            3,
        )

        self.assertEqual(
            suggestion.source_count,
            2,
        )

    def test_known_term_is_ignored(
        self,
    ):
        observations = tuple(
            self.observation("ITIL")
            for _ in range(5)
        )

        self.assertEqual(
            self.detector.detect(
                observations
            ),
            (),
        )

    def test_rare_term_is_ignored(
        self,
    ):
        observations = (
            self.observation("Rare Tool"),
            self.observation("Rare Tool"),
        )

        self.assertEqual(
            self.detector.detect(
                observations
            ),
            (),
        )

    def test_normalization_is_case_and_accent_insensitive(
        self,
    ):
        observations = (
            self.observation("Cybersécurité"),
            self.observation("cybersecurite"),
            self.observation("CYBERSÉCURITÉ"),
        )

        suggestions = self.detector.detect(
            observations
        )

        self.assertEqual(
            len(suggestions),
            1,
        )

        self.assertEqual(
            suggestions[0].normalized_term,
            "cybersecurite",
        )

    def test_contexts_are_deduplicated(
        self,
    ):
        observations = (
            self.observation(
                "FinOps",
                context="FinOps requis.",
            ),
            self.observation(
                "FinOps",
                context="finops requis.",
            ),
            self.observation(
                "FinOps",
                context="Pilotage FinOps.",
            ),
        )

        suggestion = self.detector.detect(
            observations
        )[0]

        self.assertEqual(
            suggestion.contexts,
            (
                "FinOps requis.",
                "Pilotage FinOps.",
            ),
        )

    def test_suggestion_id_is_stable(
        self,
    ):
        first = self.detector.detect(
            (
                self.observation("FinOps"),
                self.observation("FinOps"),
                self.observation("FinOps"),
            )
        )[0]

        second = self.detector.detect(
            (
                self.observation("finops"),
                self.observation("FINOPS"),
                self.observation("FinOps"),
            )
        )[0]

        self.assertEqual(
            first.suggestion_id,
            second.suggestion_id,
        )

    def test_invalid_observation_is_rejected(
        self,
    ):
        with self.assertRaises(TypeError):
            self.detector.detect(
                [object()]
            )


if __name__ == "__main__":
    unittest.main()