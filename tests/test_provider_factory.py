from __future__ import annotations

import os
import unittest
from unittest.mock import patch

from src.providers.provider_factory import (
    build_default_providers,
)


class TestProviderFactory(
    unittest.TestCase
):

    def test_remoteok_is_always_present(self):
        with patch.dict(
            os.environ,
            {},
            clear=True,
        ):
            providers = (
                build_default_providers()
            )

        names = [
            provider.name
            for provider in providers
        ]

        self.assertEqual(
            names,
            ["RemoteOK"],
        )

    def test_france_travail_is_added_when_configured(
        self,
    ):
        with patch.dict(
            os.environ,
            {
                "FRANCE_TRAVAIL_CLIENT_ID": (
                    "client"
                ),
                "FRANCE_TRAVAIL_CLIENT_SECRET": (
                    "secret"
                ),
            },
            clear=True,
        ):
            providers = (
                build_default_providers()
            )

        names = [
            provider.name
            for provider in providers
        ]

        self.assertEqual(
            names,
            [
                "RemoteOK",
                "France Travail",
            ],
        )


if __name__ == "__main__":
    unittest.main()