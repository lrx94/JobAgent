from __future__ import annotations

import unittest

from src.learning.origin import (
    LearningObservationOrigin,
)


class TestLearningObservationOrigin(
    unittest.TestCase
):

    def test_origin_is_string_enum(
        self,
    ) -> None:
        self.assertEqual(
            LearningObservationOrigin
            .JOB_ANALYZER
            .value,
            "job_analyzer",
        )

        self.assertIsInstance(
            LearningObservationOrigin
            .JOB_ANALYZER,
            str,
        )

    def test_unknown_origin_exists(
        self,
    ) -> None:
        self.assertEqual(
            LearningObservationOrigin
            .UNKNOWN
            .value,
            "unknown",
        )


if __name__ == "__main__":
    unittest.main()