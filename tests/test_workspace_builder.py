from __future__ import annotations

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
from src.workspace.builder import (
    build_workspace,
)
from src.workspace.exceptions import (
    WorkspaceAccessError,
)
from src.workspace.state import (
    WorkspaceState,
)


class TestWorkspaceBuilder(
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

    def tearDown(self) -> None:
        self.temporary_directory.cleanup()

    def create_context(
        self,
        user_id: str = "user-123",
        authenticated: bool = True,
        authorized: bool = True,
    ) -> UserContext:
        return UserContext(
            current_user=CurrentUser(
                user_id=user_id,
                subject=f"subject-{user_id}",
                email=f"{user_id}@example.com",
                display_name=user_id,
                authenticated=authenticated,
                authorized=authorized,
                roles=(Role.USER,),
            )
        )

    def test_build_workspace(self):
        workspace = build_workspace(
            user_context=self.create_context(),
            storage_root=self.storage_root,
        )

        self.assertEqual(
            workspace.user_id,
            "user-123",
        )

    def test_directories_are_created(self):
        workspace = build_workspace(
            user_context=self.create_context(),
            storage_root=self.storage_root,
        )

        self.assertTrue(
            workspace
            .services
            .paths
            .profiles_directory
            .is_dir()
        )

        self.assertTrue(
            workspace
            .services
            .paths
            .cvs_directory
            .is_dir()
        )

    def test_custom_state_is_preserved(self):
        state = WorkspaceState(
            selected_profile_id="dsi_cio",
            active_view="skills",
        )

        workspace = build_workspace(
            user_context=self.create_context(),
            storage_root=self.storage_root,
            state=state,
        )

        self.assertIs(
            workspace.state,
            state,
        )

    def test_invalid_context_type_is_rejected(
        self,
    ):
        with self.assertRaises(
            TypeError
        ):
            build_workspace(
                user_context=object(),
                storage_root=self.storage_root,
            )

    def test_unauthorized_context_is_rejected(
        self,
    ):
        with self.assertRaises(
            WorkspaceAccessError
        ):
            build_workspace(
                user_context=self.create_context(
                    authorized=False
                ),
                storage_root=self.storage_root,
            )

    def test_two_users_are_isolated(self):
        first = build_workspace(
            user_context=self.create_context(
                "user-a"
            ),
            storage_root=self.storage_root,
        )

        second = build_workspace(
            user_context=self.create_context(
                "user-b"
            ),
            storage_root=self.storage_root,
        )

        self.assertNotEqual(
            first.storage_directory,
            second.storage_directory,
        )


if __name__ == "__main__":
    unittest.main()
