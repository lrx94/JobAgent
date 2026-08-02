from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from src.storage.user_paths import (
    InvalidStorageIdentifierError,
    UnsafeStoragePathError,
    UserStoragePaths,
)


class TestUserStoragePaths(
    unittest.TestCase
):

    def setUp(self) -> None:
        self.temporary_directory = (
            tempfile.TemporaryDirectory()
        )

        self.root = (
            Path(
                self.temporary_directory.name
            )
            / "users"
        )

        self.paths = UserStoragePaths(
            user_id="user-123",
            root_directory=self.root,
        )

    def tearDown(self) -> None:
        self.temporary_directory.cleanup()

    def test_user_directory_is_under_root(self):
        self.assertEqual(
            self.paths.user_directory,
            (
                self.root.resolve()
                / "user-123"
            ),
        )

    def test_standard_directories_are_under_user_root(
        self,
    ):
        directories = (
            self.paths.profiles_directory,
            self.paths.cvs_directory,
            self.paths.jobs_directory,
            self.paths.exports_directory,
            self.paths.cache_directory,
        )

        for directory in directories:
            self.assertIn(
                self.paths.user_directory,
                directory.parents,
            )

    def test_settings_file_is_under_user_root(
        self,
    ):
        self.assertEqual(
            self.paths.settings_file,
            (
                self.paths.user_directory
                / "settings.json"
            ),
        )

    def test_jobs_database_is_under_jobs_directory(
        self,
    ):
        self.assertEqual(
            self.paths.jobs_database_file,
            (
                self.paths.jobs_directory
                / "jobs.db"
            ),
        )

    def test_profile_directory_is_isolated(
        self,
    ):
        self.assertEqual(
            self.paths.profile_directory(
                "dsi_cio"
            ),
            (
                self.paths.profiles_directory
                / "dsi_cio"
            ),
        )

    def test_profile_config_file_is_built(
        self,
    ):
        self.assertEqual(
            self.paths.profile_config_file(
                "data_engineer"
            ),
            (
                self.paths.profiles_directory
                / "data_engineer"
                / "config.json"
            ),
        )

    def test_cv_directory_is_built(self):
        self.assertEqual(
            self.paths.cv_directory(
                "cv-123"
            ),
            (
                self.paths.cvs_directory
                / "cv-123"
            ),
        )

    def test_cv_document_file_uses_pdf_by_default(
        self,
    ):
        self.assertEqual(
            self.paths.cv_document_file(
                "cv-123"
            ),
            (
                self.paths.cvs_directory
                / "cv-123"
                / "document.pdf"
            ),
        )

    def test_cv_document_accepts_normalized_extension(
        self,
    ):
        self.assertEqual(
            self.paths.cv_document_file(
                "cv-123",
                extension="PDF",
            ).suffix,
            ".pdf",
        )

    def test_cv_metadata_file_is_built(self):
        self.assertEqual(
            self.paths.cv_metadata_file(
                "cv-123"
            ),
            (
                self.paths.cvs_directory
                / "cv-123"
                / "metadata.json"
            ),
        )

    def test_export_file_is_built(self):
        self.assertEqual(
            self.paths.export_file(
                "results.csv"
            ),
            (
                self.paths.exports_directory
                / "results.csv"
            ),
        )

    def test_empty_user_id_is_rejected(self):
        with self.assertRaises(
            InvalidStorageIdentifierError
        ):
            UserStoragePaths(
                user_id="",
                root_directory=self.root,
            )

    def test_parent_traversal_user_id_is_rejected(
        self,
    ):
        with self.assertRaises(
            InvalidStorageIdentifierError
        ):
            UserStoragePaths(
                user_id="../other",
                root_directory=self.root,
            )

    def test_absolute_user_id_is_rejected(self):
        with self.assertRaises(
            InvalidStorageIdentifierError
        ):
            UserStoragePaths(
                user_id="/tmp/other",
                root_directory=self.root,
            )

    def test_invalid_profile_id_is_rejected(self):
        with self.assertRaises(
            InvalidStorageIdentifierError
        ):
            self.paths.profile_directory(
                "../../admin"
            )

    def test_invalid_cv_id_is_rejected(self):
        with self.assertRaises(
            InvalidStorageIdentifierError
        ):
            self.paths.cv_directory(
                "cv/other"
            )

    def test_invalid_export_filename_is_rejected(
        self,
    ):
        with self.assertRaises(
            InvalidStorageIdentifierError
        ):
            self.paths.export_file(
                "../secret.txt"
            )

    def test_absolute_filename_is_rejected(self):
        with self.assertRaises(
            InvalidStorageIdentifierError
        ):
            self.paths.cache_file(
                "/tmp/cache.json"
            )

    def test_invalid_extension_is_rejected(self):
        with self.assertRaises(
            InvalidStorageIdentifierError
        ):
            self.paths.cv_document_file(
                "cv-123",
                extension="../pdf",
            )

    def test_ensure_directories_creates_structure(
        self,
    ):
        self.paths.ensure_directories()

        expected_directories = (
            self.paths.user_directory,
            self.paths.profiles_directory,
            self.paths.cvs_directory,
            self.paths.jobs_directory,
            self.paths.exports_directory,
            self.paths.cache_directory,
        )

        for directory in expected_directories:
            self.assertTrue(
                directory.is_dir()
            )

    def test_ensure_directories_is_idempotent(
        self,
    ):
        self.paths.ensure_directories()
        self.paths.ensure_directories()

        self.assertTrue(
            self.paths.user_directory.is_dir()
        )

    def test_ensure_profile_directory_creates_it(
        self,
    ):
        directory = (
            self.paths
            .ensure_profile_directory(
                "dsi_cio"
            )
        )

        self.assertTrue(
            directory.is_dir()
        )

    def test_ensure_cv_directory_creates_it(
        self,
    ):
        directory = (
            self.paths
            .ensure_cv_directory(
                "cv-123"
            )
        )

        self.assertTrue(
            directory.is_dir()
        )

    def test_owned_path_is_accepted(self):
        self.paths.ensure_directories()

        owned = (
            self.paths.user_directory
            / "profiles"
        )

        self.assertEqual(
            self.paths.assert_owned_path(
                owned
            ),
            owned.resolve(),
        )

    def test_foreign_user_path_is_rejected(self):
        foreign_path = (
            self.root
            / "other-user"
            / "profiles"
        )

        with self.assertRaises(
            UnsafeStoragePathError
        ):
            self.paths.assert_owned_path(
                foreign_path
            )

    def test_path_outside_root_is_rejected(self):
        outside = (
            Path(
                self.temporary_directory.name
            )
            / "outside.txt"
        )

        with self.assertRaises(
            UnsafeStoragePathError
        ):
            self.paths.assert_owned_path(
                outside
            )

    def test_two_users_have_separate_directories(
        self,
    ):
        other = UserStoragePaths(
            user_id="user-456",
            root_directory=self.root,
        )

        self.assertNotEqual(
            self.paths.user_directory,
            other.user_directory,
        )

    def test_two_users_can_share_profile_slug(
        self,
    ):
        other = UserStoragePaths(
            user_id="user-456",
            root_directory=self.root,
        )

        first_profile = (
            self.paths.profile_directory(
                "dsi_cio"
            )
        )

        second_profile = (
            other.profile_directory(
                "dsi_cio"
            )
        )

        self.assertNotEqual(
            first_profile,
            second_profile,
        )


if __name__ == "__main__":
    unittest.main()