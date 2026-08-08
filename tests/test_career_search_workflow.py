from __future__ import annotations

import unittest

from src.career import RoleDetector
from src.career.search_workflow import (
    CareerSearchWorkflow,
)
from src.domain import Job
from src.profile import Profile


class FakeProvider:

    @property
    def name(self) -> str:
        return "RemoteOK"


class FakeJobService:

    def __init__(
        self,
        jobs: list[Job],
    ) -> None:
        self.jobs = jobs
        self.providers = [
            FakeProvider(),
        ]

        self.collection_stats = {
            "total_collected": len(
                jobs
            ),
            "total_unique": len(
                jobs
            ),
        }

        self.provider_errors = []

    def search(
        self,
        profile: Profile,
    ) -> list[Job]:
        return list(
            self.jobs
        )


class TestCareerSearchWorkflow(
    unittest.TestCase
):

    def create_role(self):
        detector = RoleDetector()

        analysis = detector.analyze(
            cv_text=(
                "DSI Groupe et directeur "
                "de projet IT."
            ),
            extracted_skills=[
                "gouvernance si",
                "transformation si",
                "pmp",
                "prince2",
            ],
            limit=5,
        )

        return next(
            suggestion
            for suggestion
            in analysis.role_suggestions
            if suggestion.role_id
            == "it_project_director"
        )

    def create_profile(self) -> Profile:
        return Profile(
            name="Directeur de projet IT",
            keywords=[
                "pmp",
                "prince2",
                "gouvernance si",
            ],
            locations=[
                "Remote",
            ],
            remote=True,
        )

    def create_cio_role(self):
        analysis = RoleDetector().analyze(
            cv_text=(
                "DSI Groupe, gouvernance et transformation SI, COBIT et ITIL."
            ),
            extracted_skills=[
                "gouvernance si",
                "transformation si",
                "cobit",
                "itil",
            ],
        )
        return next(
            item for item in analysis.role_suggestions
            if item.role_id == "cio"
        )

    def test_cio_role_terms_include_dsi_and_cio_aliases(self):
        terms = CareerSearchWorkflow.role_terms(self.create_cio_role())

        self.assertIn("dsi", terms)
        self.assertIn("cio", terms)
        self.assertIn("DSI / CIO", terms)

    def test_clear_dsi_title_is_relevant(self):
        job = Job(
            title="Directeur des systèmes d'information",
            company="Example",
            location="Paris",
            description="Pilotage de la transformation numérique.",
            source="France Travail",
            score=45,
            matched_skills=[],
        )
        result = CareerSearchWorkflow(
            job_service=FakeJobService([job])
        ).search(
            profile=self.create_profile(),
            selected_role=self.create_cio_role(),
        )

        self.assertEqual(result.jobs, [job])
        self.assertTrue(result.filter_diagnostics.jobs[0].title_match)

    def test_cio_semantic_evidence_is_relevant_but_sql_alone_is_not(self):
        semantic = Job(
            title="Technology Executive",
            company="Example",
            location="Paris",
            description="Transformation numérique.",
            source="Test",
            score=60,
            matched_skills=["gouvernance si"],
            match_details={
                "semantic_matches": [
                    {
                        "profile_skill": "cloud",
                        "job_skill": "architecture",
                        "reason": "same_category",
                    }
                ]
            },
        )
        sql_only = Job(
            title="Backend Developer",
            company="Example",
            location="Paris",
            description="SQL",
            source="Test",
            score=35,
            matched_skills=["sql"],
        )
        result = CareerSearchWorkflow(
            job_service=FakeJobService([semantic, sql_only])
        ).search(
            profile=self.create_profile(),
            selected_role=self.create_cio_role(),
        )

        self.assertEqual(result.jobs, [semantic])
        self.assertEqual(
            result.filter_diagnostics.rejection_reasons,
            {"insufficient_relevance_evidence": 1},
        )

    def test_title_match_is_retained(self):
        job = Job(
            title="IT Project Director",
            company="Example",
            location="Remote",
            description="Delivery",
            source="Test",
            score=65,
            matched_skills=[],
            remote=True,
        )

        workflow = CareerSearchWorkflow(
            job_service=FakeJobService(
                [job]
            ),
        )

        result = workflow.search(
            profile=self.create_profile(),
            selected_role=(
                self.create_role()
            ),
        )

        self.assertEqual(
            len(result.jobs),
            1,
        )

    def test_two_skill_matches_are_retained(self):
        job = Job(
            title="Delivery Lead",
            company="Example",
            location="Remote",
            description="Delivery",
            source="Test",
            score=70,
            matched_skills=[
                "pmp",
                "prince2",
            ],
            remote=True,
        )

        workflow = CareerSearchWorkflow(
            job_service=FakeJobService(
                [job]
            ),
        )

        result = workflow.search(
            profile=self.create_profile(),
            selected_role=(
                self.create_role()
            ),
        )

        self.assertEqual(
            len(result.jobs),
            1,
        )

    def test_single_generic_skill_is_rejected(self):
        job = Job(
            title=(
                "Demand Generation Manager"
            ),
            company="Example",
            location="Remote",
            description="Marketing",
            source="Test",
            score=55,
            matched_skills=[
                "sql",
            ],
            remote=True,
        )

        workflow = CareerSearchWorkflow(
            job_service=FakeJobService(
                [job]
            ),
        )

        result = workflow.search(
            profile=self.create_profile(),
            selected_role=(
                self.create_role()
            ),
        )

        self.assertEqual(
            result.jobs,
            [],
        )

    def test_zero_score_is_rejected(self):
        job = Job(
            title="IT Project Director",
            company="Example",
            location="Remote",
            description="Delivery",
            source="Test",
            score=0,
            matched_skills=[
                "pmp",
                "prince2",
            ],
            remote=True,
        )

        workflow = CareerSearchWorkflow(
            job_service=FakeJobService(
                [job]
            ),
        )

        result = workflow.search(
            profile=self.create_profile(),
            selected_role=(
                self.create_role()
            ),
        )

        self.assertEqual(
            result.jobs,
            [],
        )

    def test_provider_statuses_are_returned(self):
        workflow = CareerSearchWorkflow(
            job_service=FakeJobService(
                []
            ),
        )

        result = workflow.search(
            profile=self.create_profile(),
            selected_role=(
                self.create_role()
            ),
        )

        provider_ids = {
            status.provider_id
            for status
            in result.provider_statuses
        }

        self.assertIn(
            "remoteok",
            provider_ids,
        )

        self.assertIn(
            "apec",
            provider_ids,
        )

    def test_semantic_evidence_contributes_to_relevance(self):
        job = Job(
            title="Technology Lead",
            company="Example",
            location="Remote",
            description="Delivery",
            source="Test",
            score=60,
            matched_skills=["pmp"],
            match_details={
                "semantic_matches": [
                    {
                        "profile_skill": "azure",
                        "job_skill": "aws",
                        "reason": "same_category",
                    }
                ]
            },
            remote=True,
        )

        result = CareerSearchWorkflow(
            job_service=FakeJobService([job]),
        ).search(
            profile=self.create_profile(),
            selected_role=self.create_role(),
        )

        self.assertEqual(result.jobs, [job])
        diagnostic = result.filter_diagnostics.jobs[0]
        self.assertEqual(diagnostic.exact_match_count, 1)
        self.assertEqual(diagnostic.semantic_match_count, 1)
        self.assertTrue(diagnostic.accepted)
        self.assertIsNone(diagnostic.rejection_reason)

    def test_collected_but_zero_relevant_is_diagnosed(self):
        zero_score = Job(
            title="Finance Assistant",
            company="Example",
            location="Paris",
            description="Finance",
            source="Test",
            score=0,
        )
        insufficient = Job(
            title="Demand Generation Manager",
            company="Example",
            location="Remote",
            description="Marketing SQL",
            source="Test",
            score=55,
            matched_skills=["sql"],
        )

        result = CareerSearchWorkflow(
            job_service=FakeJobService([zero_score, insufficient]),
        ).search(
            profile=self.create_profile(),
            selected_role=self.create_role(),
        )

        self.assertEqual(result.total_collected, 2)
        self.assertEqual(result.total_relevant, 0)
        self.assertEqual(result.filter_diagnostics.total_processed, 2)
        self.assertEqual(result.filter_diagnostics.total_rejected, 2)
        self.assertEqual(
            result.filter_diagnostics.rejection_reasons,
            {
                "zero_score": 1,
                "insufficient_relevance_evidence": 1,
            },
        )


if __name__ == "__main__":
    unittest.main()
