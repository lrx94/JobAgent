from __future__ import annotations

import unittest

from src.auth.adapters.streamlit_bootstrap import (
    require_streamlit_user,
)


class StopExecution(Exception):
    pass


class FakeSidebar:

    def __init__(self):
        self.buttons = {}
        self.messages = []

    def divider(self):
        pass

    def caption(self, value):
        self.messages.append(
            ("caption", value)
        )

    def write(self, value):
        self.messages.append(
            ("write", value)
        )

    def button(
        self,
        label,
        **kwargs,
    ):
        return self.buttons.get(
            label,
            False,
        )


class FakeStreamlit:

    def __init__(
        self,
        user,
        allowed_emails,
    ):
        self.user = user

        self.secrets = {
            "access": {
                "allowed_emails": (
                    allowed_emails
                )
            }
        }

        self.sidebar = FakeSidebar()

        self.buttons = {}
        self.messages = []

        self.login_calls = 0
        self.logout_calls = 0
        self.stop_calls = 0

    def title(self, value):
        self.messages.append(
            ("title", value)
        )

    def info(self, value):
        self.messages.append(
            ("info", value)
        )

    def error(self, value):
        self.messages.append(
            ("error", value)
        )

    def caption(self, value):
        self.messages.append(
            ("caption", value)
        )

    def button(
        self,
        label,
        **kwargs,
    ):
        return self.buttons.get(
            label,
            False,
        )

    def login(self):
        self.login_calls += 1

    def logout(self):
        self.logout_calls += 1

    def stop(self):
        self.stop_calls += 1
        raise StopExecution()


class TestStreamlitBootstrap(
    unittest.TestCase
):

    def authenticated_user(
        self,
        email="ludovic@example.com",
    ):
        return {
            "is_logged_in": True,
            "sub": "subject-123",
            "email": email,
            "email_verified": True,
            "name": "Ludovic",
            "iss": (
                "https://accounts.google.com"
            ),
        }

    def test_anonymous_user_is_stopped(self):
        streamlit = FakeStreamlit(
            user={
                "is_logged_in": False,
            },
            allowed_emails=[
                "ludovic@example.com",
            ],
        )

        with self.assertRaises(
            StopExecution
        ):
            require_streamlit_user(
                streamlit_module=streamlit
            )

        self.assertEqual(
            streamlit.stop_calls,
            1,
        )

    def test_login_button_starts_login(self):
        streamlit = FakeStreamlit(
            user={
                "is_logged_in": False,
            },
            allowed_emails=[
                "ludovic@example.com",
            ],
        )

        streamlit.buttons[
            "Se connecter avec Google"
        ] = True

        with self.assertRaises(
            StopExecution
        ):
            require_streamlit_user(
                streamlit_module=streamlit
            )

        self.assertEqual(
            streamlit.login_calls,
            1,
        )

    def test_allowed_user_gets_context(self):
        streamlit = FakeStreamlit(
            user=self.authenticated_user(),
            allowed_emails=[
                "ludovic@example.com",
            ],
        )

        context = require_streamlit_user(
            streamlit_module=streamlit,
            display_account_panel=False,
        )

        self.assertEqual(
            context.email,
            "ludovic@example.com",
        )

        self.assertTrue(
            context.authorized
        )

    def test_unlisted_user_is_stopped(self):
        streamlit = FakeStreamlit(
            user=self.authenticated_user(
                email="other@example.com"
            ),
            allowed_emails=[
                "ludovic@example.com",
            ],
        )

        with self.assertRaises(
            StopExecution
        ):
            require_streamlit_user(
                streamlit_module=streamlit
            )

        self.assertEqual(
            streamlit.stop_calls,
            1,
        )

    def test_denied_user_can_logout(self):
        streamlit = FakeStreamlit(
            user=self.authenticated_user(
                email="other@example.com"
            ),
            allowed_emails=[
                "ludovic@example.com",
            ],
        )

        streamlit.buttons[
            "Se déconnecter"
        ] = True

        with self.assertRaises(
            StopExecution
        ):
            require_streamlit_user(
                streamlit_module=streamlit
            )

        self.assertEqual(
            streamlit.logout_calls,
            1,
        )

    def test_account_panel_is_displayed(self):
        streamlit = FakeStreamlit(
            user=self.authenticated_user(),
            allowed_emails=[
                "ludovic@example.com",
            ],
        )

        require_streamlit_user(
            streamlit_module=streamlit,
            display_account_panel=True,
        )

        values = [
            value
            for _, value
            in streamlit.sidebar.messages
        ]

        self.assertIn(
            "ludovic@example.com",
            values,
        )


if __name__ == "__main__":
    unittest.main()