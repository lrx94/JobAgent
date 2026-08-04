from __future__ import annotations

import unittest

from src.domain import Job
from src.learning import (
    JobLearningObservationExtractor,
)


class TestJobLearningObservationExtractor(
    unittest.TestCase
):

    def setUp(self) -> None:
        self.extractor = (
            JobLearningObservationExtractor()
        )

    @staticmethod
    def create_job() -> Job:
        return Job(
            title="Data Engineer Microsoft Fabric",
            company="Example",
            location="Paris",
            description=(
                "Expérience requise sur Microsoft Fabric, "
                "Azure OpenAI et LangGraph."
            ),
            source="France Travail",
            external_id="ft-1",
            skills=[
                "Microsoft Fabric",
                "FinOps",
            ],
        )

    def test_extracts_provider_tags(
        self,
    ):
        observations = (
            self.extractor.extract_job(
                self.create_job()
            )
        )

        terms = {
            item.term
            for item in observations
        }

        self.assertIn(
            "Microsoft Fabric",
            terms,
        )

        self.assertIn(
            "FinOps",
            terms,
        )

    def test_keeps_source_and_reference(
        self,
    ):
        observations = (
            self.extractor.extract_job(
                self.create_job()
            )
        )

        self.assertTrue(
            all(
                item.source
                == "france travail"
                for item in observations
            )
        )

        self.assertTrue(
            all(
                item.reference_id
                == "ft-1"
                for item in observations
            )
        )

    def test_duplicate_term_is_observed_once_per_job(
        self,
    ):
        observations = (
            self.extractor.extract_job(
                self.create_job()
            )
        )

        normalized = [
            item.term.casefold()
            for item in observations
        ]

        self.assertEqual(
            normalized.count(
                "microsoft fabric"
            ),
            1,
        )

    def test_invalid_job_is_rejected(
        self,
    ):
        with self.assertRaises(TypeError):
            self.extractor.extract_job(
                object()
            )


if __name__ == "__main__":
    unittest.main()