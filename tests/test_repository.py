import tempfile
import unittest
from datetime import datetime
from pathlib import Path

import src.storage.database as database
from src.domain import Job
from src.storage.repository import JobRepository


class TestJobRepository(unittest.TestCase):

    def setUp(self):
        self.temp_directory = (
            tempfile.TemporaryDirectory()
        )

        self.original_db_path = database.DB_PATH

        database.DB_PATH = (
            Path(self.temp_directory.name)
            / "test_jobagent.db"
        )

        database.init_database()

        self.repository = JobRepository()

    def tearDown(self):
        database.DB_PATH = (
            self.original_db_path
        )

        self.temp_directory.cleanup()

    def create_job(self) -> Job:
        return Job(
            external_id="job-123",
            title="Data Engineer",
            company="Example",
            location="Paris",
            description="Python SQL Spark",
            source="TestProvider",
            url="https://example.com/job-123",
            contract_type="CDI",
            salary_min=65000,
            salary_max=75000,
            remote_type="hybrid",
            published_at=datetime(
                2026,
                7,
                31,
                10,
                0,
            ),
            skills=[
                "Python",
                "SQL",
            ],
            languages=["Français"],
            raw_data={
                "provider_id": "job-123",
            },
            score=82,
            matched_skills=["Python"],
            missing_skills=["Spark"],
            match_details={
                "skills": 70,
                "location": 12,
            },
            explanation="Très bonne compatibilité",
        )

    def test_save_and_load_canonical_job(self):
        job = self.create_job()

        self.repository.save(job)

        jobs = self.repository.get_all()

        self.assertEqual(len(jobs), 1)

        restored = jobs[0]

        self.assertEqual(
            restored.external_id,
            "job-123",
        )
        self.assertEqual(
            restored.salary_min,
            65000,
        )
        self.assertEqual(
            restored.salary_max,
            75000,
        )
        self.assertEqual(
            restored.remote_type,
            "hybrid",
        )
        self.assertEqual(
            restored.skills,
            ["Python", "SQL"],
        )
        self.assertEqual(
            restored.raw_data,
            {
                "provider_id": "job-123",
            },
        )
        self.assertEqual(
            restored.match_details,
            {
                "skills": 70,
                "location": 12,
            },
        )

    def test_save_updates_existing_external_job(self):
        job = self.create_job()

        self.repository.save(job)

        job.score = 91
        job.salary_max = 80000

        self.repository.save(job)

        self.assertEqual(
            self.repository.count(),
            1,
        )

        restored = (
            self.repository.get_all()[0]
        )

        self.assertEqual(
            restored.score,
            91,
        )
        self.assertEqual(
            restored.salary_max,
            80000,
        )

    def test_exists_by_url(self):
        job = self.create_job()

        self.repository.save(job)

        self.assertTrue(
            self.repository.exists(job.url)
        )

    def test_clear(self):
        self.repository.save(
            self.create_job()
        )

        self.repository.clear()

        self.assertEqual(
            self.repository.count(),
            0,
        )


if __name__ == "__main__":
    unittest.main()