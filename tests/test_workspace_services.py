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
from src.workspace.services import (
    WorkspaceServices,
)


class TestWorkspaceServices(
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
    ) -> UserContext:
        return UserContext(
            current_user=CurrentUser(
                user_id=user_id,
                subject=f"subject-{user_id}",
                email=f"{user_id}@example.com",
                display_name=user_id,
                authenticated=True,
                authorized=True,
                roles=(Role.USER,),
            )
        )

    def test_services_are_created(self):
        workspace = build_workspace(
            user_context=self.create_context(),
            storage_root=self.storage_root,
        )

        self.assertIsInstance(
            workspace.services,
            WorkspaceServices,
        )

    def test_services_share_user_id(self):
        workspace = build_workspace(
            user_context=self.create_context(),
            storage_root=self.storage_root,
        )

        services = workspace.services

        self.assertEqual(
            services.profile_service.user_id,
            "user-123",
        )

        self.assertEqual(
            services.cv_service.user_id,
            "user-123",
        )

        self.assertEqual(
            services.association_service.user_id,
            "user-123",
        )

    def test_cv_repository_is_shared(self):
        workspace = build_workspace(
            user_context=self.create_context(),
            storage_root=self.storage_root,
        )

        services = workspace.services

        self.assertIs(
            services.cv_service.repository,
            services.cv_repository,
        )

        self.assertIs(
            services
            .association_repository
            .cv_repository,
            services.cv_repository,
        )

        self.assertIs(
            services
            .association_service
            .cv_repository,
            services.cv_repository,
        )

    def test_storage_directories_are_shared(
        self,
    ):
        workspace = build_workspace(
            user_context=self.create_context(),
            storage_root=self.storage_root,
        )

        services = workspace.services

        self.assertEqual(
            services
            .profile_service
            .profiles_directory
            .resolve(),
            services
            .paths
            .profiles_directory
            .resolve(),
        )

        self.assertEqual(
            services
            .cv_repository
            .paths
            .cvs_directory
            .resolve(),
            services
            .paths
            .cvs_directory
            .resolve(),
        )


if __name__ == "__main__":
    unittest.main()