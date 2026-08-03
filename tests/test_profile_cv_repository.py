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
    ProfileCVAssociationNotFoundError,
    ProfileNotFoundError,
)
from src.cvs.profile_cv_repository import (
    ProfileCVRepository,
)
from src.cvs.repository import (
    CVRepository,
)


PDF_ONE = (
    b"%PDF-1.4\nFirst CV\n%%EOF\n"
)

PDF_TWO = (
    b"%PDF-1.4\nSecond CV\n%%EOF\n"
)


class TestProfileCVRepository(
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

        self.context = self.create_context(
            "user-123"
        )

        self.cv_repository = CVRepository(
            user_context=self.context,
            storage_root=self.storage_root,
        )

        self.repository = (
            ProfileCVRepository(
                user_context=self.context,
                cv_repository=(
                    self.cv_repository
                ),
                storage_root=self.storage_root,
            )
        )

        self.create_profile(
            "dsi_cio"
        )

        self.create_profile(
            "directeur_programme"
        )

    def tearDown(self) -> None:
        self.temporary_directory.cleanup()

    def create_context(
        self,
        user_id: str,
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

    def create_profile(
        self,
        profile_id: str,
    ) -> None:
        directory = (
            self.repository.paths
            .ensure_profile_directory(
                profile_id
            )
        )

        (
            directory
            / "config.json"
        ).write_text(
            "{}",
            encoding="utf-8",
        )

    def create_cv(
        self,
        content: bytes,
        title: str,
    ):
        return self.cv_repository.import_bytes(
            content=content,
            title=title,
            original_filename="cv.pdf",
        )

    def test_first_attachment_becomes_primary(
        self,
    ):
        document = self.create_cv(
            PDF_ONE,
            "CV DSI",
        )

        association = self.repository.attach(
            profile_id="dsi_cio",
            cv_id=document.cv_id,
        )

        self.assertTrue(
            association.is_primary
        )

    def test_second_attachment_is_not_primary(
        self,
    ):
        first = self.create_cv(
            PDF_ONE,
            "CV DSI",
        )

        second = self.create_cv(
            PDF_TWO,
            "CV Programme",
        )

        self.repository.attach(
            "dsi_cio",
            first.cv_id,
        )

        second_association = (
            self.repository.attach(
                "dsi_cio",
                second.cv_id,
            )
        )

        self.assertFalse(
            second_association.is_primary
        )

    def test_set_primary_is_unique(self):
        first = self.create_cv(
            PDF_ONE,
            "CV DSI",
        )

        second = self.create_cv(
            PDF_TWO,
            "CV Programme",
        )

        self.repository.attach(
            "dsi_cio",
            first.cv_id,
        )

        self.repository.attach(
            "dsi_cio",
            second.cv_id,
        )

        self.repository.set_primary(
            "dsi_cio",
            second.cv_id,
        )

        associations = (
            self.repository
            .list_for_profile(
                "dsi_cio"
            )
        )

        primary = [
            item
            for item in associations
            if item.is_primary
        ]

        self.assertEqual(
            len(primary),
            1,
        )

        self.assertEqual(
            primary[0].cv_id,
            second.cv_id,
        )

    def test_cv_can_be_attached_to_multiple_profiles(
        self,
    ):
        document = self.create_cv(
            PDF_ONE,
            "CV Direction",
        )

        self.repository.attach(
            "dsi_cio",
            document.cv_id,
        )

        self.repository.attach(
            "directeur_programme",
            document.cv_id,
        )

        associations = (
            self.repository
            .list_for_cv(
                document.cv_id
            )
        )

        self.assertEqual(
            len(associations),
            2,
        )

    def test_profile_can_have_multiple_cvs(
        self,
    ):
        first = self.create_cv(
            PDF_ONE,
            "CV DSI",
        )

        second = self.create_cv(
            PDF_TWO,
            "CV Programme",
        )

        self.repository.attach(
            "dsi_cio",
            first.cv_id,
        )

        self.repository.attach(
            "dsi_cio",
            second.cv_id,
        )

        self.assertEqual(
            len(
                self.repository
                .list_for_profile(
                    "dsi_cio"
                )
            ),
            2,
        )

    def test_detaching_primary_promotes_another(
        self,
    ):
        first = self.create_cv(
            PDF_ONE,
            "CV DSI",
        )

        second = self.create_cv(
            PDF_TWO,
            "CV Programme",
        )

        self.repository.attach(
            "dsi_cio",
            first.cv_id,
        )

        self.repository.attach(
            "dsi_cio",
            second.cv_id,
        )

        self.repository.detach(
            "dsi_cio",
            first.cv_id,
        )

        primary = (
            self.repository
            .get_primary(
                "dsi_cio"
            )
        )

        self.assertIsNotNone(primary)

        self.assertEqual(
            primary.cv_id,
            second.cv_id,
        )

    def test_unknown_association_is_rejected(
        self,
    ):
        with self.assertRaises(
            ProfileCVAssociationNotFoundError
        ):
            self.repository.detach(
                "dsi_cio",
                "cv-unknown",
            )

    def test_unknown_profile_is_rejected(self):
        document = self.create_cv(
            PDF_ONE,
            "CV DSI",
        )

        with self.assertRaises(
            ProfileNotFoundError
        ):
            self.repository.attach(
                "unknown_profile",
                document.cv_id,
            )

    def test_associations_are_persisted(self):
        document = self.create_cv(
            PDF_ONE,
            "CV DSI",
        )

        self.repository.attach(
            "dsi_cio",
            document.cv_id,
        )

        reloaded = ProfileCVRepository(
            user_context=self.context,
            cv_repository=(
                self.cv_repository
            ),
            storage_root=self.storage_root,
        )

        self.assertEqual(
            len(reloaded.list_all()),
            1,
        )

    def test_two_users_are_isolated(self):
        document = self.create_cv(
            PDF_ONE,
            "CV DSI",
        )

        self.repository.attach(
            "dsi_cio",
            document.cv_id,
        )

        other_context = self.create_context(
            "user-456"
        )

        other_cv_repository = CVRepository(
            user_context=other_context,
            storage_root=self.storage_root,
        )

        other_repository = (
            ProfileCVRepository(
                user_context=other_context,
                cv_repository=(
                    other_cv_repository
                ),
                storage_root=self.storage_root,
            )
        )

        self.assertEqual(
            other_repository.list_all(),
            [],
        )


if __name__ == "__main__":
    unittest.main()