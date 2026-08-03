import unittest
from datetime import datetime

from src.domain import Job


class TestJob(unittest.TestCase):

    def test_creates_canonical_job(self):
        job = Job(
            external_id="123",
            title="Data Engineer",
            company="Example",
            location="Paris",
            description="Python SQL Spark",
            source="Test",
            url="https://example.com/123",
            contract_type="CDI",
            salary_min=60000,
            salary_max=75000,
            remote_type="hybrid",
            skills=["Python", "SQL"],
            languages=["Français", "Anglais"],
            published_at=datetime(
                2026,
                7,
                31,
            ),
        )

        self.assertEqual(
            job.external_id,
            "123",
        )
        self.assertEqual(
            job.salary_min,
            60000,
        )
        self.assertEqual(
            job.remote_type,
            "hybrid",
        )
        self.assertEqual(
            job.skills,
            ["Python", "SQL"],
        )

    def test_legacy_salary_populates_salary_min(self):
        job = Job(
            title="Developer",
            company="Example",
            location="Paris",
            description="Python",
            source="Test",
            salary=50000,
        )

        self.assertEqual(
            job.salary_min,
            50000,
        )
        self.assertEqual(
            job.salary,
            50000,
        )

    def test_legacy_remote_populates_remote_type(self):
        job = Job(
            title="Developer",
            company="Example",
            location="France",
            description="Python",
            source="Test",
            remote=True,
        )

        self.assertEqual(
            job.remote_type,
            "remote",
        )
        self.assertTrue(job.is_remote)

    def test_salary_range_is_reordered(self):
        job = Job(
            title="Developer",
            company="Example",
            location="Paris",
            description="Python",
            source="Test",
            salary_min=80000,
            salary_max=60000,
        )

        self.assertEqual(
            job.salary_min,
            60000,
        )
        self.assertEqual(
            job.salary_max,
            80000,
        )

    def test_skills_are_cleaned_and_deduplicated(self):
        job = Job(
            title="Developer",
            company="Example",
            location="Paris",
            description="Python",
            source="Test",
            skills=[
                "Python",
                " python ",
                "",
                "SQL",
            ],
        )

        self.assertEqual(
            job.skills,
            ["Python", "SQL"],
        )

    def test_title_is_required(self):
        with self.assertRaises(ValueError):
            Job(
                title="",
                company="Example",
                location="Paris",
                description="Python",
                source="Test",
            )

    def test_identity_uses_external_id_first(self):
        job = Job(
            external_id="abc",
            title="Developer",
            company="Example",
            location="Paris",
            description="Python",
            source="Provider",
            url="https://example.com/job",
        )

        self.assertEqual(
            job.identity,
            "Provider:abc",
        )


if __name__ == "__main__":
    unittest.main()