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


if __name__ == "__main__":
    unittest.main()