from __future__ import annotations

import io
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
from src.workspace.builder import (
    build_workspace,
)
from src.workspace.onboarding import (
    WorkspaceOnboardingError,
)


PDF_CONTENT = (
    b"%PDF-1.4\n"
    b"JobAgent onboarding test\n"
    b"%%EOF\n"
)


class TestWorkspaceOnboarding(
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

        self.workspace = build_workspace(
            user_context=self.create_context(),
            storage_root=self.storage_root,
        )

    def tearDown(self) -> None:
        self.temporary_directory.cleanup()

    @staticmethod
    def create_context() -> UserContext:
        return UserContext(
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

    @staticmethod
    def create_profile() -> Profile:
        return Profile(
            name="DSI / CIO",
            keywords=[
                "gouvernance si",
                "transformation si",
                "cobit",
            ],
            locations=["Paris"],
            salary_min=0,
            remote=True,
        )

    def test_create_from_bytes(self):
        result = (
            self.workspace
            .onboarding_service
            .create_from_bytes(
                content=PDF_CONTENT,
                original_filename="cv_dsi.pdf",
                profile=self.create_profile(),
                analyze=False,
            )
        )

        self.assertEqual(
            result.profile_id,
            "dsi_cio",
        )

        self.assertTrue(
            result.document.document_path.is_file()
        )

        self.assertTrue(
            result.is_primary
        )

    def test_profile_is_listed_after_onboarding(
        self,
    ):
        result = (
            self.workspace
            .onboarding_service
            .create_from_bytes(
                content=PDF_CONTENT,
                original_filename="cv_dsi.pdf",
                profile=self.create_profile(),
                analyze=False,
            )
        )

        self.assertIn(
            result.profile_id,
            self.workspace
            .profile_service
            .list_profiles(),
        )

    def test_cv_is_associated_to_profile(self):
        result = (
            self.workspace
            .onboarding_service
            .create_from_bytes(
                content=PDF_CONTENT,
                original_filename="cv_dsi.pdf",
                profile=self.create_profile(),
                analyze=False,
            )
        )

        associations = (
            self.workspace
            .association_repository
            .list_for_profile(
                result.profile_id
            )
        )

        self.assertEqual(
            len(associations),
            1,
        )

        self.assertEqual(
            associations[0].cv_id,
            result.cv_id,
        )

        self.assertTrue(
            associations[0].is_primary
        )

    def test_stream_import(self):
        result = (
            self.workspace
            .onboarding_service
            .create_from_stream(
                stream=io.BytesIO(
                    PDF_CONTENT
                ),
                original_filename="cv.pdf",
                profile=self.create_profile(),
                analyze=False,
            )
        )

        self.assertEqual(
            result.document.original_filename,
            "cv.pdf",
        )

    def test_duplicate_reuses_document(self):
        first = (
            self.workspace
            .onboarding_service
            .create_from_bytes(
                content=PDF_CONTENT,
                original_filename="cv.pdf",
                profile=self.create_profile(),
                analyze=False,
            )
        )

        second_profile = Profile(
            name="Directeur Transformation",
            keywords=[
                "transformation si",
            ],
            locations=["Paris"],
            salary_min=0,
            remote=True,
        )

        second = (
            self.workspace
            .onboarding_service
            .create_from_bytes(
                content=PDF_CONTENT,
                original_filename="copy.pdf",
                profile=second_profile,
                analyze=False,
            )
        )

        self.assertEqual(
            first.cv_id,
            second.cv_id,
        )

        self.assertTrue(
            second.duplicate_reused
        )

        self.assertEqual(
            len(
                self.workspace
                .cv_service
                .list_cvs()
            ),
            1,
        )

    def test_result_can_update_workspace_state(
        self,
    ):
        result = (
            self.workspace
            .onboarding_service
            .create_from_bytes(
                content=PDF_CONTENT,
                original_filename="cv.pdf",
                profile=self.create_profile(),
                analyze=False,
            )
        )

        selected_workspace = (
            self.workspace
            .select_onboarding_result(
                result
            )
        )

        self.assertEqual(
            selected_workspace
            .state
            .selected_profile_id,
            result.profile_id,
        )

        self.assertEqual(
            selected_workspace
            .state
            .selected_cv_id,
            result.cv_id,
        )

    def test_invalid_profile_type_is_rejected(
        self,
    ):
        with self.assertRaises(TypeError):
            (
                self.workspace
                .onboarding_service
                .create_from_bytes(
                    content=PDF_CONTENT,
                    original_filename="cv.pdf",
                    profile=object(),
                    analyze=False,
                )
            )

    def test_empty_stream_is_rejected(self):
        with self.assertRaises(Exception):
            (
                self.workspace
                .onboarding_service
                .create_from_stream(
                    stream=io.BytesIO(b""),
                    original_filename="cv.pdf",
                    profile=self.create_profile(),
                    analyze=False,
                )
            )

    def test_services_are_shared(self):
        onboarding = (
            self.workspace
            .onboarding_service
        )

        self.assertIs(
            onboarding.profile_service,
            self.workspace.profile_service,
        )

        self.assertIs(
            onboarding.cv_service,
            self.workspace.cv_service,
        )

        self.assertIs(
            onboarding.association_service,
            self.workspace.association_service,
        )


if __name__ == "__main__":
    unittest.main()