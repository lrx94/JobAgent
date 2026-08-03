from __future__ import annotations

import unittest

from src.workspace.exceptions import (
    WorkspaceSelectionError,
)
from src.workspace.state import (
    WorkspaceState,
)


class TestWorkspaceState(unittest.TestCase):

    def test_default_state(self):
        state = WorkspaceState()

        self.assertIsNone(
            state.selected_profile_id
        )

        self.assertIsNone(
            state.selected_cv_id
        )

        self.assertEqual(
            state.active_view,
            "overview",
        )

    def test_select_profile(self):
        initial = WorkspaceState(
            selected_cv_id="cv-123"
        )

        selected = initial.select_profile(
            "dsi_cio"
        )

        self.assertEqual(
            selected.selected_profile_id,
            "dsi_cio",
        )

        self.assertIsNone(
            selected.selected_cv_id
        )

        self.assertIsNot(
            initial,
            selected,
        )

    def test_select_profile_can_keep_cv(self):
        initial = WorkspaceState(
            selected_cv_id="cv-123"
        )

        selected = initial.select_profile(
            "dsi_cio",
            clear_cv=False,
        )

        self.assertEqual(
            selected.selected_cv_id,
            "cv-123",
        )

    def test_select_cv(self):
        state = (
            WorkspaceState()
            .select_cv("cv-123")
        )

        self.assertEqual(
            state.selected_cv_id,
            "cv-123",
        )

    def test_change_view(self):
        state = (
            WorkspaceState()
            .change_view("skills")
        )

        self.assertEqual(
            state.active_view,
            "skills",
        )

    def test_invalid_view_is_rejected(self):
        with self.assertRaises(
            WorkspaceSelectionError
        ):
            WorkspaceState(
                active_view="unknown"
            )

    def test_invalid_identifier_is_rejected(
        self,
    ):
        with self.assertRaises(
            WorkspaceSelectionError
        ):
            WorkspaceState(
                selected_profile_id="../admin"
            )

    def test_empty_identifier_becomes_none(self):
        state = WorkspaceState(
            selected_profile_id="   "
        )

        self.assertIsNone(
            state.selected_profile_id
        )

    def test_clear_selection(self):
        state = WorkspaceState(
            selected_profile_id="dsi_cio",
            selected_cv_id="cv-123",
            selected_job_id="job-123",
            active_view="jobs",
        )

        cleared = state.clear_selection()

        self.assertFalse(
            cleared.has_profile_selection
        )

        self.assertFalse(
            cleared.has_cv_selection
        )

        self.assertFalse(
            cleared.has_job_selection
        )

        self.assertEqual(
            cleared.active_view,
            "jobs",
        )

    def test_serialization_round_trip(self):
        state = WorkspaceState(
            selected_profile_id="dsi_cio",
            selected_cv_id="cv-123",
            active_view="cvs",
        )

        rebuilt = WorkspaceState.from_dict(
            state.to_dict()
        )

        self.assertEqual(
            rebuilt,
            state,
        )

    def test_none_dict_creates_default(self):
        self.assertEqual(
            WorkspaceState.from_dict(None),
            WorkspaceState(),
        )


if __name__ == "__main__":
    unittest.main()