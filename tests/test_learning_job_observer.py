from __future__ import annotations

import unittest

from src.domain import Job
from src.learning import (
    JobLearningObservationExtractor,
)
from unittest.mock import Mock

from src.analysis import StructuredAnalysis

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
            "microsoft fabric",
            {
                term.casefold()
                for term in terms
            },
        )

        self.assertIn(
            "azure",
            {
                term.casefold()
                for term in terms
            },
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

    def test_uses_structured_job_analysis(
        self,
    ) -> None:
        analyzer = Mock()

        analyzer.analyze_job.return_value = (
            StructuredAnalysis(
                hard_skills=(
                    "Terraform",
                    "Kubernetes",
                ),
                certifications=(
                    "TOGAF",
                ),
            )
        )

        extractor = (
            JobLearningObservationExtractor(
                analyzer=analyzer
            )
        )

        job = Job(
            title="Architecte Cloud",
            company="Example",
            location="Paris",
            description=(
                "Description du poste INFORMATION "
                "avoid spam applicants."
            ),
            source="France Travail",
            external_id="ft-structured-1",
        )

        observations = extractor.extract_job(
            job
        )

        terms = {
            item.term
            for item in observations
        }

        self.assertEqual(
            terms,
            {
                "Terraform",
                "Kubernetes",
                "TOGAF",
            },
        )

        analyzer.analyze_job.assert_called_once_with(
            job
        )

    def test_does_not_scan_raw_text_when_structured_terms_exist(
        self,
    ) -> None:
        analyzer = Mock()

        analyzer.analyze_job.return_value = (
            StructuredAnalysis(
                hard_skills=(
                    "ServiceNow",
                ),
            )
        )

        extractor = (
            JobLearningObservationExtractor(
                analyzer=analyzer
            )
        )

        job = Job(
            title="DSI",
            company="Example",
            location="Paris",
            description=(
                "Description du poste INFORMATION "
                "Companies can search "
                "avoid spam applicants."
            ),
            source="RemoteOK",
            external_id="remote-structured-1",
        )

        observations = extractor.extract_job(
            job
        )

        self.assertEqual(
            tuple(
                item.term
                for item in observations
            ),
            (
                "ServiceNow",
            ),
        )


    def test_uses_regex_fallback_when_analysis_is_empty(
        self,
    ) -> None:
        analyzer = Mock()

        analyzer.analyze_job.return_value = (
            StructuredAnalysis()
        )

        extractor = (
            JobLearningObservationExtractor(
                analyzer=analyzer,
                raw_text_fallback_enabled=True,
            )
        )

        job = Job(
            title="Kubernetes",
            company="Example",
            location="Remote",
            description="",
            source="RemoteOK",
            external_id="remote-fallback-1",
        )

        observations = extractor.extract_job(
            job
        )

        terms = {
            item.term
            for item in observations
        }

        self.assertIn(
            "Kubernetes",
            terms,
        )
        
def test_raw_text_fallback_is_disabled_by_default(
        self,
    ) -> None:
        analyzer = Mock()

        analyzer.analyze_job.return_value = (
            StructuredAnalysis()
        )

        extractor = (
            JobLearningObservationExtractor(
                analyzer=analyzer
            )
        )

        job = Job(
            title="Expert Kubernetes",
            company="Example",
            location="Remote",
            description=(
                "Une mutuelle santé, un CET, "
                "des chèques cadeaux et une "
                "épargne à 5 %."
            ),
            source="RemoteOK",
            external_id="remote-no-fallback-1",
        )

        observations = extractor.extract_job(
            job
        )

        self.assertEqual(
            observations,
            (),
        )

        analyzer.analyze_job.assert_called_once_with(
            job
        )

def test_ignores_unrecognized_provider_tags(
        self,
    ) -> None:
        job = Job(
            title="Software Engineer",
            company="Example",
            location="Remote",
            description="Python et Azure requis.",
            source="RemoteOK",
            external_id="remote-tags-1",
            skills=[
                "exec",
                "digital nomad",
                "customer support",
                "python",
                "azure",
            ],
        )

        observations = (
            self.extractor.extract_job(
                job
            )
        )

        terms = {
            item.term.casefold()
            for item in observations
        }

        self.assertIn("python", terms)
        self.assertIn("azure", terms)

        self.assertNotIn("exec", terms)
        self.assertNotIn(
            "digital nomad",
            terms,
        )
        self.assertNotIn(
            "customer support",
            terms,
        )

if __name__ == "__main__":
    unittest.main()