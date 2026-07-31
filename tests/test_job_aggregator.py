from dataclasses import dataclass
import unittest

from src.domain import Job
from src.search_request import SearchRequest
from src.services.job_aggregator import JobAggregator


@dataclass
class SuccessfulProvider:
    name: str
    jobs: list[Job]

    def search(
        self,
        request: SearchRequest,
    ) -> list[Job]:
        return list(self.jobs)


class FailingProvider:
    name = "FailingProvider"

    def search(
        self,
        request: SearchRequest,
    ) -> list[Job]:
        raise RuntimeError("Provider indisponible")


class InvalidProvider:
    name = "InvalidProvider"

    def search(self, request: SearchRequest):
        return [
            "offre invalide",
            123,
        ]


class TestJobAggregator(unittest.TestCase):

    def create_request(self) -> SearchRequest:
        return SearchRequest(
            keywords=["Python"],
            locations=["Paris"],
        )

    def create_job(
        self,
        external_id: str,
        title: str = "Python Developer",
        url: str | None = None,
        source: str = "Provider A",
    ) -> Job:
        return Job(
            external_id=external_id,
            title=title,
            company="Example Corp",
            location="Paris",
            description="Développement Python et SQL",
            source=source,
            url=url,
            skills=["Python", "SQL"],
        )

    def test_collects_jobs_from_multiple_providers(self):
        provider_a = SuccessfulProvider(
            name="Provider A",
            jobs=[
                self.create_job(
                    external_id="a-1",
                    source="Provider A",
                ),
            ],
        )

        provider_b = SuccessfulProvider(
            name="Provider B",
            jobs=[
                self.create_job(
                    external_id="b-1",
                    title="Data Engineer",
                    source="Provider B",
                ),
            ],
        )

        aggregator = JobAggregator(
            [provider_a, provider_b]
        )

        result = aggregator.collect(
            self.create_request()
        )

        self.assertEqual(len(result.jobs), 2)
        self.assertEqual(result.total_collected, 2)
        self.assertEqual(result.total_unique, 2)
        self.assertEqual(result.successful_providers, 2)

    def test_removes_duplicate_jobs(self):
        first_job = self.create_job(
            external_id="duplicate-1",
            source="Shared Provider",
        )

        duplicate_job = self.create_job(
            external_id="duplicate-1",
            source="Shared Provider",
        )

        provider_a = SuccessfulProvider(
            name="Provider A",
            jobs=[first_job],
        )

        provider_b = SuccessfulProvider(
            name="Provider B",
            jobs=[duplicate_job],
        )

        aggregator = JobAggregator(
            [provider_a, provider_b]
        )

        result = aggregator.collect(
            self.create_request()
        )

        self.assertEqual(result.total_collected, 2)
        self.assertEqual(result.total_unique, 1)
        self.assertEqual(result.duplicates_removed, 1)

        self.assertEqual(
            result.provider_stats[
                "Provider B"
            ].duplicates,
            1,
        )

    def test_provider_error_does_not_stop_collection(self):
        successful_provider = SuccessfulProvider(
            name="WorkingProvider",
            jobs=[
                self.create_job(
                    external_id="working-1"
                ),
            ],
        )

        aggregator = JobAggregator(
            [
                FailingProvider(),
                successful_provider,
            ]
        )

        result = aggregator.collect(
            self.create_request()
        )

        self.assertEqual(len(result.jobs), 1)
        self.assertEqual(result.errors, 1)
        self.assertEqual(result.failed_providers, 1)

        self.assertIn(
            "Provider indisponible",
            result.provider_stats[
                "FailingProvider"
            ].error,
        )

    def test_invalid_jobs_are_ignored(self):
        aggregator = JobAggregator(
            [InvalidProvider()]
        )

        result = aggregator.collect(
            self.create_request()
        )

        self.assertEqual(result.jobs, [])
        self.assertEqual(
            result.invalid_jobs_removed,
            2,
        )

        self.assertEqual(
            result.provider_stats[
                "InvalidProvider"
            ].invalid,
            2,
        )

    def test_statistics_can_be_serialized(self):
        provider = SuccessfulProvider(
            name="Provider A",
            jobs=[
                self.create_job(
                    external_id="a-1"
                ),
            ],
        )

        result = JobAggregator(
            [provider]
        ).collect(
            self.create_request()
        )

        statistics = result.to_dict()

        self.assertEqual(
            statistics["total_collected"],
            1,
        )

        self.assertEqual(
            statistics["total_unique"],
            1,
        )

        self.assertEqual(
            statistics["errors"],
            0,
        )

        self.assertEqual(
            statistics["providers"][
                "Provider A"
            ]["accepted"],
            1,
        )


if __name__ == "__main__":
    unittest.main()