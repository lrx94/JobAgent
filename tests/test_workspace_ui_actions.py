from __future__ import annotations

import unittest

import pytest

from src.workspace.ui.actions import (
    WorkspaceCVActions,
    ensure_profile_search,
    finalize_onboarding_session,
    get_profile_learning_result,
    run_profile_search,
    synchronize_profile_selection,
)
from src.career.search_workflow import CareerSearchResult
from src.workspace.search import WorkspaceSearchCache
from src.workspace.search import WorkspaceSearchError
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


def test_profile_transition_preserves_profile_scoped_results():
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
    assert WorkspaceSearchCache.get(state, "daf") is daf_result
    assert "workspace_learning_result_daf" in state
    assert "workspace_learning_result_dsi" in state


class FakeSearchService:
    def __init__(self, result: CareerSearchResult) -> None:
        self.result = result
        self.profile_ids: list[str] = []

    def search(self, profile_id: str) -> CareerSearchResult:
        self.profile_ids.append(profile_id)
        return self.result


class FailingSearchService:
    def search(self, profile_id: str) -> CareerSearchResult:
        raise RuntimeError(f"échec pour {profile_id}")


class WorkspaceFailingSearchService:
    def __init__(self) -> None:
        self.calls = 0

    def search(self, profile_id: str) -> CareerSearchResult:
        self.calls += 1
        raise WorkspaceSearchError(f"échec provider pour {profile_id}")


def test_first_search_uses_active_profile_and_populates_cache():
    state: dict = {}
    result = CareerSearchResult(all_jobs=[object()], jobs=[])
    service = FakeSearchService(result)

    returned = run_profile_search(
        state,
        profile_id="dsi-cio",
        search_service=service,
        dependent_cache_keys=("market_dsi-cio", "learning_dsi-cio"),
    )

    assert service.profile_ids == ["dsi-cio"]
    assert returned is result
    assert WorkspaceSearchCache.get(state, "dsi-cio") is result
    assert result.total_collected == 1
    assert result.total_relevant == 0


def test_ensure_search_initializes_profile_without_manual_action():
    state: dict = {}
    result = CareerSearchResult()
    service = FakeSearchService(result)

    availability = ensure_profile_search(
        state,
        profile_id="dsi",
        search_service=service,
        failure_cache_key="failure_dsi",
    )

    assert availability.result is result
    assert availability.searched is True
    assert availability.error is None
    assert service.profile_ids == ["dsi"]


def test_ensure_search_reuses_cached_zero_result_on_rerun():
    state: dict = {}
    result = CareerSearchResult()
    service = FakeSearchService(result)

    first = ensure_profile_search(
        state,
        profile_id="dsi",
        search_service=service,
        failure_cache_key="failure_dsi",
    )
    second = ensure_profile_search(
        state,
        profile_id="dsi",
        search_service=service,
        failure_cache_key="failure_dsi",
    )

    assert first.searched is True
    assert second.searched is False
    assert second.result is result
    assert service.profile_ids == ["dsi"]


def test_ensure_search_does_not_loop_after_workspace_error():
    state: dict = {}
    service = WorkspaceFailingSearchService()

    first = ensure_profile_search(
        state,
        profile_id="dsi",
        search_service=service,
        failure_cache_key="failure_dsi",
    )
    second = ensure_profile_search(
        state,
        profile_id="dsi",
        search_service=service,
        failure_cache_key="failure_dsi",
    )

    assert first.error == "échec provider pour dsi"
    assert second.error == first.error
    assert service.calls == 1


def test_manual_search_forces_refresh_after_automatic_initialization():
    state: dict = {}
    first = CareerSearchResult()
    second = CareerSearchResult(all_jobs=[object()])
    automatic_service = FakeSearchService(first)
    manual_service = FakeSearchService(second)

    ensure_profile_search(
        state,
        profile_id="dsi",
        search_service=automatic_service,
        failure_cache_key="failure_dsi",
    )
    run_profile_search(
        state,
        profile_id="dsi",
        search_service=manual_service,
        failure_cache_key="failure_dsi",
    )

    assert automatic_service.profile_ids == ["dsi"]
    assert manual_service.profile_ids == ["dsi"]
    assert WorkspaceSearchCache.get(state, "dsi") is second


def test_refresh_replaces_result_and_invalidates_profile_dependencies():
    old = CareerSearchResult()
    new = CareerSearchResult(all_jobs=[object()], jobs=[object()])
    state = {
        "market_dsi": object(),
        "learning_dsi": object(),
        "market_daf": object(),
    }
    WorkspaceSearchCache.set(state, "dsi", old)

    run_profile_search(
        state,
        profile_id="dsi",
        search_service=FakeSearchService(new),
        dependent_cache_keys=("market_dsi", "learning_dsi"),
    )

    assert WorkspaceSearchCache.get(state, "dsi") is new
    assert "market_dsi" not in state
    assert "learning_dsi" not in state
    assert "market_daf" in state


def test_failed_refresh_preserves_previous_result_and_dependencies():
    old = CareerSearchResult()
    market = object()
    state = {"market_dsi": market}
    WorkspaceSearchCache.set(state, "dsi", old)

    with pytest.raises(RuntimeError, match="échec pour dsi"):
        run_profile_search(
            state,
            profile_id="dsi",
            search_service=FailingSearchService(),
            dependent_cache_keys=("market_dsi",),
        )

    assert WorkspaceSearchCache.get(state, "dsi") is old
    assert state["market_dsi"] is market


def test_profile_caches_remain_independent_during_navigation():
    state: dict = {}
    dsi = CareerSearchResult()
    daf = CareerSearchResult()
    WorkspaceSearchCache.set(state, "dsi", dsi)
    WorkspaceSearchCache.activate_profile(state, "dsi")
    WorkspaceSearchCache.activate_profile(state, "daf")

    assert WorkspaceSearchCache.get(state, "daf") is None
    assert WorkspaceSearchCache.get(state, "dsi") is dsi

    run_profile_search(
        state,
        profile_id="daf",
        search_service=FakeSearchService(daf),
    )

    assert WorkspaceSearchCache.get(state, "dsi") is dsi
    assert WorkspaceSearchCache.get(state, "daf") is daf


def test_partial_provider_result_is_cached_with_its_warning():
    result = CareerSearchResult(
        all_jobs=[object()],
        jobs=[object()],
        provider_errors=["France Travail indisponible"],
    )
    state: dict = {}

    run_profile_search(
        state,
        profile_id="dsi",
        search_service=FakeSearchService(result),
    )

    cached = WorkspaceSearchCache.get(state, "dsi")
    assert cached is result
    assert cached.provider_errors == ["France Travail indisponible"]


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
