from __future__ import annotations

import unittest

from src.auth.exceptions import (
    AccessDeniedError,
    AuthenticationRequiredError,
)
from src.auth.models import (
    CurrentUser,
    Role,
)
from src.auth.repositories.allowlist_repository import (
    AllowListRepository,
)
from src.auth.services.authorization_service import (
    AuthorizationService,
)


class TestAuthorizationService(
    unittest.TestCase
):

    def setUp(self) -> None:
        repository = AllowListRepository(
            emails=[
                "ludovic@example.com",
                "admin@example.com",
            ]
        )

        self.service = AuthorizationService(
            repository=repository
        )

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
            "authorized": False,
            "roles": (
                Role.USER,
            ),
        }

        values.update(overrides)

        return CurrentUser(
            **values
        )

    def test_allowed_user_is_detected(self):
        self.assertTrue(
            self.service.is_allowed(
                self.create_user()
            )
        )

    def test_unknown_user_is_not_allowed(self):
        self.assertFalse(
            self.service.is_allowed(
                self.create_user(
                    email="other@example.com"
                )
            )
        )

    def test_unauthenticated_user_is_not_allowed(
        self,
    ):
        self.assertFalse(
            self.service.is_allowed(
                self.create_user(
                    authenticated=False
                )
            )
        )

    def test_authorize_returns_new_authorized_user(
        self,
    ):
        original = self.create_user()

        authorized = self.service.authorize(
            original
        )

        self.assertFalse(
            original.authorized
        )

        self.assertTrue(
            authorized.authorized
        )

        self.assertIsNot(
            original,
            authorized,
        )

    def test_unauthenticated_user_is_rejected(
        self,
    ):
        with self.assertRaises(
            AuthenticationRequiredError
        ):
            self.service.require_allowed(
                self.create_user(
                    authenticated=False
                )
            )

    def test_unlisted_user_is_rejected(self):
        with self.assertRaises(
            AccessDeniedError
        ):
            self.service.require_allowed(
                self.create_user(
                    email="other@example.com"
                )
            )

    def test_allowed_user_is_returned(self):
        result = self.service.require_allowed(
            self.create_user()
        )

        self.assertTrue(
            result.authorized
        )

    def test_user_role_is_detected(self):
        self.assertTrue(
            self.service.has_role(
                self.create_user(),
                Role.USER,
            )
        )

    def test_required_role_is_accepted(self):
        result = self.service.require_role(
            self.create_user(
                roles=(
                    Role.USER,
                    Role.ADMIN,
                )
            ),
            Role.ADMIN,
        )

        self.assertTrue(
            result.authorized
        )

    def test_missing_role_is_rejected(self):
        with self.assertRaises(
            AccessDeniedError
        ):
            self.service.require_role(
                self.create_user(),
                Role.ADMIN,
            )

    def test_invalid_user_type_is_rejected(self):
        with self.assertRaises(
            TypeError
        ):
            self.service.is_allowed(
                object()
            )


if __name__ == "__main__":
    unittest.main()