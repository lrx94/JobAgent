import unittest
from dataclasses import dataclass

from src.domain import Job
from src.profile import Profile
from src.search_request import SearchRequest
from src.services.job_aggregator import JobAggregator
from src.services.job_service import JobService


@dataclass
class ScoredMatchResult:
    score: float
    matched_skills: list[str]
    missing_skills: list[str]
    details: dict
    explanation: str = ""


class ScoreByTitleEngine:
    """
    Moteur de matching déterministe pour les tests.
    """

    def match(
        self,
        profile: Profile,
        job: Job,
    ) -> ScoredMatchResult:
        score = (
            90
            if "Senior" in job.title
            else 60
        )

        return ScoredMatchResult(
            score=score,
            matched_skills=["Python"],
            missing_skills=[],
            details={
                "title_score": score,
            },
            explanation=(
                f"Score calculé pour {job.title}"
            ),
        )


class FirstProvider:

    name = "FirstProvider"

    def search(
        self,
        request: SearchRequest,
    ) -> list[Job]:
        return [
            Job(
                external_id="job-1",
                title="Python Developer",
                company="Example",
                location="Paris",
                description="Python SQL",
                source="FirstProvider",
                url="https://example.com/job-1",
            ),
            Job(
                external_id="job-2",
                title="Senior Python Developer",
                company="Example",
                location="Paris",
                description="Python architecture",
                source="FirstProvider",
                url="https://example.com/job-2",
            ),
        ]


class DuplicateProvider:

    name = "DuplicateProvider"

    def search(
        self,
        request: SearchRequest,
    ) -> list[Job]:
        return [
            Job(
                external_id="job-1",
                title="Python Developer duplicate",
                company="Example",
                location="Paris",
                description="Duplicate",
                source="FirstProvider",
                url=(
                    "https://example.com/"
                    "job-1-duplicate"
                ),
            ),
        ]


class BrokenProvider:

    name = "BrokenProvider"

    def search(
        self,
        request: SearchRequest,
    ) -> list[Job]:
        raise RuntimeError(
            "Erreur réseau simulée"
        )


class TestJobServiceAggregation(unittest.TestCase):

    def setUp(self):
        self.profile = Profile(
            name="Python Engineer",
            keywords=["Python"],
            locations=["Paris"],
            salary_min=60000,
            remote=True,
        )

    def test_service_uses_job_aggregator(self):
        aggregator = JobAggregator(
            [
                FirstProvider(),
                DuplicateProvider(),
            ]
        )

        service = JobService(
            aggregator=aggregator,
            engine=ScoreByTitleEngine(),
        )

        jobs = service.search(
            self.profile
        )

        self.assertEqual(len(jobs), 2)

        self.assertEqual(
            jobs[0].title,
            "Senior Python Developer",
        )

        self.assertEqual(
            jobs[0].score,
            90,
        )

        self.assertEqual(
            jobs[1].score,
            60,
        )

        self.assertIsNotNone(
            service.last_aggregation_result
        )

    def test_statistics_are_preserved(self):
        aggregator = JobAggregator(
            [
                FirstProvider(),
                DuplicateProvider(),
            ]
        )

        service = JobService(
            aggregator=aggregator,
            engine=ScoreByTitleEngine(),
        )

        service.search(self.profile)

        statistics = service.collection_stats

        self.assertEqual(
            statistics["total_collected"],
            3,
        )

        self.assertEqual(
            statistics["total_unique"],
            2,
        )

        self.assertEqual(
            statistics["duplicates_removed"],
            1,
        )

        self.assertEqual(
            statistics["successful_providers"],
            2,
        )

    def test_provider_errors_are_exposed(self):
        aggregator = JobAggregator(
            [
                BrokenProvider(),
                FirstProvider(),
            ]
        )

        service = JobService(
            aggregator=aggregator,
            engine=ScoreByTitleEngine(),
        )

        jobs = service.search(
            self.profile
        )

        self.assertEqual(len(jobs), 2)

        self.assertEqual(
            service.collection_stats["errors"],
            1,
        )

        self.assertEqual(
            len(service.provider_errors),
            1,
        )

        self.assertIn(
            "BrokenProvider",
            service.provider_errors[0],
        )

        self.assertIn(
            "Erreur réseau simulée",
            service.provider_errors[0],
        )

    def test_search_jobs_does_not_apply_matching(self):
        aggregator = JobAggregator(
            [FirstProvider()]
        )

        service = JobService(
            aggregator=aggregator,
            engine=ScoreByTitleEngine(),
        )

        request = SearchRequest.from_profile(
            self.profile
        )

        jobs = service.search_jobs(request)

        self.assertEqual(len(jobs), 2)

        self.assertEqual(
            jobs[0].score,
            0,
        )

        self.assertEqual(
            jobs[1].score,
            0,
        )

    def test_empty_stats_before_first_search(self):
        service = JobService(
            aggregator=JobAggregator([]),
            engine=ScoreByTitleEngine(),
        )

        statistics = service.collection_stats

        self.assertEqual(
            statistics["total_collected"],
            0,
        )

        self.assertEqual(
            statistics["total_unique"],
            0,
        )

        self.assertEqual(
            statistics["providers"],
            {},
        )

    def test_rejects_providers_and_aggregator_together(self):
        aggregator = JobAggregator(
            [FirstProvider()]
        )

        with self.assertRaises(ValueError):
            JobService(
                providers=[FirstProvider()],
                aggregator=aggregator,
                engine=ScoreByTitleEngine(),
            )


if __name__ == "__main__":
    unittest.main()