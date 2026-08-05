from __future__ import annotations

import unittest

from src.learning import (
    LearningObservation,
    LearningSuggestionDetector,
)
from src.learning import (
    LearningObservation,
    LearningObservationOrigin,
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
        origin: LearningObservationOrigin = (
            LearningObservationOrigin.UNKNOWN
        ),
    ) -> LearningObservation:
        return LearningObservation(
            term=term,
            source=source,
            reference_id=reference_id,
            context=context,
            origin=origin,
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

    def test_quality_gate_rejects_noise(
        self,
    ):
        blocked_terms = (
            "Description du poste",
            "Systèmes d",
            "Companies can search",
            "avoid spam applicants",
            "and tag RMmEwMT123456789",
            "Une mutuelle santé",
            "Épargne à 5 %",
            "https://example.com/apply",
        )

        observations = tuple(
            self.observation(
                term,
                reference_id=(
                    f"job-{term_index}-"
                    f"{occurrence_index}"
                ),
            )
            for term_index, term
            in enumerate(blocked_terms)
            for occurrence_index
            in range(3)
        )

        self.assertEqual(
            self.detector.detect(
                observations
            ),
            (),
        )

    def test_quality_gate_keeps_credible_terms(
        self,
    ):
        credible_terms = (
            "Microsoft Fabric",
            "FinOps",
            "Transformation SI",
            "Prompt Engineering",
        )

        observations = tuple(
            self.observation(
                term,
                reference_id=(
                    f"job-{term_index}-"
                    f"{occurrence_index}"
                ),
            )
            for term_index, term
            in enumerate(credible_terms)
            for occurrence_index
            in range(3)
        )

        suggestions = self.detector.detect(
            observations
        )

        normalized_terms = {
            suggestion.normalized_term
            for suggestion in suggestions
        }

        self.assertEqual(
            normalized_terms,
            {
                "microsoft fabric",
                "finops",
                "transformation si",
                "prompt engineering",
            },
        )
    def test_aggregates_observation_origins(
        self,
    ) -> None:
        observations = (
            self.observation(
                "FinOps",
                reference_id="ft-1",
            ),
            LearningObservation(
                term="FinOps",
                source="RemoteOK",
                reference_id="remote-1",
                context="FinOps platform.",
                origin=(
                    LearningObservationOrigin
                    .RAW_TEXT_FALLBACK
                ),
            ),
            LearningObservation(
                term="FinOps",
                source="France Travail",
                reference_id="ft-2",
                context="Pilotage FinOps.",
                origin=(
                    LearningObservationOrigin
                    .JOB_ANALYZER
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

        self.assertEqual(
            suggestions[0].origins,
            (
                LearningObservationOrigin
                .JOB_ANALYZER,
                LearningObservationOrigin
                .RAW_TEXT_FALLBACK,
                LearningObservationOrigin
                .UNKNOWN,
            ),
        )

    def test_raw_text_only_suggestion_is_not_promoted(
        self,
    ) -> None:
        observations = tuple(
            self.observation(
                "Emerging Tool",
                reference_id=f"remote-{index}",
                origin=(
                    LearningObservationOrigin
                    .RAW_TEXT_FALLBACK
                ),
            )
            for index in range(3)
        )

        self.assertEqual(
            self.detector.detect(
                observations
            ),
            (),
        )   
    def test_job_analyzer_suggestion_is_promoted(
        self,
    ) -> None:
        observations = tuple(
            self.observation(
                "FinOps",
                reference_id=f"ft-{index}",
                origin=(
                    LearningObservationOrigin
                    .JOB_ANALYZER
                ),
            )
            for index in range(3)
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
            "finops",
        )

    def test_mixed_origin_suggestion_is_promoted(
        self,
    ) -> None:
        observations = (
            self.observation(
                "FinOps",
                reference_id="ft-1",
                origin=(
                    LearningObservationOrigin
                    .JOB_ANALYZER
                ),
            ),
            self.observation(
                "FinOps",
                reference_id="remote-1",
                origin=(
                    LearningObservationOrigin
                    .RAW_TEXT_FALLBACK
                ),
            ),
            self.observation(
                "FinOps",
                reference_id="remote-2",
                origin=(
                    LearningObservationOrigin
                    .RAW_TEXT_FALLBACK
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

        self.assertEqual(
            suggestions[0].origins,
            (
                LearningObservationOrigin
                .JOB_ANALYZER,
                LearningObservationOrigin
                .RAW_TEXT_FALLBACK,
            ),
        )

    def test_raw_text_only_can_be_enabled_explicitly(
        self,
    ) -> None:
        detector = LearningSuggestionDetector(
            minimum_occurrences=3,
            allow_raw_text_only=True,
        )

        observations = tuple(
            self.observation(
                "Emerging Tool",
                reference_id=f"remote-{index}",
                origin=(
                    LearningObservationOrigin
                    .RAW_TEXT_FALLBACK
                ),
            )
            for index in range(3)
        )

        suggestions = detector.detect(
            observations
        )

        self.assertEqual(
            len(suggestions),
            1,
        )

if __name__ == "__main__":
    unittest.main()