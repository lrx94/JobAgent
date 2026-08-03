from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from src.auth.exceptions import (
    AuthorizationConfigurationError,
)
from src.auth.repositories.allowlist_repository import (
    AllowListRepository,
)


class TestAllowListRepository(
    unittest.TestCase
):

    def setUp(self) -> None:
        self.temporary_directory = (
            tempfile.TemporaryDirectory()
        )

        self.root = Path(
            self.temporary_directory.name
        )

        self.path = (
            self.root
            / "allowed_users.json"
        )

    def tearDown(self) -> None:
        self.temporary_directory.cleanup()

    def write_json(
        self,
        value,
    ) -> None:
        self.path.write_text(
            json.dumps(value),
            encoding="utf-8",
        )

    def test_missing_file_returns_empty_set(self):
        repository = AllowListRepository(
            path=self.path
        )

        self.assertEqual(
            repository.allowed_emails(),
            set(),
        )

    def test_empty_file_returns_empty_set(self):
        self.path.write_text(
            "",
            encoding="utf-8",
        )

        repository = AllowListRepository(
            path=self.path
        )

        self.assertEqual(
            repository.allowed_emails(),
            set(),
        )

    def test_invalid_json_is_rejected(self):
        self.path.write_text(
            "{invalid",
            encoding="utf-8",
        )

        repository = AllowListRepository(
            path=self.path
        )

        with self.assertRaises(
            AuthorizationConfigurationError
        ):
            repository.allowed_emails()

    def test_object_format_is_loaded(self):
        self.write_json(
            {
                "allowed_emails": [
                    "ludovic@example.com",
                ]
            }
        )

        repository = AllowListRepository(
            path=self.path
        )

        self.assertEqual(
            repository.allowed_emails(),
            {
                "ludovic@example.com",
            },
        )

    def test_list_format_is_loaded(self):
        self.write_json(
            [
                "ludovic@example.com",
            ]
        )

        repository = AllowListRepository(
            path=self.path
        )

        self.assertTrue(
            repository.is_allowed_email(
                "ludovic@example.com"
            )
        )

    def test_emails_are_normalized(self):
        repository = AllowListRepository(
            emails=[
                " Ludovic@Example.COM ",
            ]
        )

        self.assertEqual(
            repository.allowed_emails(),
            {
                "ludovic@example.com",
            },
        )

    def test_duplicates_and_empty_values_are_removed(
        self,
    ):
        repository = AllowListRepository(
            emails=[
                "ludovic@example.com",
                "LUDOVIC@example.com",
                "",
                "   ",
            ]
        )

        self.assertEqual(
            repository.allowed_emails(),
            {
                "ludovic@example.com",
            },
        )

    def test_lookup_is_case_insensitive(self):
        repository = AllowListRepository(
            emails=[
                "ludovic@example.com",
            ]
        )

        self.assertTrue(
            repository.is_allowed_email(
                " LUDOVIC@EXAMPLE.COM "
            )
        )

    def test_unknown_email_is_rejected(self):
        repository = AllowListRepository(
            emails=[
                "ludovic@example.com",
            ]
        )

        self.assertFalse(
            repository.is_allowed_email(
                "other@example.com"
            )
        )

    def test_allowed_emails_returns_defensive_copy(
        self,
    ):
        repository = AllowListRepository(
            emails=[
                "ludovic@example.com",
            ]
        )

        result = repository.allowed_emails()
        result.add("intruder@example.com")

        self.assertNotIn(
            "intruder@example.com",
            repository.allowed_emails(),
        )

    def test_file_is_cached_until_reload(self):
        self.write_json(
            {
                "allowed_emails": [
                    "first@example.com",
                ]
            }
        )

        repository = AllowListRepository(
            path=self.path
        )

        repository.allowed_emails()

        self.write_json(
            {
                "allowed_emails": [
                    "second@example.com",
                ]
            }
        )

        self.assertTrue(
            repository.is_allowed_email(
                "first@example.com"
            )
        )

        repository.reload()

        self.assertTrue(
            repository.is_allowed_email(
                "second@example.com"
            )
        )

    def test_path_and_emails_cannot_be_combined(self):
        with self.assertRaises(
            ValueError
        ):
            AllowListRepository(
                path=self.path,
                emails=[
                    "ludovic@example.com",
                ],
            )

    def test_invalid_email_is_rejected(self):
        repository = AllowListRepository(
            emails=[
                "invalid-email",
            ]
        )

        with self.assertRaises(
            AuthorizationConfigurationError
        ):
            repository.allowed_emails()


if __name__ == "__main__":
    unittest.main()