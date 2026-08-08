from __future__ import annotations

import unittest

from src.workspace.ui.actions import (
    WorkspaceCVActions,
    finalize_onboarding_session,
    get_profile_learning_result,
    synchronize_profile_selection,
)
from src.career.search_workflow import CareerSearchResult
from src.workspace.search import WorkspaceSearchCache
from src.workspace.learning_service import (
    WorkspaceLearningResult,
    WorkspaceLearningSummary,
)


def test_finalize_onboarding_session_selects_and_clears_preview():
    state = {
        "selected": "old",
        "preview": object(),
        "upload": b"pdf",
        "generation": 2,
        "unrelated": "kept",
    }

    finalize_onboarding_session(
        state,
        profile_id="new-profile",
        selected_profile_key="selected",
        keys_to_clear=("preview", "upload"),
        generation_key="generation",
    )

    assert state == {
        "selected": "new-profile",
        "unrelated": "kept",
        "generation": 3,
    }


def test_profile_transition_clears_previous_search_and_learning():
    state = {
        "workspace_learning_result_daf": object(),
        "workspace_learning_result_dsi": object(),
    }
    daf_result = CareerSearchResult()
    WorkspaceSearchCache.set(state, "daf", daf_result)
    WorkspaceSearchCache.activate_profile(state, "daf")

    previous = synchronize_profile_selection(
        state,
        profile_id="dsi",
        learning_result_key_prefix="workspace_learning_result",
    )

    assert previous == "daf"
    assert WorkspaceSearchCache.get(state, "daf") is None
    assert "workspace_learning_result_daf" not in state
    assert "workspace_learning_result_dsi" in state


def test_learning_cache_rejects_result_from_another_profile():
    result = WorkspaceLearningResult(
        detected=(),
        stored=(),
        summary=WorkspaceLearningSummary.from_suggestions(()),
        profile_id="dsi",
    )
    state = {"workspace_learning_result_daf": result}

    assert get_profile_learning_result(
        state,
        profile_id="daf",
        learning_result_key_prefix="workspace_learning_result",
    ) is None
    assert "workspace_learning_result_daf" not in state

class FakeCVService:

    def __init__(self) -> None:
        self.renamed = []

    def rename_cv(self, cv_id, new_title):
        self.renamed.append(
            (cv_id, new_title)
        )
        return "renamed"


class FakeAssociationService:

    def __init__(self) -> None:
        self.calls = []

    def delete_cv(self, cv_id, force=False):
        self.calls.append(
            ("delete", cv_id, force)
        )
        return "deleted"

    def attach_cv(
        self,
        profile_id,
        cv_id,
        is_primary=False,
    ):
        self.calls.append(
            (
                "attach",
                profile_id,
                cv_id,
                is_primary,
            )
        )
        return "attached"

    def detach_cv(self, profile_id, cv_id):
        self.calls.append(
            ("detach", profile_id, cv_id)
        )
        return "detached"

    def set_primary_cv(
        self,
        profile_id,
        cv_id,
    ):
        self.calls.append(
            ("primary", profile_id, cv_id)
        )
        return "primary"


class FakeAssociationRepository:

    def list_for_cv(self, cv_id):
        return [
            f"association:{cv_id}"
        ]


class FakeProfileService:

    def list_profiles(self):
        return [
            "dsi_cio",
            "data_engineer",
            "cloud_architect",
        ]


class TestWorkspaceCVActions(
    unittest.TestCase
):

    def setUp(self) -> None:
        self.cv_service = FakeCVService()
        self.association_service = (
            FakeAssociationService()
        )

        self.actions = WorkspaceCVActions(
            cv_service=self.cv_service,
            association_service=(
                self.association_service
            ),
            association_repository=(
                FakeAssociationRepository()
            ),
            profile_service=(
                FakeProfileService()
            ),
        )

    def test_rename_delegates(self):
        result = self.actions.rename_cv(
            "cv-1",
            "CV DSI",
        )

        self.assertEqual(
            result,
            "renamed",
        )

        self.assertEqual(
            self.cv_service.renamed,
            [("cv-1", "CV DSI")],
        )

    def test_attach_delegates(self):
        self.actions.attach_cv(
            profile_id="dsi_cio",
            cv_id="cv-1",
            is_primary=True,
        )

        self.assertIn(
            (
                "attach",
                "dsi_cio",
                "cv-1",
                True,
            ),
            self.association_service.calls,
        )

    def test_detach_delegates(self):
        self.actions.detach_cv(
            profile_id="dsi_cio",
            cv_id="cv-1",
        )

        self.assertIn(
            (
                "detach",
                "dsi_cio",
                "cv-1",
            ),
            self.association_service.calls,
        )

    def test_set_primary_delegates(self):
        self.actions.set_primary_cv(
            profile_id="dsi_cio",
            cv_id="cv-1",
        )

        self.assertIn(
            (
                "primary",
                "dsi_cio",
                "cv-1",
            ),
            self.association_service.calls,
        )

    def test_delete_delegates_force(self):
        self.actions.delete_cv(
            "cv-1",
            force=True,
        )

        self.assertIn(
            ("delete", "cv-1", True),
            self.association_service.calls,
        )

    def test_available_profiles_excludes_associated(
        self,
    ):
        result = (
            self.actions
            .available_profile_ids(
                [
                    "dsi_cio",
                    "cloud_architect",
                ]
            )
        )

        self.assertEqual(
            result,
            ["data_engineer"],
        )

    def test_associations_are_listed(self):
        self.assertEqual(
            self.actions.associations_for_cv(
                "cv-1"
            ),
            ["association:cv-1"],
        )


if __name__ == "__main__":
    unittest.main()
