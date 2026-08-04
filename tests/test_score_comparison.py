from __future__ import annotations

import unittest

from src.analysis import (
    ComparativeScoringService,
    ExperienceRequirement,
    ManagementScope,
    StructuredAnalysis,
)
from src.domain import Job


class FakeJobAnalyzer:
    def __init__(
        self,
        requirements: StructuredAnalysis,
    ) -> None:
        self.requirements = requirements
        self.jobs: list[Job] = []

    def analyze_job(
        self,
        job: Job,
    ) -> StructuredAnalysis:
        self.jobs.append(job)
        return self.requirements


class TestComparativeScoringService(
    unittest.TestCase
):

    def setUp(self) -> None:
        self.candidate = StructuredAnalysis(
            hard_skills=(
                "Azure",
                "ITIL",
                "Python",
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

        self.requirements = StructuredAnalysis(
            hard_skills=(
                "Azure",
                "ITIL",
                "COBIT",
            ),
            soft_skills=(
                "Leadership",
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

        self.job_analyzer = FakeJobAnalyzer(
            self.requirements
        )

        self.service = (
            ComparativeScoringService(
                job_analyzer=(
                    self.job_analyzer
                )
            )
        )

    @staticmethod
    def create_job(
        *,
        score: float = 72.0,
        external_id: str = "job-1",
    ) -> Job:
        return Job(
            title="DSI Senior",
            company="Example",
            location="Paris",
            description="Description",
            source="France Travail",
            external_id=external_id,
            score=score,
        )

    def test_compares_legacy_and_structured_scores(
        self,
    ):
        job = self.create_job(
            score=72.0
        )

        result = self.service.compare_job(
            candidate=self.candidate,
            job=job,
        )

        self.assertEqual(
            result.legacy_score,
            72.0,
        )

        self.assertGreater(
            result.structured_score,
            0.0,
        )

        self.assertEqual(
            result.difference,
            round(
                result.structured_score
                - 72.0,
                1,
            ),
        )

    def test_does_not_replace_legacy_job_score(
        self,
    ):
        job = self.create_job(
            score=81.0
        )

        self.service.compare_job(
            candidate=self.candidate,
            job=job,
        )

        self.assertEqual(
            job.score,
            81.0,
        )

    def test_stores_structured_details_on_job(
        self,
    ):
        job = self.create_job()

        result = self.service.compare_job(
            candidate=self.candidate,
            job=job,
        )

        details = job.match_details[
            "structured"
        ]

        self.assertEqual(
            details["legacy_score"],
            72.0,
        )

        self.assertEqual(
            details["global_score"],
            result.structured_score,
        )

        self.assertTrue(
            details["dimensions"]
        )

        self.assertIn(
            "requirements",
            details,
        )

    def test_serializes_dimension_gaps(
        self,
    ):
        job = self.create_job()

        self.service.compare_job(
            candidate=self.candidate,
            job=job,
        )

        details = job.match_details[
            "structured"
        ]

        hard_skills = next(
            item
            for item
            in details["dimensions"]
            if item["name"]
            == "hard_skills"
        )

        self.assertIn(
            "COBIT",
            hard_skills["missing"],
        )

    def test_compares_multiple_jobs(
        self,
    ):
        jobs = [
            self.create_job(
                external_id="job-1",
            ),
            self.create_job(
                external_id="job-2",
                score=60.0,
            ),
        ]

        results = self.service.compare(
            candidate=self.candidate,
            jobs=jobs,
        )

        self.assertEqual(
            len(results),
            2,
        )

        self.assertEqual(
            len(self.job_analyzer.jobs),
            2,
        )

    def test_invalid_candidate_is_rejected(
        self,
    ):
        with self.assertRaises(TypeError):
            self.service.compare(
                candidate=object(),
                jobs=[],
            )

    def test_invalid_job_is_rejected(
        self,
    ):
        with self.assertRaises(TypeError):
            self.service.compare_job(
                candidate=self.candidate,
                job=object(),
            )


if __name__ == "__main__":
    unittest.main()