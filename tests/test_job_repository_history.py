from __future__ import annotations

import tempfile
import unittest
from datetime import datetime
from pathlib import Path
from unittest.mock import patch

from src.domain import Job
from src.storage.repository import JobRepository


def create_job(
    external_id: str,
    *,
    title: str = "Data Engineer",
    description: str = "Python SQL",
    source: str = "FakeProvider",
    score: float = 75,
    remote_type: str = "hybrid",
) -> Job:
    normalized_source = (
        source.lower()
        .replace(" ", "-")
    )

    return Job(
        external_id=external_id,
        title=title,
        company="Example",
        location="Paris",
        description=description,
        source=source,
        url=(
            f"https://{normalized_source}.example.com/"
            f"jobs/{external_id}"
        ),
        remote_type=remote_type,
        score=score,
        matched_skills=[
            "Python",
            "SQL",
        ],
        missing_skills=[
            "Spark",
        ],
        collected_at=datetime.now(),
    )


class TestJobRepositoryHistory(
    unittest.TestCase
):

    def setUp(self) -> None:
        self.temporary_directory = (
            tempfile.TemporaryDirectory()
        )

        self.database_path = (
            Path(
                self.temporary_directory.name
            )
            / "jobagent-test.db"
        )

        self.database_patch = patch(
            "src.storage.database.DB_PATH",
            self.database_path,
        )

        self.database_patch.start()

        self.repository = JobRepository()

    def tearDown(self) -> None:
        self.database_patch.stop()
        self.temporary_directory.cleanup()

    def test_first_save_is_inserted(self):
        job = create_job("job-1")

        result = self.repository.save(job)

        self.assertEqual(
            result.action,
            "inserted",
        )

        self.assertEqual(
            result.seen_count,
            1,
        )

        self.assertGreater(
            result.job_id,
            0,
        )

        self.assertEqual(
            self.repository.count(),
            1,
        )

        metadata = (
            self.repository
            .get_job_metadata(job)
        )

        self.assertIsNotNone(metadata)

        self.assertEqual(
            metadata["last_action"],
            "inserted",
        )

        self.assertEqual(
            metadata["seen_count"],
            1,
        )

    def test_identical_save_is_unchanged(self):
        first_job = create_job("job-1")

        first_result = (
            self.repository.save(first_job)
        )

        second_job = create_job("job-1")

        second_result = (
            self.repository.save(second_job)
        )

        self.assertEqual(
            second_result.action,
            "unchanged",
        )

        self.assertEqual(
            second_result.job_id,
            first_result.job_id,
        )

        self.assertEqual(
            second_result.seen_count,
            2,
        )

        self.assertEqual(
            self.repository.count(),
            1,
        )

        metadata = (
            self.repository
            .get_job_metadata(second_job)
        )

        self.assertEqual(
            metadata["last_action"],
            "unchanged",
        )

        self.assertEqual(
            metadata["seen_count"],
            2,
        )

    def test_changed_description_is_updated(self):
        original = create_job(
            "job-1",
            description="Python SQL",
        )

        self.repository.save(original)

        changed = create_job(
            "job-1",
            description=(
                "Python SQL Spark Azure"
            ),
        )

        result = self.repository.save(
            changed
        )

        self.assertEqual(
            result.action,
            "updated",
        )

        self.assertEqual(
            result.seen_count,
            2,
        )

        jobs = self.repository.get_all()

        self.assertEqual(
            len(jobs),
            1,
        )

        self.assertEqual(
            jobs[0].description,
            "Python SQL Spark Azure",
        )

        metadata = (
            self.repository
            .get_job_metadata(changed)
        )

        self.assertEqual(
            metadata["last_action"],
            "updated",
        )

    def test_changed_score_is_updated(self):
        original = create_job(
            "job-1",
            score=50,
        )

        self.repository.save(original)

        rescored = create_job(
            "job-1",
            score=90,
        )

        result = self.repository.save(
            rescored
        )

        self.assertEqual(
            result.action,
            "updated",
        )

        best_jobs = (
            self.repository.get_best_jobs(
                limit=1
            )
        )

        self.assertEqual(
            best_jobs[0].score,
            90,
        )

    def test_new_jobs_returns_recent_insertions(self):
        self.repository.save(
            create_job("job-1")
        )

        jobs = (
            self.repository.get_new_jobs(
                days=1
            )
        )

        self.assertEqual(
            len(jobs),
            1,
        )

        self.assertEqual(
            jobs[0].external_id,
            "job-1",
        )

    def test_updated_jobs_returns_modified_jobs(self):
        original = create_job(
            "job-1",
            title="Data Engineer",
        )

        self.repository.save(original)

        updated = create_job(
            "job-1",
            title="Senior Data Engineer",
        )

        self.repository.save(updated)

        jobs = (
            self.repository
            .get_updated_jobs(days=1)
        )

        self.assertEqual(
            len(jobs),
            1,
        )

        self.assertEqual(
            jobs[0].title,
            "Senior Data Engineer",
        )

    def test_unchanged_job_is_not_updated_job(self):
        self.repository.save(
            create_job("job-1")
        )

        self.repository.save(
            create_job("job-1")
        )

        updated_jobs = (
            self.repository
            .get_updated_jobs(days=1)
        )

        self.assertEqual(
            updated_jobs,
            [],
        )

    def test_recent_jobs_returns_seen_jobs(self):
        self.repository.save(
            create_job("job-1")
        )

        recent_jobs = (
            self.repository
            .get_recent_jobs(days=7)
        )

        self.assertEqual(
            len(recent_jobs),
            1,
        )

    def test_best_jobs_respects_limit_and_score(self):
        self.repository.save(
            create_job(
                "job-1",
                score=40,
            )
        )

        self.repository.save(
            create_job(
                "job-2",
                score=95,
            )
        )

        self.repository.save(
            create_job(
                "job-3",
                score=80,
            )
        )

        jobs = (
            self.repository.get_best_jobs(
                limit=2,
                minimum_score=50,
            )
        )

        self.assertEqual(
            len(jobs),
            2,
        )

        self.assertEqual(
            [
                job.external_id
                for job in jobs
            ],
            [
                "job-2",
                "job-3",
            ],
        )

    def test_statistics_are_grouped_by_source(self):
        self.repository.save(
            create_job(
                "job-1",
                source="FranceTravail",
                score=90,
                remote_type="remote",
            )
        )

        self.repository.save(
            create_job(
                "job-2",
                source="FranceTravail",
                score=70,
            )
        )

        self.repository.save(
            create_job(
                "job-3",
                source="RemoteOK",
                score=80,
                remote_type="remote",
            )
        )

        statistics = (
            self.repository.get_statistics()
        )

        self.assertEqual(
            statistics["total_jobs"],
            3,
        )

        self.assertEqual(
            statistics["average_score"],
            80,
        )

        self.assertEqual(
            statistics["best_score"],
            90,
        )

        self.assertEqual(
            statistics["remote_jobs"],
            2,
        )

        self.assertEqual(
            statistics["excellent_jobs"],
            2,
        )

        self.assertEqual(
            statistics["new_today"],
            3,
        )

        self.assertEqual(
            statistics["sources"][
                "FranceTravail"
            ]["total"],
            2,
        )

        self.assertEqual(
            statistics["sources"][
                "RemoteOK"
            ]["total"],
            1,
        )

        self.assertIsNotNone(
            statistics["last_sync_at"]
        )

    def test_different_sources_can_reuse_external_id(self):
        first = create_job(
            "shared-id",
            source="ProviderA",
        )

        second = create_job(
            "shared-id",
            source="ProviderB",
        )

        first_result = self.repository.save(
            first
        )

        second_result = self.repository.save(
            second
        )

        self.assertEqual(
            first_result.action,
            "inserted",
        )

        self.assertEqual(
            second_result.action,
            "inserted",
        )

        self.assertEqual(
            self.repository.count(),
            2,
        )

    def test_invalid_object_is_rejected(self):
        with self.assertRaises(TypeError):
            self.repository.save(
                object()
            )


if __name__ == "__main__":
    unittest.main()