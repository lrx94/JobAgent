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
from src.profile import Profile
from src.workspace import build_workspace
from src.workspace.ui import (
    build_workspace_snapshot,
    format_file_size,
    profile_display_name,
)


PDF_CONTENT = (
    b"%PDF-1.4\n"
    b"Career Workspace test\n"
    b"%%EOF\n"
)


class TestWorkspaceUIPresenter(
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
        name: str = "DSI / CIO",
    ):
        return (
            self.workspace
            .profile_service
            .create_profile(
                profile=Profile(
                    name=name,
                    keywords=[
                        "gouvernance si",
                        "cobit",
                    ],
                    locations=["Paris"],
                    salary_min=100000,
                    remote=True,
                )
            )
        )

    def create_cv(
        self,
        content: bytes = PDF_CONTENT,
    ):
        return (
            self.workspace
            .cv_service
            .import_bytes(
                content=content,
                title="CV DSI",
                original_filename="cv_dsi.pdf",
                analyze=False,
            )
        )

    def test_empty_snapshot(self):
        snapshot = build_workspace_snapshot(
            self.workspace
        )

        self.assertEqual(
            snapshot.profile_count,
            0,
        )

        self.assertEqual(
            snapshot.cv_count,
            0,
        )

    def test_profile_is_present(self):
        result = self.create_profile()

        snapshot = build_workspace_snapshot(
            self.workspace
        )

        profile = snapshot.get_profile(
            result.profile_id
        )

        self.assertIsNotNone(profile)

        self.assertEqual(
            profile.display_name,
            "DSI / CIO",
        )

    def test_unassigned_cv_is_present(self):
        result = self.create_cv()

        snapshot = build_workspace_snapshot(
            self.workspace
        )

        self.assertEqual(
            len(snapshot.unassigned_cvs),
            1,
        )

        self.assertEqual(
            snapshot.unassigned_cvs[0].cv_id,
            result.cv_id,
        )

    def test_associated_cv_is_under_profile(
        self,
    ):
        profile_result = (
            self.create_profile()
        )

        cv_result = self.create_cv()

        (
            self.workspace
            .association_service
            .attach_cv(
                profile_id=(
                    profile_result.profile_id
                ),
                cv_id=cv_result.cv_id,
                is_primary=True,
            )
        )

        snapshot = build_workspace_snapshot(
            self.workspace
        )

        profile = snapshot.get_profile(
            profile_result.profile_id
        )

        self.assertIsNotNone(profile)

        self.assertEqual(
            profile.cv_count,
            1,
        )

        self.assertEqual(
            profile.primary_cv.cv_id,
            cv_result.cv_id,
        )

        self.assertEqual(
            snapshot.unassigned_cvs,
            (),
        )

    def test_cv_count_deduplicates_associations(
        self,
    ):
        first_profile = self.create_profile(
            "DSI / CIO"
        )

        second_profile = self.create_profile(
            "Directeur Transformation"
        )

        cv_result = self.create_cv()

        for profile_result in (
            first_profile,
            second_profile,
        ):
            (
                self.workspace
                .association_service
                .attach_cv(
                    profile_id=(
                        profile_result.profile_id
                    ),
                    cv_id=cv_result.cv_id,
                )
            )

        snapshot = build_workspace_snapshot(
            self.workspace
        )

        self.assertEqual(
            snapshot.cv_count,
            1,
        )

    def test_file_size_format(self):
        self.assertEqual(
            format_file_size(500),
            "500 o",
        )

        self.assertEqual(
            format_file_size(2048),
            "2.0 Ko",
        )

        self.assertEqual(
            format_file_size(
                3 * 1024 * 1024
            ),
            "3.0 Mo",
        )

    def test_profile_name_fallback(self):
        self.assertEqual(
            profile_display_name(
                "data_engineer",
                {},
            ),
            "Data Engineer",
        )


if __name__ == "__main__":
    unittest.main()