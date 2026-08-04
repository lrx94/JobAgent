from __future__ import annotations

import unittest
from unittest.mock import MagicMock, patch

from src.domain import Job
from src.ui.ai_debug import (
    get_structured_details,
    render_ai_debug,
)


class FakeContext:
    def __enter__(self):
        return self

    def __exit__(
        self,
        exception_type,
        exception,
        traceback,
    ):
        return False


class TestAIDebug(
    unittest.TestCase
):

    @staticmethod
    def create_job(
        *,
        structured: bool = True,
    ) -> Job:
        match_details = {}

        if structured:
            match_details["structured"] = {
                "version": "3.16.4",
                "legacy_score": 72.0,
                "global_score": 84.0,
                "dimensions": [
                    {
                        "name": "hard_skills",
                        "score": 66.7,
                        "weight": 0.4,
                        "matched": [
                            "Azure",
                            "ITIL",
                        ],
                        "missing": [
                            "COBIT",
                        ],
                        "explanation": (
                            "2 exigences sur 3 "
                            "satisfaites."
                        ),
                    },
                    {
                        "name": "experience",
                        "score": 100.0,
                        "weight": 0.2,
                        "matched": [
                            "20 ans d'expérience",
                        ],
                        "missing": [],
                        "explanation": (
                            "20 ans détectés pour "
                            "10 ans requis."
                        ),
                    },
                ],
                "strengths": [
                    "Azure",
                    "ITIL",
                    "Leadership",
                ],
                "gaps": [
                    "COBIT",
                    "Communication",
                ],
                "warnings": [],
            }

        return Job(
            title="DSI Senior",
            company="Example",
            location="Paris",
            description="Description",
            source="France Travail",
            score=72.0,
            match_details=match_details,
        )

    def test_returns_none_without_structured_details(
        self,
    ):
        job = self.create_job(
            structured=False
        )

        self.assertIsNone(
            get_structured_details(job)
        )

    def test_returns_structured_details(
        self,
    ):
        job = self.create_job()

        details = get_structured_details(
            job
        )

        self.assertIsNotNone(details)

        self.assertEqual(
            details["global_score"],
            84.0,
        )

    @patch(
        "src.ui.ai_debug.st"
    )
    def test_does_not_render_without_details(
        self,
        streamlit_mock,
    ):
        job = self.create_job(
            structured=False
        )

        displayed = render_ai_debug(
            job
        )

        self.assertFalse(displayed)

        streamlit_mock.expander.assert_not_called()

    @patch(
        "src.ui.ai_debug.st"
    )
    def test_renders_structured_panel(
        self,
        streamlit_mock,
    ):
        streamlit_mock.expander.return_value = (
            FakeContext()
        )

        streamlit_mock.columns.return_value = (
            MagicMock(),
            MagicMock(),
            MagicMock(),
        )

        displayed = render_ai_debug(
            self.create_job()
        )

        self.assertTrue(displayed)

        streamlit_mock.expander.assert_called()

        streamlit_mock.dataframe.assert_called_once()

        streamlit_mock.caption.assert_called()

    @patch(
        "src.ui.ai_debug.st"
    )
    def test_empty_dimensions_are_supported(
        self,
        streamlit_mock,
    ):
        streamlit_mock.expander.return_value = (
            FakeContext()
        )

        streamlit_mock.columns.return_value = (
            MagicMock(),
            MagicMock(),
            MagicMock(),
        )

        job = self.create_job()

        job.match_details[
            "structured"
        ]["dimensions"] = []

        displayed = render_ai_debug(
            job
        )

        self.assertTrue(displayed)

        streamlit_mock.info.assert_called_with(
            "Aucun sous-score disponible."
        )

    @patch(
        "src.ui.ai_debug.st"
    )
    def test_strengths_and_gaps_are_rendered(
        self,
        streamlit_mock,
    ):
        streamlit_mock.expander.return_value = (
            FakeContext()
        )

        streamlit_mock.columns.return_value = (
            MagicMock(),
            MagicMock(),
            MagicMock(),
        )

        render_ai_debug(
            self.create_job()
        )

        rendered_values = [
            call.args[0]
            for call
            in streamlit_mock.write.call_args_list
            if call.args
        ]

        self.assertIn(
            "- Azure",
            rendered_values,
        )

        self.assertIn(
            "- COBIT",
            rendered_values,
        )

    def test_invalid_job_is_rejected(
        self,
    ):
        with self.assertRaises(TypeError):
            get_structured_details(
                object()
            )


if __name__ == "__main__":
    unittest.main()