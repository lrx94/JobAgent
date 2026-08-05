import tempfile
import unittest
from pathlib import Path

from src.storage.user_paths import UserStoragePaths
from src.workspace.profile_delete_service import (
    ProfileDeleteService,
)


class TestProfileDeleteService(
    unittest.TestCase,
):

    def setUp(self):
        self.tempdir = (
            tempfile.TemporaryDirectory()
        )

        self.paths = UserStoragePaths(
            user_id="user",
            root_directory=self.tempdir.name,
        )

        self.paths.ensure_directories()

        self.profile = (
            self.paths.profile_directory(
                "demo"
            )
        )

        self.profile.mkdir(
            parents=True,
            exist_ok=True,
        )

        (
            self.profile / "config.json"
        ).write_text(
            "{}",
            encoding="utf-8",
        )

        self.service = (
            ProfileDeleteService(
                self.paths
            )
        )

    def tearDown(self):
        self.tempdir.cleanup()

    def test_delete_profile(self):
        self.assertTrue(
            self.profile.exists()
        )

        self.service.delete(
            "demo"
        )

        self.assertFalse(
            self.profile.exists()
        )

    def test_unknown_profile(self):
        with self.assertRaises(
            FileNotFoundError
        ):
            self.service.delete(
                "unknown"
            )

    def test_empty_profile(self):
        with self.assertRaises(
            ValueError
        ):
            self.service.delete("")