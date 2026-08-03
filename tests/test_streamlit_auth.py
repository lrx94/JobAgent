from __future__ import annotations

import unittest

from src.auth.exceptions import (
    AuthenticationConfigurationError,
    IdentityClaimsError,
)
from src.auth.models import (
    Role,
)
from src.auth.adapters.streamlit_auth import (
    StreamlitAuthAdapter,
)


class FakeStreamlit:

    def __init__(
        self,
        user=None,
        secrets=None,
    ):
        self.user = (
            user
            if user is not None
            else {
                "is_logged_in": False,
            }
        )

        self.secrets = (
            secrets
            if secrets is not None
            else {}
        )

        self.login_calls = 0
        self.logout_calls = 0

    def login(self):
        self.login_calls += 1

    def logout(self):
        self.logout_calls += 1


class TestStreamlitAuthAdapter(
    unittest.TestCase
):

    def authenticated_claims(
        self,
        **overrides,
    ):
        values = {
            "is_logged_in": True,
            "sub": "google-subject-123",
            "email": "Ludovic@Example.com",
            "email_verified": True,
            "name": "Ludovic",
            "iss": (
                "https://accounts.google.com"
            ),
        }

        values.update(overrides)

        return values

    def test_anonymous_session_returns_none(self):
        streamlit = FakeStreamlit()

        adapter = StreamlitAuthAdapter(
            streamlit_module=streamlit
        )

        self.assertFalse(
            adapter.is_logged_in()
        )

        self.assertIsNone(
            adapter.current_user()
        )

    def test_claims_are_converted_to_user(self):
        streamlit = FakeStreamlit(
            user=self.authenticated_claims()
        )

        adapter = StreamlitAuthAdapter(
            streamlit_module=streamlit
        )

        user = adapter.current_user()

        self.assertIsNotNone(user)

        self.assertEqual(
            user.subject,
            "google-subject-123",
        )

        self.assertEqual(
            user.email,
            "ludovic@example.com",
        )

        self.assertEqual(
            user.display_name,
            "Ludovic",
        )

        self.assertTrue(
            user.authenticated
        )

        self.assertFalse(
            user.authorized
        )

        self.assertEqual(
            user.roles,
            (
                Role.USER,
            ),
        )

    def test_user_id_is_stable(self):
        first = (
            StreamlitAuthAdapter
            .build_user_id(
                issuer="google",
                subject="subject-1",
            )
        )

        second = (
            StreamlitAuthAdapter
            .build_user_id(
                issuer="google",
                subject="subject-1",
            )
        )

        self.assertEqual(
            first,
            second,
        )

    def test_different_subjects_get_different_ids(
        self,
    ):
        first = (
            StreamlitAuthAdapter
            .build_user_id(
                issuer="google",
                subject="subject-1",
            )
        )

        second = (
            StreamlitAuthAdapter
            .build_user_id(
                issuer="google",
                subject="subject-2",
            )
        )

        self.assertNotEqual(
            first,
            second,
        )

    def test_missing_subject_is_rejected(self):
        streamlit = FakeStreamlit(
            user=self.authenticated_claims(
                sub=""
            )
        )

        adapter = StreamlitAuthAdapter(
            streamlit_module=streamlit
        )

        with self.assertRaises(
            IdentityClaimsError
        ):
            adapter.current_user()

    def test_missing_email_is_rejected(self):
        streamlit = FakeStreamlit(
            user=self.authenticated_claims(
                email=""
            )
        )

        adapter = StreamlitAuthAdapter(
            streamlit_module=streamlit
        )

        with self.assertRaises(
            IdentityClaimsError
        ):
            adapter.current_user()

    def test_unverified_email_is_rejected(self):
        streamlit = FakeStreamlit(
            user=self.authenticated_claims(
                email_verified=False
            )
        )

        adapter = StreamlitAuthAdapter(
            streamlit_module=streamlit
        )

        with self.assertRaises(
            IdentityClaimsError
        ):
            adapter.current_user()

    def test_login_calls_streamlit(self):
        streamlit = FakeStreamlit()

        adapter = StreamlitAuthAdapter(
            streamlit_module=streamlit
        )

        adapter.login()

        self.assertEqual(
            streamlit.login_calls,
            1,
        )

    def test_logout_calls_streamlit(self):
        streamlit = FakeStreamlit()

        adapter = StreamlitAuthAdapter(
            streamlit_module=streamlit
        )

        adapter.logout()

        self.assertEqual(
            streamlit.logout_calls,
            1,
        )

    def test_allowed_emails_are_loaded(self):
        streamlit = FakeStreamlit(
            secrets={
                "access": {
                    "allowed_emails": [
                        "ludovic@example.com",
                    ]
                }
            }
        )

        adapter = StreamlitAuthAdapter(
            streamlit_module=streamlit
        )

        self.assertEqual(
            adapter.allowed_emails(),
            [
                "ludovic@example.com",
            ],
        )

    def test_missing_access_section_is_rejected(
        self,
    ):
        adapter = StreamlitAuthAdapter(
            streamlit_module=(
                FakeStreamlit(
                    secrets={}
                )
            )
        )

        with self.assertRaises(
            AuthenticationConfigurationError
        ):
            adapter.allowed_emails()


if __name__ == "__main__":
    unittest.main()