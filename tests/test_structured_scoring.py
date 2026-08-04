from __future__ import annotations

import unittest

from src.analysis import (
    ExperienceRequirement,
    ManagementScope,
    StructuredAnalysis,
    StructuredScorer,
)


class TestStructuredScorer(
    unittest.TestCase
):

    def setUp(self) -> None:
        self.scorer = StructuredScorer()

    @staticmethod
    def candidate() -> StructuredAnalysis:
        return StructuredAnalysis(
            hard_skills=(
                "Python",
                "Azure",
                "ITIL",
            ),
            soft_skills=(
                "Leadership",
            ),
            seniority="executive",
            experience=(
                ExperienceRequirement(
                    years=20,
                ),
            ),
            management=ManagementScope(
                required=True,
                team_size=25,
            ),
            certifications=(
                "ITIL",
            ),
            languages=(
                "Anglais",
            ),
        )

    @staticmethod
    def requirements() -> StructuredAnalysis:
        return StructuredAnalysis(
            hard_skills=(
                "Azure",
                "ITIL",
                "COBIT",
            ),
            soft_skills=(
                "Leadership",
                "Communication",
            ),
            seniority="senior",
            experience=(
                ExperienceRequirement(
                    years=10,
                    required=True,
                ),
            ),
            management=ManagementScope(
                required=True,
                team_size=20,
            ),
            certifications=(
                "ITIL",
            ),
            languages=(
                "Anglais",
            ),
        )

    def test_scores_hard_skills(self):
        result = self.scorer.score(
            candidate=self.candidate(),
            requirements=self.requirements(),
        )

        dimension = next(
            item
            for item in result.dimensions
            if item.name == "hard_skills"
        )

        self.assertEqual(
            round(dimension.score, 1),
            66.7,
        )

        self.assertIn(
            "COBIT",
            dimension.missing,
        )

    def test_experience_is_satisfied(self):
        result = self.scorer.score(
            candidate=self.candidate(),
            requirements=self.requirements(),
        )

        dimension = next(
            item
            for item in result.dimensions
            if item.name == "experience"
        )

        self.assertEqual(
            dimension.score,
            100.0,
        )

    def test_higher_seniority_is_accepted(self):
        result = self.scorer.score(
            candidate=self.candidate(),
            requirements=self.requirements(),
        )

        dimension = next(
            item
            for item in result.dimensions
            if item.name == "seniority"
        )

        self.assertEqual(
            dimension.score,
            100.0,
        )

    def test_management_scope_is_satisfied(self):
        result = self.scorer.score(
            candidate=self.candidate(),
            requirements=self.requirements(),
        )

        dimension = next(
            item
            for item in result.dimensions
            if item.name == "management"
        )

        self.assertEqual(
            dimension.score,
            100.0,
        )

    def test_global_score_is_bounded(self):
        result = self.scorer.score(
            candidate=self.candidate(),
            requirements=self.requirements(),
        )

        self.assertGreaterEqual(
            result.global_score,
            0.0,
        )

        self.assertLessEqual(
            result.global_score,
            100.0,
        )

    def test_gaps_are_exposed(self):
        result = self.scorer.score(
            candidate=self.candidate(),
            requirements=self.requirements(),
        )

        self.assertIn(
            "COBIT",
            result.gaps,
        )

        self.assertIn(
            "Communication",
            result.gaps,
        )

    def test_missing_experience_scores_zero(self):
        result = self.scorer.score(
            candidate=StructuredAnalysis(),
            requirements=StructuredAnalysis(
                experience=(
                    ExperienceRequirement(
                        years=5,
                        required=True,
                    ),
                ),
            ),
        )

        dimension = next(
            item
            for item in result.dimensions
            if item.name == "experience"
        )

        self.assertEqual(
            dimension.score,
            0.0,
        )

    def test_invalid_candidate_is_rejected(self):
        with self.assertRaises(TypeError):
            self.scorer.score(
                candidate=object(),
                requirements=self.requirements(),
            )


if __name__ == "__main__":
    unittest.main()