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
from src.cvs.exceptions import (
    CVNotFoundError,
)
from src.workspace.builder import (
    build_workspace,
)
from src.workspace.exceptions import (
    WorkspaceResourceNotFoundError,
)


PDF_CONTENT = (
    b"%PDF-1.4\n"
    b"Workspace CV\n"
    b"%%EOF\n"
)


class TestWorkspaceModel(
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

    def tearDown(self) -> None:
        self.temporary_directory.cleanup()

    def create_profile(
        self,
        profile_id: str,
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
                    "name": profile_id,
                    "keywords": [],
                    "locations": [],
                    "salary_min": 0,
                    "remote": True,
                }
            ),
            encoding="utf-8",
        )

    def test_service_shortcuts(self):
        self.assertIs(
            self.workspace.cv_service,
            self.workspace
            .services
            .cv_service,
        )

        self.assertIs(
            self.workspace.profile_service,
            self.workspace
            .services
            .profile_service,
        )

    def test_select_existing_profile(self):
        self.create_profile(
            "dsi_cio"
        )

        selected = (
            self.workspace
            .select_profile(
                "dsi_cio"
            )
        )

        self.assertEqual(
            selected
            .state
            .selected_profile_id,
            "dsi_cio",
        )

    def test_unknown_profile_is_rejected(
        self,
    ):
        with self.assertRaises(
            WorkspaceResourceNotFoundError
        ):
            self.workspace.select_profile(
                "unknown"
            )

    def test_select_existing_cv(self):
        document = (
            self.workspace
            .cv_repository
            .import_bytes(
                content=PDF_CONTENT,
                title="CV Workspace",
                original_filename="cv.pdf",
            )
        )

        selected = (
            self.workspace
            .select_cv(document.cv_id)
        )

        self.assertEqual(
            selected.state.selected_cv_id,
            document.cv_id,
        )

    def test_unknown_cv_is_rejected(self):
        with self.assertRaises(
            WorkspaceResourceNotFoundError
        ):
            self.workspace.select_cv(
                "00000000-0000-0000-0000-000000000000"
            )

    def test_workspace_is_user_scoped(self):
        document = (
            self.workspace
            .cv_repository
            .import_bytes(
                content=PDF_CONTENT,
                title="CV Workspace",
                original_filename="cv.pdf",
            )
        )

        self.assertTrue(
            self.workspace
            .cv_repository
            .exists(document.cv_id)
        )

        with self.assertRaises(
            CVNotFoundError
        ):
            self.workspace.cv_repository.get(
                "00000000-0000-0000-0000-000000000000"
            )


if __name__ == "__main__":
    unittest.main()