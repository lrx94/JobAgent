from __future__ import annotations

import unittest

from src.career import RoleDetector


class TestRoleDetector(unittest.TestCase):

    def setUp(self) -> None:
        self.detector = RoleDetector()

    def test_detects_cio_profile(self):
        text = """
        DSI Groupe et membre du COMEX.
        Pilotage de la transformation SI,
        gouvernance, COBIT, ITIL et management.
        """

        analysis = self.detector.analyze(
            cv_text=text,
            extracted_skills=[
                "gouvernance si",
                "transformation si",
                "cobit",
                "itil",
            ],
        )

        self.assertIsNotNone(
            analysis.primary_role
        )

        self.assertEqual(
            analysis.primary_role.role_id,
            "cio",
        )

        self.assertGreaterEqual(
            analysis.primary_role.score,
            70,
        )

    def test_detects_program_director(self):
        text = """
        Directeur de programme IT.
        Pilotage de portefeuilles,
        projets stratégiques et budgets.
        Certification PMP et PRINCE2.
        """

        analysis = self.detector.analyze(
            cv_text=text,
            extracted_skills=[
                "gestion de programme",
                "gestion de projet",
                "pmp",
                "prince2",
            ],
        )

        self.assertEqual(
            analysis.primary_role.role_id,
            "it_program_director",
        )

    def test_detects_cfo_profile(self):
        text = """
        Directeur administratif et financier.
        Contrôle de gestion, trésorerie,
        consolidation, budget et audit.
        """

        analysis = self.detector.analyze(
            cv_text=text,
            extracted_skills=[
                "finance",
                "contrôle de gestion",
                "trésorerie",
                "consolidation",
                "budget",
            ],
        )

        self.assertEqual(
            analysis.primary_role.role_id,
            "cfo",
        )

    def test_detects_executive_seniority(self):
        text = """
        Chief Information Officer,
        membre du COMEX et directeur groupe.
        """

        seniority = (
            self.detector.detect_seniority(
                text
            )
        )

        self.assertEqual(
            seniority,
            "executive",
        )

    def test_unknown_profile_returns_warning(self):
        analysis = self.detector.analyze(
            cv_text="Profil sans information exploitable.",
            extracted_skills=[],
        )

        self.assertIsNone(
            analysis.primary_role
        )

        self.assertTrue(
            analysis.warnings
        )

    def test_results_are_sorted_by_score(self):
        text = """
        DSI et directeur de programme IT.
        Gouvernance SI, transformation SI,
        COBIT, PMP et PRINCE2.
        """

        analysis = self.detector.analyze(
            cv_text=text,
            extracted_skills=[
                "gouvernance si",
                "transformation si",
                "cobit",
                "pmp",
                "prince2",
            ],
        )

        scores = [
            suggestion.score
            for suggestion
            in analysis.role_suggestions
        ]

        self.assertEqual(
            scores,
            sorted(
                scores,
                reverse=True,
            ),
        )


if __name__ == "__main__":
    unittest.main()