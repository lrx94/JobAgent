from __future__ import annotations

import unittest

from src.career import (
    ProviderAdvisor,
)


class TestProviderAdvisor(
    unittest.TestCase
):

    def setUp(self) -> None:
        self.advisor = (
            ProviderAdvisor()
        )

    def test_remoteok_is_available(self):
        statuses = self.advisor.evaluate(
            recommended_providers=[
                "RemoteOK",
                "APEC",
            ],
            available_provider_names=[
                "RemoteOK",
            ],
        )

        by_id = {
            status.provider_id: status
            for status in statuses
        }

        self.assertTrue(
            by_id["remoteok"]
            .operational
        )

        self.assertEqual(
            by_id["apec"].status,
            "not_implemented",
        )

    def test_provider_names_are_normalized(self):
        self.assertEqual(
            self.advisor
            .canonical_provider_id(
                "RemoteOKProvider"
            ),
            "remoteok",
        )

        self.assertEqual(
            self.advisor
            .canonical_provider_id(
                "France Travail"
            ),
            "francetravail",
        )

    def test_recommended_providers_are_first(self):
        statuses = self.advisor.evaluate(
            recommended_providers=[
                "APEC",
            ],
            available_provider_names=[
                "RemoteOK",
            ],
        )

        self.assertEqual(
            statuses[0].provider_id,
            "apec",
        )

        self.assertTrue(
            statuses[0].recommended
        )

    def test_available_unrecommended_provider_is_included(
        self,
    ):
        statuses = self.advisor.evaluate(
            recommended_providers=[
                "APEC",
            ],
            available_provider_names=[
                "RemoteOK",
            ],
        )

        provider_ids = {
            status.provider_id
            for status in statuses
        }

        self.assertIn(
            "remoteok",
            provider_ids,
        )


if __name__ == "__main__":
    unittest.main()