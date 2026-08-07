from __future__ import annotations

import unittest

from src.ai.skill_extractor import (
    SkillExtractor,
)


class TestAISkillExtractor(
    unittest.TestCase
):

    def setUp(self) -> None:
        self.extractor = SkillExtractor()

    def test_empty_text_returns_empty_list(
        self,
    ) -> None:
        self.assertEqual(
            self.extractor.extract(""),
            [],
        )

    def test_extracts_known_it_skills(
        self,
    ) -> None:
        skills = set(
            self.extractor.extract(
                (
                    "Environnement Python, Azure, "
                    "Terraform et Kubernetes."
                )
            )
        )

        self.assertEqual(
            skills,
            {
                "azure",
                "kubernetes",
                "python",
                "terraform",
            },
        )

    def test_extracts_finance_skills(
        self,
    ) -> None:
        text = """
        Directeur financier spécialisé dans le pilotage
        budgétaire, le contrôle de gestion, le reporting
        financier et l'analyse financière.

        Suivi de la trésorerie, pilotage de la masse
        salariale, indicateurs de performance, SAP
        et MS Office.
        """

        skills = set(
            self.extractor.extract(
                text
            )
        )

        expected = {
            "pilotage budgétaire",
            "contrôle de gestion",
            "reporting financier",
            "analyse financière",
            "trésorerie",
            "gestion de la masse salariale",
            "indicateurs de performance",
            "sap",
            "microsoft office",
        }

        self.assertTrue(
            expected.issubset(
                skills
            ),
            msg=(
                "Compétences manquantes : "
                f"{sorted(expected - skills)}"
            ),
        )

    def test_extracts_finance_synonyms(
        self,
    ) -> None:
        text = """
        Pilotage du budget et construction budgétaire.
        Reportings financiers et suivi de trésorerie.
        Opérations de clôture et aide à la décision.
        """

        skills = set(
            self.extractor.extract(
                text
            )
        )

        self.assertIn(
            "pilotage budgétaire",
            skills,
        )

        self.assertIn(
            "gestion budgétaire",
            skills,
        )

        self.assertIn(
            "reporting financier",
            skills,
        )

        self.assertIn(
            "trésorerie",
            skills,
        )

        self.assertIn(
            "clôture comptable",
            skills,
        )

        self.assertIn(
            "analyse financière",
            skills,
        )

    def test_matching_is_case_insensitive(
        self,
    ) -> None:
        skills = set(
            self.extractor.extract(
                "SAP, sap et SaP."
            )
        )

        self.assertEqual(
            skills,
            {
                "sap",
            },
        )

    def test_does_not_match_inside_another_word(
        self,
    ) -> None:
        skills = set(
            self.extractor.extract(
                "Le mot sapin ne désigne pas SAP."
            )
        )

        self.assertIn(
            "sap",
            skills,
        )

        skills_without_explicit_sap = set(
            self.extractor.extract(
                "Le sapin est décoré."
            )
        )

        self.assertNotIn(
            "sap",
            skills_without_explicit_sap,
        )
    def test_extracts_multiword_skill_across_line_break(
        self,
    ) -> None:
        skills = set(
            self.extractor.extract(
                """
                Pilotage
                budgétaire et reporting
                financier.
                """
            )
        )

        self.assertIn(
            "pilotage budgétaire",
            skills,
        )

        self.assertIn(
            "reporting financier",
            skills,
        )

if __name__ == "__main__":
    unittest.main()