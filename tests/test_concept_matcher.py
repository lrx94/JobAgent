from __future__ import annotations

import unittest

from src.skills import (
    BusinessConcept,
    ConceptMatcher,
)


class TestConceptMatcher(
    unittest.TestCase
):

    def setUp(self) -> None:
        self.matcher = ConceptMatcher()

    def test_detects_itil_v4_variants(
        self,
    ):
        variants = (
            "ITILv4",
            "itilV4",
            "ITIL V4 Foundation",
            "Certification itil 4",
            "ITIL Foundation",
        )

        for value in variants:
            with self.subTest(value=value):
                labels = (
                    self.matcher
                    .extract_labels(value)
                )

                self.assertIn(
                    "ITIL",
                    labels,
                )

    def test_detects_project_management(
        self,
    ):
        labels = self.matcher.extract_labels(
            "Pilotage d'un portefeuille de projets "
            "et coordination des équipes projet."
        )

        self.assertIn(
            "Gestion de projet",
            labels,
        )

    def test_detects_project_director(
        self,
    ):
        labels = self.matcher.extract_labels(
            "Directeur de projet IT depuis 2018."
        )

        self.assertIn(
            "Gestion de projet",
            labels,
        )

    def test_detects_it_governance(
        self,
    ):
        labels = self.matcher.extract_labels(
            "Gouvernance COMEX, priorisation, "
            "stratégie et arbitrage stratégique."
        )

        self.assertIn(
            "Gouvernance SI",
            labels,
        )

    def test_detects_governance_from_design_authority(
        self,
    ):
        labels = self.matcher.extract_labels(
            "Animation d'une Design Authority "
            "et d'un comité de pilotage."
        )

        self.assertIn(
            "Gouvernance SI",
            labels,
        )

    def test_matching_is_case_insensitive(
        self,
    ):
        labels = self.matcher.extract_labels(
            "GOUVERNANCE SI ET ITILV4"
        )

        self.assertIn(
            "Gouvernance SI",
            labels,
        )

        self.assertIn(
            "ITIL",
            labels,
        )

    def test_matching_is_accent_insensitive(
        self,
    ):
        labels = self.matcher.extract_labels(
            "strategie informatique et schema directeur"
        )

        self.assertIn(
            "Gouvernance SI",
            labels,
        )

    def test_unrelated_text_returns_no_match(
        self,
    ):
        labels = self.matcher.extract_labels(
            "Photographie, randonnée et natation."
        )

        self.assertEqual(
            labels,
            (),
        )

    def test_invalid_catalog_item_is_rejected(
        self,
    ):
        with self.assertRaises(TypeError):
            ConceptMatcher(
                concepts=[
                    object(),
                ]
            )

    def test_custom_concept_is_supported(
        self,
    ):
        matcher = ConceptMatcher(
            concepts=(
                BusinessConcept(
                    concept_id="finops",
                    label="FinOps",
                    aliases=(
                        "cloud cost management",
                    ),
                ),
            )
        )

        labels = matcher.extract_labels(
            "Cloud cost management."
        )

        self.assertEqual(
            labels,
            (
                "FinOps",
            ),
        )


if __name__ == "__main__":
    unittest.main()