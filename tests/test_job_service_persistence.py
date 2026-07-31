from __future__ import annotations

import unittest
from dataclasses import dataclass, field
from typing import Any
from unittest.mock import patch

from src.domain import Job
from src.services.job_service import JobService


@dataclass
class FakeMatchResult:
    score: float = 75.0
    matched_skills: list[str] = field(
        default_factory=lambda: [
            "Python",
            "SQL",
        ]
    )
    missing_skills: list[str] = field(
        default_factory=lambda: [
            "Spark",
        ]
    )
    details: dict[str, Any] = field(
        default_factory=lambda: {
            "skills_score": 75,
        }
    )
    explanation: str = "Bon niveau de correspondance."


class FakeMatchingEngine:
    def match(
        self,
        profile,
        job: Job,
    ) -> FakeMatchResult:
        return FakeMatchResult()


class FakeRegistry:
    def __init__(
        self,
        providers=None,
    ) -> None:
        self._providers = list(
            providers or []
        )

    def all(self):
        return list(self._providers)


class FakeProviderStats:
    def __init__(
        self,
        error: str | None = None,
    ) -> None:
        self.error = error


class FakeAggregationResult:
    def __init__(
        self,
        jobs: list[Job],
    ) -> None:
        self.jobs = jobs
        self.provider_stats = {
            "FakeProvider": FakeProviderStats(),
        }

    def to_dict(self) -> dict[str, Any]:
        return {
            "total_collected": len(self.jobs),
            "total_unique": len(self.jobs),
            "duplicates_removed": 0,
            "invalid_jobs_removed": 0,
            "errors": 0,
            "successful_providers": 1,
            "failed_providers": 0,
            "providers": {
                "FakeProvider": {
                    "collected": len(self.jobs),
                    "error": None,
                }
            },
        }


class FakeAggregator:
    def __init__(
        self,
        jobs: list[Job],
    ) -> None:
        self.jobs = jobs
        self.registry = FakeRegistry()

    def collect(
        self,
        request,
    ) -> FakeAggregationResult:
        return FakeAggregationResult(
            list(self.jobs)
        )


class FakeRepository:
    def __init__(self) -> None:
        self.saved_jobs: list[Job] = []

    def save(
        self,
        job: Job,
    ) -> None:
        self.saved_jobs.append(job)


class FailingRepository:
    def __init__(self) -> None:
        self.calls = 0

    def save(
        self,
        job: Job,
    ) -> None:
        self.calls += 1

        raise RuntimeError(
            "Base SQLite indisponible"
        )


class PartiallyFailingRepository:
    def __init__(self) -> None:
        self.saved_jobs: list[Job] = []

    def save(
        self,
        job: Job,
    ) -> None:
        if job.external_id == "failure":
            raise RuntimeError(
                "Échec simulé"
            )

        self.saved_jobs.append(job)


def create_job(
    external_id: str,
    title: str = "Data Engineer",
) -> Job:
    return Job(
        external_id=external_id,
        title=title,
        company="Example",
        location="Paris",
        description="Python SQL",
        source="FakeProvider",
        url=(
            "https://example.com/jobs/"
            f"{external_id}"
        ),
    )


class TestJobServicePersistence(unittest.TestCase):

    def test_persists_every_matched_job(self):
        jobs = [
            create_job("job-1"),
            create_job("job-2"),
        ]

        repository = FakeRepository()

        service = JobService(
            aggregator=FakeAggregator(jobs),
            engine=FakeMatchingEngine(),
            repository=repository,
            persistence_enabled=True,
        )

        with patch(
            "src.services.job_service."
            "SearchRequest.from_profile",
            return_value=object(),
        ):
            results = service.search(
                profile=object()
            )

        self.assertEqual(
            len(results),
            2,
        )

        self.assertEqual(
            len(repository.saved_jobs),
            2,
        )

        self.assertEqual(
            repository.saved_jobs[0].score,
            75.0,
        )

        self.assertEqual(
            repository.saved_jobs[0].matched_skills,
            ["Python", "SQL"],
        )

        self.assertEqual(
            service.persistence_stats,
            {
                "enabled": True,
                "attempted": 2,
                "saved": 2,
                "failed": 0,
            },
        )

        self.assertEqual(
            service.persistence_errors,
            [],
        )

    def test_does_not_persist_when_disabled(self):
        jobs = [
            create_job("job-1"),
        ]

        repository = FakeRepository()

        service = JobService(
            aggregator=FakeAggregator(jobs),
            engine=FakeMatchingEngine(),
            repository=repository,
            persistence_enabled=False,
        )

        with patch(
            "src.services.job_service."
            "SearchRequest.from_profile",
            return_value=object(),
        ):
            results = service.search(
                profile=object()
            )

        self.assertEqual(
            len(results),
            1,
        )

        self.assertEqual(
            repository.saved_jobs,
            [],
        )

        self.assertEqual(
            service.persistence_stats,
            {
                "enabled": False,
                "attempted": 0,
                "saved": 0,
                "failed": 0,
            },
        )

    def test_repository_failure_does_not_stop_search(self):
        jobs = [
            create_job("job-1"),
            create_job("job-2"),
        ]

        repository = FailingRepository()

        service = JobService(
            aggregator=FakeAggregator(jobs),
            engine=FakeMatchingEngine(),
            repository=repository,
            persistence_enabled=True,
        )

        with patch(
            "src.services.job_service."
            "SearchRequest.from_profile",
            return_value=object(),
        ):
            results = service.search(
                profile=object()
            )

        self.assertEqual(
            len(results),
            2,
        )

        self.assertEqual(
            repository.calls,
            2,
        )

        self.assertEqual(
            service.persistence_stats,
            {
                "enabled": True,
                "attempted": 2,
                "saved": 0,
                "failed": 2,
            },
        )

        self.assertEqual(
            len(service.persistence_errors),
            2,
        )

        self.assertIn(
            "Base SQLite indisponible",
            service.persistence_errors[0],
        )

    def test_failure_is_isolated_to_one_job(self):
        jobs = [
            create_job("success-1"),
            create_job("failure"),
            create_job("success-2"),
        ]

        repository = PartiallyFailingRepository()

        service = JobService(
            aggregator=FakeAggregator(jobs),
            engine=FakeMatchingEngine(),
            repository=repository,
            persistence_enabled=True,
        )

        with patch(
            "src.services.job_service."
            "SearchRequest.from_profile",
            return_value=object(),
        ):
            results = service.search(
                profile=object()
            )

        self.assertEqual(
            len(results),
            3,
        )

        self.assertEqual(
            [
                job.external_id
                for job in repository.saved_jobs
            ],
            [
                "success-1",
                "success-2",
            ],
        )

        self.assertEqual(
            service.persistence_stats,
            {
                "enabled": True,
                "attempted": 3,
                "saved": 2,
                "failed": 1,
            },
        )

        self.assertEqual(
            len(service.persistence_errors),
            1,
        )

        self.assertIn(
            "FakeProvider:failure",
            service.persistence_errors[0],
        )

    def test_search_jobs_does_not_persist(self):
        jobs = [
            create_job("job-1"),
        ]

        repository = FakeRepository()

        service = JobService(
            aggregator=FakeAggregator(jobs),
            engine=FakeMatchingEngine(),
            repository=repository,
            persistence_enabled=True,
        )

        results = service.search_jobs(
            request=object()
        )

        self.assertEqual(
            len(results),
            1,
        )

        self.assertEqual(
            repository.saved_jobs,
            [],
        )

        self.assertEqual(
            service.persistence_stats,
            {
                "enabled": True,
                "attempted": 0,
                "saved": 0,
                "failed": 0,
            },
        )

    def test_results_remain_sorted_by_score(self):
        first_job = create_job(
            "job-1",
            title="First",
        )

        second_job = create_job(
            "job-2",
            title="Second",
        )

        class VariableMatchingEngine:
            def match(
                self,
                profile,
                job: Job,
            ) -> FakeMatchResult:
                score = (
                    90.0
                    if job.title == "Second"
                    else 25.0
                )

                return FakeMatchResult(
                    score=score
                )

        repository = FakeRepository()

        service = JobService(
            aggregator=FakeAggregator(
                [
                    first_job,
                    second_job,
                ]
            ),
            engine=VariableMatchingEngine(),
            repository=repository,
            persistence_enabled=True,
        )

        with patch(
            "src.services.job_service."
            "SearchRequest.from_profile",
            return_value=object(),
        ):
            results = service.search(
                profile=object()
            )

        self.assertEqual(
            [
                job.title
                for job in results
            ],
            [
                "Second",
                "First",
            ],
        )

        self.assertEqual(
            len(repository.saved_jobs),
            2,
        )


if __name__ == "__main__":
    unittest.main()