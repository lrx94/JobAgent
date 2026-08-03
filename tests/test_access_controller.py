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
from src.auth.services.access_controller import (
    AccessController,
)
from src.auth.services.authorization_service import (
    AuthorizationService,
)
from src.auth.user_context import (
    UserContext,
)


class TestAccessController(
    unittest.TestCase
):

    def setUp(self) -> None:
        repository = AllowListRepository(
            emails=[
                "ludovic@example.com",
            ]
        )

        service = AuthorizationService(
            repository=repository
        )

        self.controller = AccessController(
            authorization_service=service
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

    def test_create_context_calculates_authorization(
        self,
    ):
        context = self.controller.create_context(
            self.create_user()
        )

        self.assertIsInstance(
            context,
            UserContext,
        )

        self.assertTrue(
            context.authorized
        )

    def test_create_context_can_represent_denied_user(
        self,
    ):
        context = self.controller.create_context(
            self.create_user(
                email="other@example.com"
            )
        )

        self.assertFalse(
            context.authorized
        )

    def test_require_access_returns_context(self):
        context = self.controller.require_access(
            self.create_user()
        )

        self.assertTrue(
            context.can_access_application
        )

        self.assertEqual(
            context.user_id,
            "user-123",
        )

    def test_require_access_rejects_anonymous_user(
        self,
    ):
        with self.assertRaises(
            AuthenticationRequiredError
        ):
            self.controller.require_access(
                self.create_user(
                    authenticated=False
                )
            )

    def test_require_access_rejects_unlisted_user(
        self,
    ):
        with self.assertRaises(
            AccessDeniedError
        ):
            self.controller.require_access(
                self.create_user(
                    email="other@example.com"
                )
            )

    def test_require_role_returns_context(self):
        context = self.controller.require_role(
            self.create_user(
                roles=(
                    Role.USER,
                    Role.ADMIN,
                )
            ),
            Role.ADMIN,
        )

        self.assertTrue(
            context.has_role(
                Role.ADMIN
            )
        )

    def test_require_role_rejects_missing_role(
        self,
    ):
        with self.assertRaises(
            AccessDeniedError
        ):
            self.controller.require_role(
                self.create_user(),
                Role.ADMIN,
            )


if __name__ == "__main__":
    unittest.main()