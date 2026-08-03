from __future__ import annotations

import json
import unittest

from src.providers.france_travail_auth import (
    FranceTravailAuthClient,
)
from src.providers.france_travail_config import (
    FranceTravailConfig,
)


class FakeResponse:

    status = 200

    def __init__(self, payload):
        self.body = json.dumps(
            payload
        ).encode("utf-8")

    def read(self):
        return self.body

    def __enter__(self):
        return self

    def __exit__(
        self,
        exc_type,
        exc_value,
        traceback,
    ):
        return False


class CountingOpener:

    def __init__(self):
        self.calls = 0

    def __call__(
        self,
        request,
        timeout,
    ):
        self.calls += 1

        return FakeResponse(
            {
                "access_token": (
                    "token-test"
                ),
                "expires_in": 300,
            }
        )


class TestFranceTravailAuth(
    unittest.TestCase
):

    def create_config(self):
        return FranceTravailConfig(
            client_id="client",
            client_secret="secret",
        )

    def test_returns_access_token(self):
        opener = CountingOpener()

        client = FranceTravailAuthClient(
            config=self.create_config(),
            opener=opener,
        )

        self.assertEqual(
            client.access_token(),
            "token-test",
        )

    def test_token_is_cached(self):
        opener = CountingOpener()

        client = FranceTravailAuthClient(
            config=self.create_config(),
            opener=opener,
        )

        client.access_token()
        client.access_token()

        self.assertEqual(
            opener.calls,
            1,
        )

    def test_force_refresh_requests_new_token(
        self,
    ):
        opener = CountingOpener()

        client = FranceTravailAuthClient(
            config=self.create_config(),
            opener=opener,
        )

        client.access_token()
        client.access_token(
            force_refresh=True
        )

        self.assertEqual(
            opener.calls,
            2,
        )


if __name__ == "__main__":
    unittest.main()