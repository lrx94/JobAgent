from __future__ import annotations

import unittest
from dataclasses import FrozenInstanceError

from src.auth.models import (
    CurrentUser,
    Role,
)


class TestCurrentUser(unittest.TestCase):

    def create_user(
        self,
        **overrides,
    ) -> CurrentUser:
        values = {
            "user_id": "user-123",
            "subject": "google-subject-123",
            "email": "Ludovic@Example.com",
            "display_name": "Ludovic",
            "authenticated": True,
            "authorized": True,
            "roles": (
                Role.USER,
            ),
        }

        values.update(overrides)

        return CurrentUser(
            **values
        )

    def test_creates_authenticated_user(self):
        user = self.create_user()

        self.assertEqual(
            user.user_id,
            "user-123",
        )

        self.assertEqual(
            user.subject,
            "google-subject-123",
        )

        self.assertEqual(
            user.email,
            "ludovic@example.com",
        )

        self.assertTrue(
            user.authenticated
        )

        self.assertTrue(
            user.authorized
        )

        self.assertTrue(
            user.can_access_application
        )

    def test_user_without_roles_is_supported(self):
        user = self.create_user(
            roles=(),
        )

        self.assertEqual(
            user.roles,
            (),
        )

        self.assertFalse(
            user.is_admin
        )

        self.assertFalse(
            user.is_beta_tester
        )

        self.assertFalse(
            user.is_user
        )

    def test_admin_role_is_detected(self):
        user = self.create_user(
            roles=(
                Role.USER,
                Role.ADMIN,
            ),
        )

        self.assertTrue(
            user.is_admin
        )

        self.assertTrue(
            user.has_role(
                Role.ADMIN
            )
        )

    def test_beta_tester_role_is_detected(self):
        user = self.create_user(
            roles=(
                "user",
                "beta_tester",
            ),
        )

        self.assertTrue(
            user.is_beta_tester
        )

        self.assertEqual(
            user.roles,
            (
                Role.USER,
                Role.BETA_TESTER,
            ),
        )

    def test_current_user_is_immutable(self):
        user = self.create_user()

        with self.assertRaises(
            FrozenInstanceError
        ):
            user.email = "other@example.com"

    def test_duplicate_roles_are_removed(self):
        user = self.create_user(
            roles=(
                Role.USER,
                Role.USER,
                "admin",
                Role.ADMIN,
            ),
        )

        self.assertEqual(
            user.roles,
            (
                Role.USER,
                Role.ADMIN,
            ),
        )

    def test_missing_display_name_uses_email_prefix(
        self,
    ):
        user = self.create_user(
            display_name="",
        )

        self.assertEqual(
            user.display_name,
            "ludovic",
        )

    def test_invalid_email_is_rejected(self):
        with self.assertRaisesRegex(
            ValueError,
            "email est invalide",
        ):
            self.create_user(
                email="invalid-email",
            )

    def test_missing_subject_is_rejected(self):
        with self.assertRaisesRegex(
            ValueError,
            "subject est obligatoire",
        ):
            self.create_user(
                subject="",
            )

    def test_unknown_role_is_rejected(self):
        with self.assertRaisesRegex(
            ValueError,
            "Rôle inconnu",
        ):
            self.create_user(
                roles=(
                    "superhero",
                ),
            )


if __name__ == "__main__":
    unittest.main()