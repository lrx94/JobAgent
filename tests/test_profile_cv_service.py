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
from src.cvs.exceptions import (
    CVStillInUseError,
)
from src.cvs.profile_cv_repository import (
    ProfileCVRepository,
)
from src.cvs.profile_cv_service import (
    ProfileCVService,
)
from src.cvs.repository import (
    CVRepository,
)


PDF_CONTENT = (
    b"%PDF-1.4\nCV Test\n%%EOF\n"
)


class TestProfileCVService(
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

        self.context = UserContext(
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

        self.cv_repository = CVRepository(
            user_context=self.context,
            storage_root=self.storage_root,
        )

        self.association_repository = (
            ProfileCVRepository(
                user_context=self.context,
                cv_repository=(
                    self.cv_repository
                ),
                storage_root=self.storage_root,
            )
        )

        self.service = ProfileCVService(
            association_repository=(
                self.association_repository
            ),
            cv_repository=(
                self.cv_repository
            ),
        )

        directory = (
            self.association_repository
            .paths
            .ensure_profile_directory(
                "dsi_cio"
            )
        )

        (
            directory
            / "config.json"
        ).write_text(
            "{}",
            encoding="utf-8",
        )

    def tearDown(self) -> None:
        self.temporary_directory.cleanup()

    def create_cv(self):
        return self.cv_repository.import_bytes(
            content=PDF_CONTENT,
            title="CV DSI",
            original_filename="cv.pdf",
        )

    def test_attach_and_list_profile_cvs(
        self,
    ):
        document = self.create_cv()

        self.service.attach_cv(
            profile_id="dsi_cio",
            cv_id=document.cv_id,
        )

        documents = (
            self.service
            .list_profile_cvs(
                "dsi_cio"
            )
        )

        self.assertEqual(
            len(documents),
            1,
        )

        self.assertEqual(
            documents[0].cv_id,
            document.cv_id,
        )

    def test_get_primary_cv(self):
        document = self.create_cv()

        self.service.attach_cv(
            "dsi_cio",
            document.cv_id,
        )

        primary = (
            self.service.get_primary_cv(
                "dsi_cio"
            )
        )

        self.assertIsNotNone(primary)

        self.assertEqual(
            primary.cv_id,
            document.cv_id,
        )

    def test_delete_used_cv_is_rejected(
        self,
    ):
        document = self.create_cv()

        self.service.attach_cv(
            "dsi_cio",
            document.cv_id,
        )

        with self.assertRaises(
            CVStillInUseError
        ):
            self.service.delete_cv(
                document.cv_id
            )

    def test_force_delete_detaches_and_deletes(
        self,
    ):
        document = self.create_cv()

        self.service.attach_cv(
            "dsi_cio",
            document.cv_id,
        )

        self.service.delete_cv(
            document.cv_id,
            force=True,
        )

        self.assertFalse(
            self.cv_repository.exists(
                document.cv_id
            )
        )

        self.assertEqual(
            self.association_repository
            .list_for_cv(
                document.cv_id
            ),
            [],
        )

    def test_list_profiles_for_cv(self):
        document = self.create_cv()

        self.service.attach_cv(
            "dsi_cio",
            document.cv_id,
        )

        self.assertEqual(
            self.service
            .list_profiles_for_cv(
                document.cv_id
            ),
            ["dsi_cio"],
        )


if __name__ == "__main__":
    unittest.main()