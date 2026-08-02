from __future__ import annotations

import json
import unittest

from src.providers.france_travail import (
    FranceTravailProvider,
)
from src.providers.france_travail_config import (
    FranceTravailConfig,
)
from src.search_request import SearchRequest


class FakeAuth:

    def access_token(self):
        return "token"

    def invalidate(self):
        pass


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


class CapturingOpener:

    def __init__(self, payload):
        self.payload = payload
        self.request = None

    def __call__(
        self,
        request,
        timeout,
    ):
        self.request = request

        return FakeResponse(
            self.payload
        )


class TestFranceTravailProvider(
    unittest.TestCase
):

    def create_provider(
        self,
        opener,
    ):
        return FranceTravailProvider(
            config=FranceTravailConfig(
                client_id="client",
                client_secret="secret",
            ),
            auth_client=FakeAuth(),
            opener=opener,
        )

    def test_search_returns_jobs(self):
        opener = CapturingOpener(
            {
                "resultats": [
                    {
                        "id": "A1",
                        "intitule": (
                            "Directeur de projet"
                        ),
                        "description": (
                            "Pilotage de programme"
                        ),
                        "entreprise": {
                            "nom": "Example",
                        },
                        "lieuTravail": {
                            "libelle": "Paris",
                        },
                    }
                ]
            }
        )

        provider = self.create_provider(
            opener
        )

        jobs = provider.search(
            SearchRequest(
                keywords=[
                    "Directeur de projet"
                ],
                locations=["Paris"],
                page_size=20,
            )
        )

        self.assertEqual(
            len(jobs),
            1,
        )

        self.assertEqual(
            jobs[0].source,
            "France Travail",
        )

    def test_request_uses_bearer_token(
        self,
    ):
        opener = CapturingOpener(
            {
                "resultats": [],
            }
        )

        provider = self.create_provider(
            opener
        )

        provider.search(
            SearchRequest(
                keywords=["DSI"],
            )
        )

        self.assertEqual(
            opener.request.get_header(
                "Authorization"
            ),
            "Bearer token",
        )

    def test_invalid_request_is_rejected(
        self,
    ):
        opener = CapturingOpener(
            {
                "resultats": [],
            }
        )

        provider = self.create_provider(
            opener
        )

        with self.assertRaises(
            TypeError
        ):
            provider.search(
                object()
            )


if __name__ == "__main__":
    unittest.main()