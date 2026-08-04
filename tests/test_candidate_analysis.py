from __future__ import annotations

import unittest

from src.analysis import (
    CandidateAnalyzer,
)
from src.career.models import (
    CareerAnalysis,
)
from src.cvs.results import (
    CVAnalysisResult,
)


class TestCandidateAnalyzer(
    unittest.TestCase
):

    def setUp(self) -> None:
        self.analyzer = (
            CandidateAnalyzer()
        )

    @staticmethod
    def create_career_analysis(
        seniority: str = "executive",
    ) -> CareerAnalysis:
        return CareerAnalysis(
            suggested_title="DSI / CIO",
            seniority=seniority,
            extracted_skills=(
                "itil",
                "cobit",
                "azure",
            ),
            role_suggestions=(),
            search_terms=(
                "DSI",
                "CIO",
            ),
            warnings=(),
        )

    def test_reuses_cv_skills(
        self,
    ):
        cv_analysis = CVAnalysisResult(
            text=(
                "DSI avec une expérience "
                "en gouvernance."
            ),
            skills=(
                "ITIL",
                "Azure",
            ),
        )

        result = self.analyzer.analyze(
            cv_analysis=cv_analysis,
            career_analysis=(
                self.create_career_analysis()
            ),
        )

        self.assertEqual(
            result.hard_skills,
            (
                "itil",
                "azure",
            ),
        )

    def test_detects_itil_v4_certification(
        self,
    ):
        cv_analysis = CVAnalysisResult(
            text=(
                "Certification ITILv4 "
                "Foundation obtenue en 2025."
            ),
            skills=(),
        )

        result = self.analyzer.analyze(
            cv_analysis=cv_analysis,
            career_analysis=(
                self.create_career_analysis()
            ),
        )

        self.assertIn(
            "ITIL",
            result.certifications,
        )

    def test_itil_detection_is_case_insensitive(
        self,
    ):
        for value in (
            "itilv4",
            "itilV4",
            "ITILV4",
            "ITILv4",
            "ITIL V4",
        ):
            with self.subTest(value=value):
                result = self.analyzer.analyze(
                    cv_analysis=(
                        CVAnalysisResult(
                            text=(
                                "Certification "
                                f"{value} Foundation."
                            ),
                        )
                    ),
                    career_analysis=(
                        self.create_career_analysis()
                    ),
                )

                self.assertIn(
                    "ITIL",
                    result.certifications,
                )

    def test_detects_total_experience(
        self,
    ):
        result = self.analyzer.analyze(
            cv_analysis=(
                CVAnalysisResult(
                    text=(
                        "DSI avec plus de "
                        "20 ans d'expérience."
                    ),
                )
            ),
            career_analysis=(
                self.create_career_analysis()
            ),
        )

        self.assertEqual(
            result.experience[0].years,
            20.0,
        )

        self.assertTrue(
            result.experience[0].evidence,
        )

    def test_detects_management_scope(
        self,
    ):
        result = self.analyzer.analyze(
            cv_analysis=(
                CVAnalysisResult(
                    text=(
                        "Management d'une équipe "
                        "de 25 personnes et pilotage "
                        "d'un budget de 4 M€."
                    ),
                )
            ),
            career_analysis=(
                self.create_career_analysis()
            ),
        )

        self.assertTrue(
            result.management.required,
        )

        self.assertEqual(
            result.management.team_size,
            25,
        )

        self.assertEqual(
            result.management.budget_amount,
            4_000_000,
        )

    def test_detects_soft_skills(
        self,
    ):
        result = self.analyzer.analyze(
            cv_analysis=(
                CVAnalysisResult(
                    text=(
                        "Leadership, communication "
                        "et gestion des parties "
                        "prenantes."
                    ),
                )
            ),
            career_analysis=(
                self.create_career_analysis()
            ),
        )

        self.assertIn(
            "Leadership",
            result.soft_skills,
        )

        self.assertIn(
            "Communication",
            result.soft_skills,
        )

        self.assertIn(
            "Gestion des parties prenantes",
            result.soft_skills,
        )

    def test_detects_language(
        self,
    ):
        result = self.analyzer.analyze(
            cv_analysis=(
                CVAnalysisResult(
                    text=(
                        "Anglais opérationnel "
                        "niveau B1+."
                    ),
                )
            ),
            career_analysis=(
                self.create_career_analysis()
            ),
        )

        self.assertIn(
            "Anglais",
            result.languages,
        )

    def test_reuses_career_seniority(
        self,
    ):
        result = self.analyzer.analyze(
            cv_analysis=(
                CVAnalysisResult(
                    text="Profil de direction."
                )
            ),
            career_analysis=(
                self.create_career_analysis(
                    seniority="executive"
                )
            ),
        )

        self.assertEqual(
            result.seniority,
            "executive",
        )

    def test_invalid_cv_analysis_is_rejected(
        self,
    ):
        with self.assertRaises(TypeError):
            self.analyzer.analyze(
                cv_analysis=object(),
            )
    def test_detects_budget_variants(
        self,
    ):
        variants = {
            "Budget de 4 M€.": 4_000_000,
            "Budget : 500 k€": 500_000,
            "Pilotage de 2 millions euros": 2_000_000,
            "Périmètre de 8 M€ OPEX": 8_000_000,
        }

        for text, expected in variants.items():
            with self.subTest(text=text):
                result = self.analyzer.analyze(
                    cv_analysis=CVAnalysisResult(
                        text=text,
                    ),
                    career_analysis=(
                        self.create_career_analysis()
                    ),
                )

                self.assertEqual(
                    result.management.budget_amount,
                    expected,
                )

if __name__ == "__main__":
    unittest.main()