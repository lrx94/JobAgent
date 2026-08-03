from __future__ import annotations

import unittest

from src.career import (
    CareerProfileBuilder,
    RoleDetector,
)


class TestCareerProfileBuilder(
    unittest.TestCase
):

    def setUp(self) -> None:
        self.detector = RoleDetector()
        self.builder = CareerProfileBuilder()

    def create_analysis(self):
        return self.detector.analyze(
            cv_text=(
                "DSI Groupe, transformation SI, "
                "gouvernance, COBIT et ITIL."
            ),
            extracted_skills=[
                "gouvernance si",
                "transformation si",
                "cobit",
                "itil",
                "sql",
            ],
        )

    def test_builds_profile_from_primary_role(self):
        generated = self.builder.build(
            analysis=self.create_analysis(),
            locations=["Paris", "Remote"],
            salary_min=80000,
            remote=True,
        )

        profile = generated.profile

        self.assertEqual(
            profile.name,
            "DSI / CIO",
        )

        self.assertIn(
            "gouvernance si",
            profile.keywords,
        )

        self.assertEqual(
            profile.locations,
            ["Paris", "Remote"],
        )

        self.assertEqual(
            profile.salary_min,
            80000,
        )

        self.assertTrue(
            profile.remote
        )

    def test_can_select_another_suggested_role(self):
        analysis = self.detector.analyze(
            cv_text=(
                "DSI et directeur de programme IT. "
                "PMP, PRINCE2, transformation SI."
            ),
            extracted_skills=[
                "pmp",
                "prince2",
                "transformation si",
                "gouvernance si",
            ],
            limit=5,
        )

        role_ids = {
            item.role_id
            for item in analysis.role_suggestions
        }

        self.assertIn(
            "it_program_director",
            role_ids,
        )

        generated = self.builder.build(
            analysis=analysis,
            role_id="it_program_director",
        )

        self.assertEqual(
            generated.profile.name,
            "Directeur de programme IT",
        )

    def test_unknown_role_is_rejected(self):
        with self.assertRaises(ValueError):
            self.builder.build(
                analysis=self.create_analysis(),
                role_id="unknown-role",
            )

    def test_keywords_are_deduplicated(self):
        generated = self.builder.build(
            analysis=self.create_analysis()
        )

        keywords = generated.profile.keywords

        self.assertEqual(
            len(keywords),
            len(
                {
                    keyword.casefold()
                    for keyword in keywords
                }
            ),
        )


if __name__ == "__main__":
    unittest.main()