from __future__ import annotations

import unittest

from src.matching.scorer import Scorer


class TestScorerV310(unittest.TestCase):

    def setUp(self) -> None:
        self.scorer = Scorer()

    def test_zero_skill_forces_zero_global_score(self):
        score = self.scorer.global_score(
            skill=0,
            location=100,
            remote=100,
            salary=100,
        )

        self.assertEqual(score, 0)

    def test_skill_match_allows_global_score(self):
        score = self.scorer.global_score(
            skill=50,
            location=100,
            remote=100,
            salary=100,
        )

        self.assertEqual(score, 75)

    def test_global_score_is_bounded_to_one_hundred(self):
        score = self.scorer.global_score(
            skill=200,
            location=200,
            remote=200,
            salary=200,
        )

        self.assertEqual(score, 100)

    def test_global_score_is_never_negative(self):
        score = self.scorer.global_score(
            skill=-10,
            location=-10,
            remote=-10,
            salary=-10,
        )

        self.assertEqual(score, 0)


if __name__ == "__main__":
    unittest.main()