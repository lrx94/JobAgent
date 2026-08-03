from __future__ import annotations

import unittest
from types import SimpleNamespace

from src.market import (
    MarketProfileSkillResolver,
)


class FakeCVService:
    def __init__(
        self,
        *,
        skills=(),
        error: Exception | None = None,
    ) -> None:
        self.skills = tuple(skills)
        self.error = error
        self.analyzed_cv_ids: list[str] = []

    def analyze(
        self,
        cv_id: str,
    ):
        self.analyzed_cv_ids.append(
            cv_id
        )

        if self.error is not None:
            raise self.error

        return SimpleNamespace(
            skills=self.skills
        )


class TestMarketProfileSkillResolver(
    unittest.TestCase
):

    def test_uses_primary_cv_skills(
        self,
    ):
        cv_service = FakeCVService(
            skills=(
                "Azure",
                "ITIL",
                "Gouvernance SI",
            )
        )

        resolver = (
            MarketProfileSkillResolver(
                cv_service=cv_service
            )
        )

        result = resolver.resolve(
            primary_cv_id="cv-123",
            fallback_keywords=(
                "DSI",
                "CIO",
            ),
        )

        self.assertEqual(
            result.source,
            "cv",
        )

        self.assertEqual(
            result.cv_id,
            "cv-123",
        )

        self.assertEqual(
            result.skills,
            (
                "Azure",
                "ITIL",
                "Gouvernance SI",
            ),
        )

        self.assertEqual(
            cv_service.analyzed_cv_ids,
            ["cv-123"],
        )

        self.assertFalse(
            result.warnings
        )

    def test_cv_skills_take_priority_over_keywords(
        self,
    ):
        resolver = (
            MarketProfileSkillResolver(
                cv_service=FakeCVService(
                    skills=(
                        "Azure",
                        "ITIL",
                    )
                )
            )
        )

        result = resolver.resolve(
            primary_cv_id="cv-123",
            fallback_keywords=(
                "Python",
                "SQL",
            ),
        )

        self.assertEqual(
            result.skills,
            (
                "Azure",
                "ITIL",
            ),
        )

        self.assertNotIn(
            "Python",
            result.skills,
        )

    def test_uses_keywords_without_primary_cv(
        self,
    ):
        resolver = (
            MarketProfileSkillResolver(
                cv_service=FakeCVService()
            )
        )

        result = resolver.resolve(
            primary_cv_id=None,
            fallback_keywords=(
                "DSI",
                "Transformation SI",
            ),
        )

        self.assertEqual(
            result.source,
            "keywords",
        )

        self.assertEqual(
            result.skills,
            (
                "DSI",
                "Transformation SI",
            ),
        )

        self.assertTrue(
            result.warnings
        )

    def test_uses_keywords_when_cv_has_no_skills(
        self,
    ):
        resolver = (
            MarketProfileSkillResolver(
                cv_service=FakeCVService(
                    skills=()
                )
            )
        )

        result = resolver.resolve(
            primary_cv_id="cv-empty",
            fallback_keywords=(
                "DSI",
                "CIO",
            ),
        )

        self.assertEqual(
            result.source,
            "keywords",
        )

        self.assertEqual(
            result.skills,
            (
                "DSI",
                "CIO",
            ),
        )

        self.assertTrue(
            result.warnings
        )

    def test_uses_keywords_when_cv_analysis_fails(
        self,
    ):
        resolver = (
            MarketProfileSkillResolver(
                cv_service=FakeCVService(
                    error=RuntimeError(
                        "PDF invalide"
                    )
                )
            )
        )

        result = resolver.resolve(
            primary_cv_id="cv-error",
            fallback_keywords=(
                "Azure",
                "Cloud",
            ),
        )

        self.assertEqual(
            result.source,
            "keywords",
        )

        self.assertEqual(
            result.skills,
            (
                "Azure",
                "Cloud",
            ),
        )

        self.assertTrue(
            result.warnings
        )

    def test_returns_none_without_any_skills(
        self,
    ):
        resolver = (
            MarketProfileSkillResolver(
                cv_service=FakeCVService()
            )
        )

        result = resolver.resolve(
            primary_cv_id=None,
            fallback_keywords=(),
        )

        self.assertEqual(
            result.source,
            "none",
        )

        self.assertEqual(
            result.skills,
            (),
        )

        self.assertTrue(
            result.warnings
        )

    def test_normalizes_duplicates(
        self,
    ):
        resolver = (
            MarketProfileSkillResolver(
                cv_service=FakeCVService(
                    skills=(
                        "Azure",
                        " azure ",
                        "ITIL",
                        "",
                    )
                )
            )
        )

        result = resolver.resolve(
            primary_cv_id="cv-123",
            fallback_keywords=(),
        )

        self.assertEqual(
            result.skills,
            (
                "Azure",
                "ITIL",
            ),
        )


if __name__ == "__main__":
    unittest.main()