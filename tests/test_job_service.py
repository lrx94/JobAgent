import unittest
from dataclasses import dataclass

from src.domain import Job
from src.profile import Profile
from src.providers.base import JobProvider
from src.search_request import SearchRequest
from src.services.job_service import JobService


class FakeProvider(JobProvider):

    name = "FakeProvider"

    def search(
        self,
        request: SearchRequest,
    ) -> list[Job]:
        return [
            Job(
                external_id="1",
                title="Data Engineer",
                company="Example",
                location=request.primary_location,
                description="Python SQL",
                source="Fake",
                url="https://example.com/1",
            ),
            Job(
                external_id="1",
                title="Data Engineer duplicate",
                company="Example",
                location=request.primary_location,
                description="Duplicate",
                source="Fake",
                url=(
                    "https://example.com/duplicate"
                ),
            ),
        ]


class FailingProvider(JobProvider):

    name = "FailingProvider"

    def search(
        self,
        request: SearchRequest,
    ) -> list[Job]:
        raise RuntimeError(
            "Provider indisponible"
        )


@dataclass
class FakeMatchResult:
    score: float
    matched_skills: list[str]
    missing_skills: list[str]
    details: dict
    explanation: str = ""


class FakeMatchingEngine:

    def match(
        self,
        profile,
        job,
    ) -> FakeMatchResult:
        return FakeMatchResult(
            score=75,
            matched_skills=["Python"],
            missing_skills=["Spark"],
            details={
                "skills": 75,
            },
            explanation="Test",
        )


class TestJobService(unittest.TestCase):

    def setUp(self):
        self.profile = Profile(
            name="Data Engineer",
            keywords=[
                "Python",
                "Spark",
            ],
            locations=["Paris"],
            salary_min=65000,
            remote=True,
        )

    def test_search_collects_matches_and_sorts(self):
        service = JobService(
            providers=[FakeProvider()],
            engine=FakeMatchingEngine(),
        )

        jobs = service.search(
            self.profile
        )

        self.assertEqual(len(jobs), 1)

        job = jobs[0]

        self.assertEqual(job.score, 75)

        self.assertEqual(
            job.matched_skills,
            ["Python"],
        )

        self.assertEqual(
            job.missing_skills,
            ["Spark"],
        )

        self.assertEqual(
            job.match_details,
            {"skills": 75},
        )

        self.assertEqual(
            job.explanation,
            "Test",
        )

    def test_provider_error_does_not_stop_search(self):
        service = JobService(
            providers=[
                FailingProvider(),
                FakeProvider(),
            ],
            engine=FakeMatchingEngine(),
        )

        jobs = service.search(
            self.profile
        )

        self.assertEqual(len(jobs), 1)

        self.assertEqual(
            len(service.provider_errors),
            1,
        )

        self.assertIn(
            "Provider indisponible",
            service.provider_errors[0],
        )

    def test_collection_stats_are_available(self):
        service = JobService(
            providers=[FakeProvider()],
            engine=FakeMatchingEngine(),
        )

        service.search(self.profile)

        statistics = service.collection_stats

        self.assertEqual(
            statistics["total_collected"],
            2,
        )

        self.assertEqual(
            statistics["total_unique"],
            1,
        )

        self.assertEqual(
            statistics["duplicates_removed"],
            1,
        )

        self.assertEqual(
            statistics["errors"],
            0,
        )


if __name__ == "__main__":
    unittest.main()