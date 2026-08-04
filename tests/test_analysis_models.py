from __future__ import annotations

import unittest

from src.analysis import (
    Evidence,
    ExperienceRequirement,
    ManagementScope,
    StructuredAnalysis,
)


class TestEvidence(
    unittest.TestCase
):

    def test_normalizes_values(self):
        evidence = Evidence(
            value=" ITIL ",
            source="CV",
            excerpt=" Certification ITIL V4 ",
            confidence=1.4,
            reference_id=" cv-123 ",
        )

        self.assertEqual(
            evidence.value,
            "ITIL",
        )

        self.assertEqual(
            evidence.source,
            "cv",
        )

        self.assertEqual(
            evidence.excerpt,
            "Certification ITIL V4",
        )

        self.assertEqual(
            evidence.confidence,
            1.0,
        )

        self.assertEqual(
            evidence.reference_id,
            "cv-123",
        )

    def test_empty_value_is_rejected(self):
        with self.assertRaises(ValueError):
            Evidence(value="")


class TestAnalysisModels(
    unittest.TestCase
):

    def test_experience_normalizes_negative_years(self):
        experience = ExperienceRequirement(
            years=-5,
            domain=" Direction SI ",
            required=True,
        )

        self.assertEqual(
            experience.years,
            0.0,
        )

        self.assertEqual(
            experience.domain,
            "Direction SI",
        )

        self.assertTrue(
            experience.required,
        )

    def test_management_scope_normalizes_values(self):
        scope = ManagementScope(
            required=True,
            team_size=-10,
            budget_amount=2_000_000,
        )

        self.assertTrue(
            scope.required,
        )

        self.assertEqual(
            scope.team_size,
            0,
        )

        self.assertEqual(
            scope.budget_amount,
            2_000_000,
        )

    def test_structured_analysis_deduplicates_values(self):
        analysis = StructuredAnalysis(
            hard_skills=(
                "ITIL",
                " itil ",
                "Azure",
            ),
            soft_skills=(
                "Leadership",
                "leadership",
            ),
            seniority="EXECUTIVE",
            certifications=(
                "ITIL V4",
                "itil v4",
            ),
        )

        self.assertEqual(
            analysis.hard_skills,
            (
                "ITIL",
                "Azure",
            ),
        )

        self.assertEqual(
            analysis.soft_skills,
            (
                "Leadership",
            ),
        )

        self.assertEqual(
            analysis.seniority,
            "executive",
        )

        self.assertEqual(
            analysis.certifications,
            (
                "ITIL V4",
            ),
        )

    def test_unknown_seniority_is_safe(self):
        analysis = StructuredAnalysis(
            seniority="wizard",
        )

        self.assertEqual(
            analysis.seniority,
            "unknown",
        )

    def test_evidence_can_be_attached(self):
        evidence = Evidence(
            value="10 ans",
            source="job",
            excerpt=(
                "Vous justifiez de 10 ans "
                "d'expérience."
            ),
            confidence=0.95,
        )

        analysis = StructuredAnalysis(
            experience=(
                ExperienceRequirement(
                    years=10,
                    required=True,
                    evidence=(
                        evidence,
                    ),
                ),
            ),
            evidence=(
                evidence,
            ),
        )

        self.assertEqual(
            analysis.experience[0].years,
            10.0,
        )

        self.assertEqual(
            analysis.evidence[0],
            evidence,
        )


if __name__ == "__main__":
    unittest.main()