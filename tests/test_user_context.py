from __future__ import annotations

import unittest
from dataclasses import FrozenInstanceError

from src.auth.exceptions import (
    AccessDeniedError,
    AuthenticationRequiredError,
)
from src.auth.models import (
    CurrentUser,
    Role,
)
from src.auth.user_context import (
    UserContext,
)


class TestUserContext(unittest.TestCase):

    def create_user(
        self,
        **overrides,
    ) -> CurrentUser:
        values = {
            "user_id": "user-123",
            "subject": "google-subject-123",
            "email": "ludovic@example.com",
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

    def test_exposes_user_properties(self):
        context = UserContext(
            current_user=self.create_user()
        )

        self.assertEqual(
            context.user_id,
            "user-123",
        )

        self.assertEqual(
            context.subject,
            "google-subject-123",
        )

        self.assertEqual(
            context.email,
            "ludovic@example.com",
        )

        self.assertEqual(
            context.display_name,
            "Ludovic",
        )

        self.assertTrue(
            context.authenticated
        )

        self.assertTrue(
            context.authorized
        )

        self.assertTrue(
            context.can_access_application
        )

    def test_invalid_user_type_is_rejected(self):
        with self.assertRaises(
            TypeError
        ):
            UserContext(
                current_user=object()
            )

    def test_unauthenticated_user_is_rejected(
        self,
    ):
        context = UserContext(
            current_user=self.create_user(
                authenticated=False,
                authorized=False,
            )
        )

        with self.assertRaises(
            AuthenticationRequiredError
        ):
            context.require_authenticated()

    def test_authenticated_but_unauthorized_user_is_rejected(
        self,
    ):
        context = UserContext(
            current_user=self.create_user(
                authenticated=True,
                authorized=False,
            )
        )

        with self.assertRaises(
            AccessDeniedError
        ):
            context.require_authorized()

    def test_authorized_user_is_accepted(self):
        context = UserContext(
            current_user=self.create_user()
        )

        context.require_authenticated()
        context.require_authorized()

    def test_role_is_detected(self):
        context = UserContext(
            current_user=self.create_user(
                roles=(
                    Role.USER,
                    Role.ADMIN,
                )
            )
        )

        self.assertTrue(
            context.has_role(
                Role.ADMIN
            )
        )

    def test_required_role_is_accepted(self):
        context = UserContext(
            current_user=self.create_user(
                roles=(
                    Role.ADMIN,
                )
            )
        )

        context.require_role(
            Role.ADMIN
        )

    def test_missing_role_is_rejected(self):
        context = UserContext(
            current_user=self.create_user(
                roles=(
                    Role.USER,
                )
            )
        )

        with self.assertRaises(
            AccessDeniedError
        ):
            context.require_role(
                Role.ADMIN
            )

    def test_context_is_immutable(self):
        context = UserContext(
            current_user=self.create_user()
        )

        with self.assertRaises(
            FrozenInstanceError
        ):
            context.current_user = (
                self.create_user(
                    user_id="other"
                )
            )


if __name__ == "__main__":
    unittest.main()