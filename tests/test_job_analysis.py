from __future__ import annotations

import unittest

from src.analysis import (
    JobAnalyzer,
)
from src.domain import Job


class FakeSkillExtractor:

    SKILLS = (
        "Python",
        "Azure",
        "ITIL",
        "Terraform",
    )

    def extract(
        self,
        text: str,
    ) -> list[str]:
        normalized = str(
            text or ""
        ).casefold()

        return [
            skill
            for skill in self.SKILLS
            if skill.casefold()
            in normalized
        ]


class TestJobAnalyzer(
    unittest.TestCase
):

    def setUp(self) -> None:
        self.analyzer = JobAnalyzer(
            skill_extractor=(
                FakeSkillExtractor()
            )
        )

    @staticmethod
    def create_job(
        description: str,
        *,
        title: str = "DSI Senior",
        skills: list[str] | None = None,
    ) -> Job:
        return Job(
            title=title,
            company="Example",
            location="Paris",
            description=description,
            source="France Travail",
            skills=skills or [],
        )

    def test_extracts_hard_skills(
        self,
    ):
        result = self.analyzer.analyze_job(
            self.create_job(
                "Maîtrise de Python, Azure "
                "et Terraform."
            )
        )

        self.assertIn(
            "Python",
            result.hard_skills,
        )

        self.assertIn(
            "Azure",
            result.hard_skills,
        )

        self.assertIn(
            "Terraform",
            result.hard_skills,
        )

    def test_merges_provider_skills(
        self,
    ):
        result = self.analyzer.analyze_job(
            self.create_job(
                "Poste de direction.",
                skills=[
                    "Azure",
                    "ITIL",
                ],
            )
        )

        self.assertIn(
            "Azure",
            result.hard_skills,
        )

        self.assertIn(
            "ITIL",
            result.hard_skills,
        )

    def test_detects_required_experience(
        self,
    ):
        result = self.analyzer.analyze_job(
            self.create_job(
                "Vous justifiez d'au moins "
                "10 ans d'expérience."
            )
        )

        self.assertEqual(
            result.experience[0].years,
            10.0,
        )

        self.assertTrue(
            result.experience[0].required,
        )

        self.assertEqual(
            result.experience[0]
            .evidence[0]
            .source,
            "job",
        )

    def test_detects_seniority(
        self,
    ):
        result = self.analyzer.analyze_job(
            self.create_job(
                "Nous recherchons un manager senior."
            )
        )

        self.assertEqual(
            result.seniority,
            "senior",
        )

    def test_detects_management_scope(
        self,
    ):
        result = self.analyzer.analyze_job(
            self.create_job(
                "Management d'une équipe "
                "de 20 personnes et pilotage "
                "d'un budget de 5 M€."
            )
        )

        self.assertTrue(
            result.management.required,
        )

        self.assertEqual(
            result.management.team_size,
            20,
        )

        self.assertEqual(
            result.management.budget_amount,
            5_000_000,
        )

        self.assertEqual(
            result.management
            .evidence[0]
            .source,
            "job",
        )

    def test_detects_soft_skills(
        self,
    ):
        result = self.analyzer.analyze_job(
            self.create_job(
                "Leadership, communication "
                "et gestion des parties prenantes."
            )
        )

        self.assertIn(
            "Leadership",
            result.soft_skills,
        )

        self.assertIn(
            "Communication",
            result.soft_skills,
        )

    def test_detects_itil_v4(
        self,
    ):
        result = self.analyzer.analyze_job(
            self.create_job(
                "Certification ITILV4 souhaitée."
            )
        )

        self.assertIn(
            "ITIL",
            result.certifications,
        )

    def test_detects_language(
        self,
    ):
        result = self.analyzer.analyze_job(
            self.create_job(
                "Anglais opérationnel indispensable."
            )
        )

        self.assertIn(
            "Anglais",
            result.languages,
        )

    def test_empty_requirements_return_warnings(
        self,
    ):
        result = self.analyzer.analyze_job(
            self.create_job(
                "Description générale du poste.",
                title="Poste professionnel",
            )
        )

        self.assertTrue(
            result.warnings
        )

    def test_invalid_job_is_rejected(
        self,
    ):
        with self.assertRaises(TypeError):
            self.analyzer.analyze_job(
                object()
            )

    def test_adds_business_concepts_to_job_skills(
        self,
    ):
        result = self.analyzer.analyze_job(
            self.create_job(
                "Le poste nécessite une certification "
                "ITILv4, le pilotage de projets et la "
                "gouvernance du système d'information."
            )
        )

        self.assertIn(
            "ITIL",
            result.hard_skills,
        )

        self.assertIn(
            "Gestion de projet",
            result.hard_skills,
        )

        self.assertIn(
            "Gouvernance SI",
            result.hard_skills,
        )

if __name__ == "__main__":
    unittest.main()