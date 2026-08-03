from __future__ import annotations

import json
import unittest
from unittest.mock import patch

from src.providers.remoteok import RemoteOKProvider
from src.search_request import SearchRequest


class FakeHttpResponse:

    def __init__(
        self,
        payload,
        status: int = 200,
    ) -> None:
        self.status = status
        self._body = json.dumps(
            payload
        ).encode("utf-8")

    def read(self) -> bytes:
        return self._body

    def __enter__(self):
        return self

    def __exit__(
        self,
        exc_type,
        exc_value,
        traceback,
    ) -> bool:
        return False


def remoteok_payload() -> list[dict]:
    return [
        {
            "legal": "metadata",
        },
        {
            "id": "job-1",
            "position": "Senior Data Engineer",
            "company": "Example Data",
            "location": "Worldwide",
            "description": (
                "<p>Python, SQL, Spark "
                "and Azure pipelines.</p>"
            ),
            "url": (
                "https://remoteok.com/"
                "remote-jobs/job-1"
            ),
            "tags": [
                "python",
                "sql",
                "spark",
            ],
            "salary_min": 70000,
            "salary_max": 95000,
            "epoch": 1760000000,
        },
        {
            "id": "job-2",
            "position": "Finance Director",
            "company": "Example Finance",
            "location": "Remote",
            "description": (
                "<p>Financial planning "
                "and management.</p>"
            ),
            "url": (
                "https://remoteok.com/"
                "remote-jobs/job-2"
            ),
            "tags": [
                "finance",
                "management",
            ],
            "epoch": 1760000100,
        },
    ]


class TestRemoteOKProvider(unittest.TestCase):

    def setUp(self) -> None:
        self.provider = RemoteOKProvider(
            timeout=5,
        )

    @patch(
        "src.providers.remoteok.urlopen"
    )
    def test_fetches_and_normalizes_jobs(
        self,
        mocked_urlopen,
    ):
        mocked_urlopen.return_value = (
            FakeHttpResponse(
                remoteok_payload()
            )
        )

        request = SearchRequest(
            locations=["Remote"],
            page_size=20,
        )

        jobs = self.provider.search(request)

        self.assertEqual(len(jobs), 2)

        data_job = next(
            job
            for job in jobs
            if job.external_id == "job-1"
        )

        self.assertEqual(
            data_job.title,
            "Senior Data Engineer",
        )
        self.assertEqual(
            data_job.company,
            "Example Data",
        )
        self.assertEqual(
            data_job.source,
            "RemoteOK",
        )
        self.assertEqual(
            data_job.remote_type,
            "remote",
        )
        self.assertTrue(data_job.remote)
        self.assertEqual(
            data_job.salary_min,
            70000,
        )
        self.assertEqual(
            data_job.salary_max,
            95000,
        )
        self.assertEqual(
            data_job.salary_currency,
            "USD",
        )
        self.assertEqual(
            data_job.salary_period,
            "year",
        )
        self.assertEqual(
            data_job.skills,
            [
                "python",
                "sql",
                "spark",
            ],
        )
        self.assertNotIn(
            "<p>",
            data_job.description,
        )

    @patch(
        "src.providers.remoteok.urlopen"
    )
    def test_metadata_entry_is_ignored(
        self,
        mocked_urlopen,
    ):
        mocked_urlopen.return_value = (
            FakeHttpResponse(
                remoteok_payload()
            )
        )

        jobs = self.provider.search(
            SearchRequest(
                locations=["Remote"],
            )
        )

        self.assertEqual(len(jobs), 2)

        self.assertTrue(
            all(job.external_id for job in jobs)
        )

    @patch(
        "src.providers.remoteok.urlopen"
    )
    def test_provider_does_not_filter_by_profile_keywords(
        self,
        mocked_urlopen,
    ):
        mocked_urlopen.return_value = (
            FakeHttpResponse(
                remoteok_payload()
            )
        )

        request = SearchRequest(
            keywords=[
                "COBIT",
                "PRINCE2",
            ],
            locations=["Remote"],
            page_size=20,
        )

        jobs = self.provider.search(request)

        # Les mots-clés sont traités par MatchingEngine,
        # pas par le provider.
        self.assertEqual(len(jobs), 2)

    @patch(
        "src.providers.remoteok.urlopen"
    )
    def test_pagination_is_applied_after_normalization(
        self,
        mocked_urlopen,
    ):
        mocked_urlopen.return_value = (
            FakeHttpResponse(
                remoteok_payload()
            )
        )

        jobs = self.provider.search(
            SearchRequest(
                locations=["Remote"],
                page=1,
                page_size=1,
            )
        )

        self.assertEqual(len(jobs), 1)

    @patch(
        "src.providers.remoteok.urlopen"
    )
    def test_salary_filter_keeps_unknown_salary(
        self,
        mocked_urlopen,
    ):
        mocked_urlopen.return_value = (
            FakeHttpResponse(
                remoteok_payload()
            )
        )

        jobs = self.provider.search(
            SearchRequest(
                locations=["Remote"],
                salary_min=90000,
                page_size=20,
            )
        )

        external_ids = {
            job.external_id
            for job in jobs
        }

        # job-1 passe grâce à salary_max=95000.
        self.assertIn(
            "job-1",
            external_ids,
        )

        # Une rémunération non fournie n'est pas
        # éliminée arbitrairement par le provider.
        self.assertIn(
            "job-2",
            external_ids,
        )

    def test_rejects_invalid_search_request(self):
        with self.assertRaises(TypeError):
            self.provider.search(
                object()
            )


if __name__ == "__main__":
    unittest.main()