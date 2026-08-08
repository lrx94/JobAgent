from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from src.learning import (
    LearningSuggestion,
    LearningSuggestionRepository,
    SuggestionStatus,
    SuggestionType,
)


class TestLearningSuggestionRepository(
    unittest.TestCase
):

    def setUp(self) -> None:
        self.temporary_directory = (
            tempfile.TemporaryDirectory()
        )

        self.repository = (
            LearningSuggestionRepository(
                Path(
                    self.temporary_directory.name
                )
                / "suggestions.json"
            )
        )

    def tearDown(self) -> None:
        self.temporary_directory.cleanup()

    @staticmethod
    def suggestion(
        *,
        occurrence_count: int = 5,
        profile_id: str | None = None,
        status: SuggestionStatus = SuggestionStatus.CANDIDATE,
    ) -> LearningSuggestion:
        return LearningSuggestion(
            suggestion_id="skill-fabric",
            observed_term="Microsoft Fabric",
            normalized_term="microsoft fabric",
            suggestion_type=(
                SuggestionType.SKILL
            ),
            occurrence_count=(
                occurrence_count
            ),
            source_count=2,
            sources=(
                "france travail",
                "remoteok",
            ),
            contexts=(
                "Microsoft Fabric requis.",
            ),
            confidence=0.8,
            profile_id=profile_id,
            status=status,
        )

    def test_saves_and_loads_suggestion(
        self,
    ):
        self.repository.save_many(
            [self.suggestion()]
        )

        result = (
            self.repository.list_all()
        )

        self.assertEqual(
            len(result),
            1,
        )

        self.assertEqual(
            result[0].observed_term,
            "Microsoft Fabric",
        )

    def test_status_is_persisted(
        self,
    ):
        self.repository.save_many(
            [self.suggestion()]
        )

        self.repository.change_status(
            suggestion_id="skill-fabric",
            status=(
                SuggestionStatus.ACCEPTED
            ),
        )

        result = self.repository.get(
            "skill-fabric"
        )

        self.assertEqual(
            result.status,
            SuggestionStatus.ACCEPTED,
        )

    def test_human_status_survives_refresh(
        self,
    ):
        self.repository.save_many(
            [self.suggestion()]
        )

        self.repository.change_status(
            suggestion_id="skill-fabric",
            status=(
                SuggestionStatus.REJECTED
            ),
        )

        self.repository.save_many(
            [
                self.suggestion(
                    occurrence_count=12
                )
            ]
        )

        result = self.repository.get(
            "skill-fabric"
        )

        self.assertEqual(
            result.status,
            SuggestionStatus.REJECTED,
        )

        self.assertEqual(
            result.occurrence_count,
            12,
        )

    def test_unknown_suggestion_is_rejected(
        self,
    ):
        with self.assertRaises(KeyError):
            self.repository.change_status(
                suggestion_id="unknown",
                status=(
                    SuggestionStatus.ACCEPTED
                ),
            )

    def test_repository_filters_and_updates_by_profile(self):
        self.repository.save_many(
            [
                self.suggestion(profile_id="dsi"),
                self.suggestion(profile_id="daf"),
            ]
        )

        self.repository.change_status(
            suggestion_id="skill-fabric",
            profile_id="dsi",
            status=SuggestionStatus.ACCEPTED,
        )

        self.assertEqual(
            self.repository.get(
                "skill-fabric", profile_id="dsi"
            ).status,
            SuggestionStatus.ACCEPTED,
        )
        self.assertEqual(
            self.repository.get(
                "skill-fabric", profile_id="daf"
            ).status,
            SuggestionStatus.CANDIDATE,
        )

    def test_legacy_human_decision_is_preserved_when_scoped(self):
        self.repository.save_many(
            [self.suggestion(status=SuggestionStatus.REJECTED)]
        )
        self.repository.save_many(
            [self.suggestion(profile_id="dsi")]
        )

        scoped = self.repository.get(
            "skill-fabric",
            profile_id="dsi",
        )
        self.assertEqual(scoped.status, SuggestionStatus.REJECTED)
        self.assertIsNone(
            self.repository.get("skill-fabric").profile_id
        )


if __name__ == "__main__":
    unittest.main()
