from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from src.domain import Job
from src.auth.models import (
    CurrentUser,
    Role,
)
from src.auth.user_context import (
    UserContext,
)
from src.career.search_workflow import (
    CareerSearchResult,
)
from src.domain import Job
from src.profile import Profile
from src.workspace import (
    build_workspace,
)
from src.workspace.search import (
    WorkspaceSearchCache,
    WorkspaceSearchError,
    WorkspaceSearchService,
)


class FakeCareerSearchWorkflow:

    def __init__(self) -> None:
        self.profiles: list[Profile] = []

    def search(
        self,
        profile: Profile,
        selected_role=None,
    ) -> CareerSearchResult:
        self.profiles.append(profile)

        return CareerSearchResult(
            jobs=[
                Job(
                    title="Data Engineer",
                    company="Example",
                    location="Paris",
                    description=(
                        "Python SQL Azure"
                    ),
                    source="Test",
                    score=75,
                )
            ],
            all_jobs=[],
        )


class TestWorkspaceSearchService(
    unittest.TestCase
):

    def setUp(self) -> None:
        self.temporary_directory = (
            tempfile.TemporaryDirectory()
        )

        self.storage_root = (
            Path(
                self.temporary_directory.name
            )
            / "users"
        )

        context = UserContext(
            current_user=CurrentUser(
                user_id="user-123",
                subject="subject-123",
                email="user@example.com",
                display_name="User",
                authenticated=True,
                authorized=True,
                roles=(Role.USER,),
            )
        )

        self.workspace = build_workspace(
            user_context=context,
            storage_root=self.storage_root,
        )

        self.workflow = (
            FakeCareerSearchWorkflow()
        )

        self.service = WorkspaceSearchService(
            profile_service=(
                self.workspace.profile_service
            ),
            workflow=self.workflow,
        )

    def tearDown(self) -> None:
        self.temporary_directory.cleanup()

    def create_profile(
        self,
        profile_id: str = "data_engineer",
    ) -> None:
        directory = (
            self.workspace
            .services
            .paths
            .ensure_profile_directory(
                profile_id
            )
        )

        (
            directory
            / "config.json"
        ).write_text(
            json.dumps(
                {
                    "name": "Data Engineer",
                    "keywords": [
                        "Python",
                        "SQL",
                        "Azure",
                    ],
                    "locations": [
                        "Paris",
                    ],
                    "salary_min": 65000,
                    "remote": True,
                }
            ),
            encoding="utf-8",
        )

    def test_build_context(self):
        self.create_profile()

        context = (
            self.service
            .build_context(
                "data_engineer"
            )
        )

        self.assertEqual(
            context.profile_id,
            "data_engineer",
        )

        self.assertEqual(
            context.profile.name,
            "Data Engineer",
        )

        self.assertEqual(
            context.profile.keywords,
            [
                "Python",
                "SQL",
                "Azure",
            ],
        )

        self.assertEqual(
            context.profile.locations,
            [
                "Paris",
            ],
        )

        self.assertEqual(
            context.profile.salary_min,
            65000,
        )

        self.assertTrue(
            context.profile.remote
        )

    def test_search_uses_existing_workflow(
        self,
    ):
        self.create_profile()

        result = self.service.search(
            "data_engineer"
        )

        self.assertEqual(
            len(result.jobs),
            1,
        )

        self.assertEqual(
            len(self.workflow.profiles),
            1,
        )

        self.assertEqual(
            self.workflow
            .profiles[0]
            .name,
            "Data Engineer",
        )

    def test_unknown_profile_is_rejected(
        self,
    ):
        with self.assertRaises(
            WorkspaceSearchError
        ):
            self.service.search(
                "unknown"
            )

    def test_empty_profile_id_is_rejected(
        self,
    ):
        with self.assertRaises(
            WorkspaceSearchError
        ):
            self.service.search("")

    def test_cache_is_scoped_by_profile(
        self,
    ):
        session_state: dict = {}

        first = CareerSearchResult(
            jobs=[]
        )

        second = CareerSearchResult(
            jobs=[]
        )

        WorkspaceSearchCache.set(
            session_state,
            "profile-a",
            first,
        )

        WorkspaceSearchCache.set(
            session_state,
            "profile-b",
            second,
        )

        self.assertIs(
            WorkspaceSearchCache.get(
                session_state,
                "profile-a",
            ),
            first,
        )

        self.assertIs(
            WorkspaceSearchCache.get(
                session_state,
                "profile-b",
            ),
            second,
        )

    def test_cache_clear_only_one_profile(
        self,
    ):
        session_state: dict = {}

        first = CareerSearchResult()
        second = CareerSearchResult()

        WorkspaceSearchCache.set(
            session_state,
            "profile-a",
            first,
        )

        WorkspaceSearchCache.set(
            session_state,
            "profile-b",
            second,
        )

        WorkspaceSearchCache.clear(
            session_state,
            "profile-a",
        )

        self.assertIsNone(
            WorkspaceSearchCache.get(
                session_state,
                "profile-a",
            )
        )

        self.assertIs(
            WorkspaceSearchCache.get(
                session_state,
                "profile-b",
            ),
            second,
        )
    def test_search_without_analysis_service_still_works(
        self,
    ):
        self.create_profile()

        result = self.service.search(
            "data_engineer"
        )

        self.assertIsNotNone(result)

    def test_result_jobs_prefers_all_jobs(
        self,
    ):
        first = Job(
            title="First",
            company="Example",
            location="Paris",
            description="Description",
            source="Test",
        )

        second = Job(
            title="Second",
            company="Example",
            location="Paris",
            description="Description",
            source="Test",
        )

        result = type(
            "Result",
            (),
            {
                "all_jobs": [
                    first,
                    second,
                ],
                "jobs": [
                    first,
                ],
            },
        )()

        selected = (
            WorkspaceSearchService
            ._result_jobs(result)
        )

        self.assertEqual(
            selected,
            (
                first,
                second,
            ),
        )

if __name__ == "__main__":
    unittest.main()