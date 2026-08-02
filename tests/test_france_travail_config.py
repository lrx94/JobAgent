from __future__ import annotations

import os
import unittest
from unittest.mock import patch

from src.providers.france_travail_config import (
    FranceTravailConfig,
)


class TestFranceTravailConfig(
    unittest.TestCase
):

    def test_empty_environment_is_not_configured(
        self,
    ):
        with patch.dict(
            os.environ,
            {},
            clear=True,
        ):
            config = (
                FranceTravailConfig
                .from_environment()
            )

        self.assertFalse(
            config.configured
        )

    def test_credentials_enable_configuration(
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
            config = (
                FranceTravailConfig
                .from_environment()
            )

        self.assertTrue(
            config.configured
        )

    def test_missing_credentials_are_rejected(
        self,
    ):
        config = FranceTravailConfig()

        with self.assertRaises(
            RuntimeError
        ):
            config.require_credentials()


if __name__ == "__main__":
    unittest.main()