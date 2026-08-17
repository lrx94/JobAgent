from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

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
from src.search_request import SearchRequest
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
        self.selected_roles = []

    def search(
        self,
        profile: Profile,
        selected_role=None,
    ) -> CareerSearchResult:
        self.profiles.append(profile)
        self.selected_roles.append(selected_role)

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
        career: dict | None = None,
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
                    **(
                        {"career": career}
                        if career is not None
                        else {}
                    ),
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

        self.assertIsNone(self.workflow.selected_roles[0])

    def test_search_preserves_selected_role_metadata(self):
        self.create_profile(
            career={
                "selected_role_id": "data_engineer",
            }
        )

        self.service.search("data_engineer")

        selected_role = self.workflow.selected_roles[0]
        self.assertIsNotNone(selected_role)
        self.assertEqual(selected_role.role_id, "data_engineer")
        self.assertEqual(selected_role.label, "Data Engineer")
        self.assertIn("RemoteOK", selected_role.preferred_providers)

    def test_transitional_role_metadata_is_supported(self):
        self.create_profile(
            career={"selected_role": {"role_id": "data_engineer"}}
        )

        self.service.search("data_engineer")

        self.assertEqual(
            self.workflow.selected_roles[0].role_id,
            "data_engineer",
        )

    def test_unknown_role_id_is_ignored(self):
        self.create_profile(career={"selected_role_id": "obsolete_role"})

        self.service.search("data_engineer")

        self.assertIsNone(self.workflow.selected_roles[0])

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

    def test_empty_user_profile_list_is_safe(self):
        self.assertEqual(
            self.service.list_profile_ids(),
            [],
        )

    def test_profiles_are_isolated_between_users(self):
        self.create_profile("private_profile")

        other_context = UserContext(
            current_user=CurrentUser(
                user_id="other-user",
                subject="other-subject",
                email="other@example.com",
                display_name="Other",
                authenticated=True,
                authorized=True,
                roles=(Role.USER,),
            )
        )
        other_workspace = build_workspace(
            user_context=other_context,
            storage_root=self.storage_root,
        )
        other_service = WorkspaceSearchService(
            profile_service=other_workspace.profile_service,
            workflow=FakeCareerSearchWorkflow(),
        )

        self.assertEqual(
            other_service.list_profile_ids(),
            [],
        )

        with self.assertRaises(WorkspaceSearchError):
            other_service.build_context("private_profile")

    def test_update_constraints_preserves_profile_business_data(self):
        self.create_profile(
            career={"selected_role_id": "data_engineer"}
        )
        config_path = (
            self.workspace.services.paths
            .profile_directory("data_engineer")
            / "config.json"
        )
        config = json.loads(config_path.read_text(encoding="utf-8"))
        config["cv"] = "cv-principal.pdf"
        config["custom_metadata"] = {"keep": True}
        config_path.write_text(json.dumps(config), encoding="utf-8")

        updated = self.service.update_profile_constraints(
            profile_id="data_engineer",
            locations=[" Lyon ", "lyon", "Remote"],
            salary_min=72000,
            remote=False,
        )
        persisted = self.workspace.profile_service.load_profile_config(
            "data_engineer"
        )

        self.assertEqual(updated.profile.locations, ["Lyon", "Remote"])
        self.assertEqual(updated.profile.salary_min, 72000)
        self.assertFalse(updated.profile.remote)
        self.assertEqual(persisted["keywords"], ["Python", "SQL", "Azure"])
        self.assertEqual(
            persisted["career"],
            {"selected_role_id": "data_engineer"},
        )
        self.assertEqual(persisted["cv"], "cv-principal.pdf")
        self.assertEqual(persisted["custom_metadata"], {"keep": True})

    def test_update_constraints_rejects_negative_salary(self):
        self.create_profile()
        with self.assertRaises(WorkspaceSearchError):
            self.service.update_profile_constraints(
                profile_id="data_engineer",
                locations=["Paris"],
                salary_min=-1,
                remote=True,
            )

    def test_update_constraints_preserves_cv_associations(self):
        self.create_profile()
        imported = self.workspace.cv_service.import_bytes(
            content=b"%PDF-1.4\nconstraints test\n%%EOF\n",
            title="CV Data",
            original_filename="cv.pdf",
            analyze=False,
        )
        association = self.workspace.association_service.attach_cv(
            profile_id="data_engineer",
            cv_id=imported.cv_id,
            is_primary=True,
        )

        self.service.update_profile_constraints(
            profile_id="data_engineer",
            locations=["Lyon"],
            salary_min=70000,
            remote=False,
        )

        self.assertEqual(
            self.workspace.association_repository.list_for_profile(
                "data_engineer"
            ),
            [association],
        )

    def test_update_constraints_remains_user_isolated(self):
        self.create_profile("private_profile")
        other_context = UserContext(
            current_user=CurrentUser(
                user_id="other-user",
                subject="other-subject",
                email="other@example.com",
                display_name="Other",
                authenticated=True,
                authorized=True,
                roles=(Role.USER,),
            )
        )
        other_workspace = build_workspace(
            user_context=other_context,
            storage_root=self.storage_root,
        )
        other_service = WorkspaceSearchService(
            profile_service=other_workspace.profile_service,
            workflow=FakeCareerSearchWorkflow(),
        )

        with self.assertRaises(WorkspaceSearchError):
            other_service.update_profile_constraints(
                profile_id="private_profile",
                locations=["Lyon"],
                salary_min=50000,
                remote=False,
            )

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

    def test_activating_new_profile_preserves_profile_scoped_results(self):
        session_state: dict = {}
        daf = CareerSearchResult()
        dsi = CareerSearchResult()
        other = CareerSearchResult()
        WorkspaceSearchCache.set(session_state, "daf", daf)
        WorkspaceSearchCache.set(session_state, "dsi", dsi)
        WorkspaceSearchCache.set(session_state, "other", other)
        WorkspaceSearchCache.activate_profile(session_state, "daf")

        previous = WorkspaceSearchCache.activate_profile(
            session_state,
            "dsi",
        )

        self.assertEqual(previous, "daf")
        self.assertIs(WorkspaceSearchCache.get(session_state, "daf"), daf)
        self.assertIs(WorkspaceSearchCache.get(session_state, "dsi"), dsi)
        self.assertIs(WorkspaceSearchCache.get(session_state, "other"), other)

    def test_updated_profile_builds_typed_search_request(self):
        self.create_profile(career={"selected_role_id": "cio"})
        updated = self.service.update_profile_constraints(
            profile_id="data_engineer",
            locations=[" Paris ", ""],
            salary_min=70000,
            remote=False,
        )

        request = SearchRequest.from_profile(updated.profile)
        self.assertEqual(request.locations, ["Paris"])
        self.assertEqual(request.salary_min, 70000)
        self.assertIsInstance(request.salary_min, int)
        self.assertIs(request.remote, False)
        self.assertEqual(request.keywords, ["Python", "SQL", "Azure"])

    def test_cio_role_is_restored_after_profile_reload(self):
        self.create_profile(career={"selected_role_id": "cio"})

        context = self.service.build_context("data_engineer")

        self.assertIsNotNone(context.selected_role)
        self.assertEqual(context.selected_role.role_id, "cio")
        self.assertEqual(context.selected_role.label, "DSI / CIO")


if __name__ == "__main__":
    unittest.main()
