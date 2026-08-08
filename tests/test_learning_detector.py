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

    def test_quality_gate_rejects_scraping_identifiers(self):
        rejected = (
            "and tag RMmEwMTplMGE6ZWUwOmMxMjA6NjljMDplZThjOmJiMzpjNDk1",
            "https://example.com/jobs/123",
            "user@example.com",
            "550e8400-e29b-41d4-a716-446655440000",
            "a3f80c924ecb2f3e8f45d09fe7a55c10",
            "<span>Docker</span>",
        )
        for term in rejected:
            with self.subTest(term=term):
                observations = tuple(
                    self.observation(term) for _ in range(3)
                )
                self.assertEqual(self.detector.detect(observations), ())

    def test_quality_gate_preserves_legitimate_technical_skills(self):
        for term in ("C++", "C#", ".NET", "SAP", "Power BI", "CI/CD", "Kubernetes"):
            with self.subTest(term=term):
                observations = tuple(
                    self.observation(term) for _ in range(3)
                )
                self.assertEqual(len(self.detector.detect(observations)), 1)

    def test_business_skill_can_pass_quality_gate(self):
        observations = tuple(
            self.observation("Pilotage financier") for _ in range(3)
        )
        self.assertEqual(len(self.detector.detect(observations)), 1)

    def test_quality_gate_rejects_structural_and_lexical_noise(self):
        rejected = (
            "de la DSI",
            "Systèmes d",
            "Esprit d",
            "Participer à l",
            "Description du poste",
            "RESPONSABILITÉS",
            "Enfin",
            "Directeur",
            "Directrice des systèmes",
            "Définir",
            "Mettre en place",
            "Piloter les projets",
            "à la Direction",
            "les équipes IT",
        )

        for term in rejected:
            with self.subTest(term=term):
                self.assertFalse(
                    self.detector.is_quality_term(term)
                )

    def test_quality_gate_preserves_expected_business_concepts(self):
        admitted = (
            "RGPD",
            "Cybersécurité",
            "ERP",
            "IA",
            "SAP",
            "Kubernetes",
            "Power BI",
            "FinOps",
            "C++",
            "C#",
            ".NET",
            "CI/CD",
            "gestion de projet",
            "gouvernance SI",
            "protection des données",
        )

        for term in admitted:
            with self.subTest(term=term):
                self.assertTrue(
                    self.detector.is_quality_term(term)
                )
                observations = tuple(
                    self.observation(
                        term,
                        reference_id=f"job-{index}",
                        context=f"Contexte métier {index}: {term}",
                    )
                    for index in range(3)
                )
                if (
                    self.detector.normalize_term(term)
                    not in self.detector.known_terms
                ):
                    self.assertEqual(
                        len(self.detector.detect(observations)),
                        1,
                    )

    def test_quality_gate_uses_generic_rules_not_observed_phrases(self):
        rejected_equivalents = (
            "du département Finance",
            "Garantir la conformité",
            "Responsable des opérations",
            "Profil recherché",
            "Architecture d",
        )

        for term in rejected_equivalents:
            with self.subTest(term=term):
                self.assertFalse(
                    self.detector.is_quality_term(term)
                )

    def test_quality_gate_rejects_document_headers(self):
        headers = (
            "Description du profil",
            "Description du poste",
            "Profil recherché",
            "Votre profil",
            "Vos missions",
            "Responsabilités",
            "Missions",
            "Compétences requises",
            "Qualifications",
        )

        for term in headers:
            with self.subTest(term=term):
                self.assertFalse(
                    self.detector.is_quality_term(term)
                )

    def test_quality_gate_rejects_incomplete_subject_fragments(self):
        fragments = (
            "Vous avez une",
            "Vous êtes un",
            "Vous êtes une",
            "Vous disposez d'une",
            "Vous justifiez d'une",
            "Nous recherchons un",
            "Il possède une",
        )

        for term in fragments:
            with self.subTest(term=term):
                self.assertFalse(
                    self.detector.is_quality_term(term)
                )

    def test_incomplete_fragment_rule_preserves_complete_skills(self):
        skills = (
            "gestion de projet",
            "analyse financière",
            "protection des données",
            "pilotage budgétaire",
            "cybersécurité",
            "ERP",
            "RGPD",
            "IA",
            "Power BI",
            "SAP",
            "C++",
            "C#",
            ".NET",
            "CI/CD",
        )

        for term in skills:
            with self.subTest(term=term):
                self.assertTrue(
                    self.detector.is_quality_term(term)
                )

    def test_quality_gate_rejects_isolated_numbers(self):
        for term in ("10", "000", "2025"):
            with self.subTest(term=term):
                self.assertFalse(
                    self.detector.is_quality_term(term)
                )

    def test_quality_gate_preserves_structured_versioned_skills(self):
        for term in (
            "ISO 27001",
            "Windows 11",
            "Python 3",
            "SAP S/4HANA",
            "C++",
            "C#",
            ".NET",
            "CI/CD",
            "RGPD",
            "ERP",
            "Cybersécurité",
        ):
            with self.subTest(term=term):
                self.assertTrue(
                    self.detector.is_quality_term(term)
                )


if __name__ == "__main__":
    unittest.main()
