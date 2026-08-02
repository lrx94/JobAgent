from __future__ import annotations

import unittest

from src.career import RoleDetector
from src.providers.provider_selector import (
    ProviderSelector,
)


class TestProviderSelector(unittest.TestCase):

    def setUp(self) -> None:
        self.selector = ProviderSelector()
        self.detector = RoleDetector()

    def create_cio_role(self):
        analysis = self.detector.analyze(
            cv_text=(
                "DSI Groupe, membre du COMEX, "
                "gouvernance et transformation SI."
            ),
            extracted_skills=[
                "gouvernance si",
                "transformation si",
                "cobit",
            ],
        )

        return next(
            suggestion
            for suggestion
            in analysis.role_suggestions
            if suggestion.role_id == "cio"
        )

    def create_data_role(self):
        analysis = self.detector.analyze(
            cv_text=(
                "Data Engineer Python SQL ETL."
            ),
            extracted_skills=[
                "python",
                "sql",
                "etl",
                "spark",
            ],
        )

        return next(
            suggestion
            for suggestion
            in analysis.role_suggestions
            if suggestion.role_id
            == "data_engineer"
        )

    def test_cio_uses_remoteok_as_fallback(self):
        result = self.selector.select(
            selected_role=self.create_cio_role(),
            available_provider_names=[
                "RemoteOK",
            ],
            remote_requested=True,
        )

        self.assertEqual(
            result.selected_provider_ids,
            ["remoteok"],
        )

        remoteok = next(
            item
            for item in result.items
            if item.provider_id == "remoteok"
        )

        self.assertTrue(remoteok.fallback)
        self.assertFalse(remoteok.recommended)

        self.assertIn(
            "apec",
            result.missing_recommended_provider_ids,
        )

        self.assertIn(
            "francetravail",
            result.missing_recommended_provider_ids,
        )

    def test_data_profile_selects_recommended_remoteok(
        self,
    ):
        result = self.selector.select(
            selected_role=self.create_data_role(),
            available_provider_names=[
                "RemoteOKProvider",
            ],
            remote_requested=True,
        )

        remoteok = next(
            item
            for item in result.items
            if item.provider_id == "remoteok"
        )

        self.assertTrue(remoteok.selected)
        self.assertTrue(remoteok.recommended)
        self.assertFalse(remoteok.fallback)
        self.assertTrue(remoteok.operational)

    def test_no_available_provider_produces_no_selection(
        self,
    ):
        result = self.selector.select(
            selected_role=self.create_cio_role(),
            available_provider_names=[],
        )

        self.assertEqual(
            result.selected_provider_ids,
            [],
        )

        self.assertFalse(
            result.has_operational_selection
        )

    def test_provider_names_are_normalized(self):
        self.assertEqual(
            self.selector.canonical_provider_id(
                "France Travail"
            ),
            "francetravail",
        )

        self.assertEqual(
            self.selector.canonical_provider_id(
                "WelcomeToTheJungle"
            ),
            "welcometothejungle",
        )

    def test_selection_is_explainable(self):
        result = self.selector.select(
            selected_role=self.create_data_role(),
            available_provider_names=[
                "RemoteOK",
            ],
            remote_requested=True,
        )

        remoteok = next(
            item
            for item in result.items
            if item.provider_id == "remoteok"
        )

        self.assertTrue(remoteok.reasons)
        self.assertGreater(
            remoteok.score,
            0,
        )

    def test_result_can_be_converted_to_dict(self):
        result = self.selector.select(
            selected_role=self.create_cio_role(),
            available_provider_names=[
                "RemoteOK",
            ],
        )

        data = result.to_dict()

        self.assertIn(
            "selected_provider_ids",
            data,
        )

        self.assertIn(
            "providers",
            data,
        )


if __name__ == "__main__":
    unittest.main()