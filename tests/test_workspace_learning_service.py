from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from src.domain import Job
from src.learning import (
    AssistedLearningService,
    LearningSuggestionDetector,
    LearningSuggestionRepository,
    SuggestionStatus,
)
from src.workspace.learning_service import (
    WorkspaceLearningError,
    WorkspaceLearningService,
    WorkspaceLearningSummary,
)


class TestWorkspaceLearningSummary(
    unittest.TestCase
):

    def test_empty_summary(
        self,
    ) -> None:
        summary = (
            WorkspaceLearningSummary
            .from_suggestions(())
        )

        self.assertEqual(
            summary.total,
            0,
        )

        self.assertEqual(
            summary.candidate,
            0,
        )

        self.assertEqual(
            summary.accepted,
            0,
        )

        self.assertEqual(
            summary.rejected,
            0,
        )

        self.assertEqual(
            summary.ignored,
            0,
        )


class TestWorkspaceLearningService(
    unittest.TestCase
):

    def setUp(self) -> None:
        self.temporary_directory = (
            tempfile.TemporaryDirectory()
        )

        detector = (
            LearningSuggestionDetector(
                known_terms=(
                    "Azure",
                    "ITIL",
                ),
                minimum_occurrences=2,
            )
        )

        repository = (
            LearningSuggestionRepository(
                Path(
                    self.temporary_directory.name
                )
                / "suggestions.json"
            )
        )

        learning_service = (
            AssistedLearningService(
                detector=detector,
                repository=repository,
            )
        )

        self.service = (
            WorkspaceLearningService(
                user_id="user-123",
                learning_service=(
                    learning_service
                ),
            )
        )

    def tearDown(self) -> None:
        self.temporary_directory.cleanup()

    @staticmethod
    def create_job(
        external_id: str,
    ) -> Job:
        return Job(
            title="Data Engineer",
            company="Example",
            location="Remote",
            description=(
                "Microsoft Fabric requis."
            ),
            source="France Travail",
            external_id=external_id,
            skills=[
                "Microsoft Fabric",
            ],
        )

    def test_exposes_user_id(
        self,
    ) -> None:
        self.assertEqual(
            self.service.user_id,
            "user-123",
        )

    def test_analyzes_jobs(
        self,
    ) -> None:
        result = self.service.analyze_jobs(
            [
                self.create_job("ft-1"),
                self.create_job("ft-2"),
            ]
        )

        detected_terms = {
            item.normalized_term
            for item in result.detected
        }

        self.assertIn(
            "microsoft fabric",
            detected_terms,
        )

        self.assertGreaterEqual(
            result.summary.total,
            1,
        )

        self.assertGreaterEqual(
            result.summary.candidate,
            1,
        )

    def test_duplicate_job_object_is_analyzed_once(
        self,
    ) -> None:
        job = self.create_job(
            "ft-1"
        )

        result = self.service.analyze_jobs(
            [
                job,
                job,
            ]
        )

        self.assertEqual(
            result.detected,
            (),
        )

    def test_accepts_suggestion(
        self,
    ) -> None:
        result = self.service.analyze_jobs(
            [
                self.create_job("ft-1"),
                self.create_job("ft-2"),
            ]
        )

        suggestion = next(
            item
            for item in result.detected
            if item.normalized_term
            == "microsoft fabric"
        )

        accepted = self.service.accept(
            suggestion.suggestion_id
        )

        self.assertEqual(
            accepted.status,
            SuggestionStatus.ACCEPTED,
        )

    def test_rejects_suggestion(
        self,
    ) -> None:
        result = self.service.analyze_jobs(
            [
                self.create_job("ft-1"),
                self.create_job("ft-2"),
            ]
        )

        suggestion = next(
            item
            for item in result.detected
            if item.normalized_term
            == "microsoft fabric"
        )

        rejected = self.service.reject(
            suggestion.suggestion_id
        )

        self.assertEqual(
            rejected.status,
            SuggestionStatus.REJECTED,
        )

    def test_filters_suggestions(
        self,
    ) -> None:
        result = self.service.analyze_jobs(
            [
                self.create_job("ft-1"),
                self.create_job("ft-2"),
            ]
        )

        suggestion = next(
            item
            for item in result.detected
            if item.normalized_term
            == "microsoft fabric"
        )

        self.service.ignore(
            suggestion.suggestion_id
        )

        ignored = (
            self.service
            .list_suggestions(
                status=(
                    SuggestionStatus.IGNORED
                )
            )
        )

        self.assertEqual(
            len(ignored),
            1,
        )

    def test_empty_suggestion_id_is_rejected(
        self,
    ) -> None:
        with self.assertRaises(
            WorkspaceLearningError
        ):
            self.service.accept("")

    def test_invalid_job_is_rejected(
        self,
    ) -> None:
        with self.assertRaises(TypeError):
            self.service.analyze_jobs(
                [object()]
            )

    def test_empty_user_id_is_rejected(
        self,
    ) -> None:
        repository = (
            LearningSuggestionRepository(
                Path(
                    self.temporary_directory.name
                )
                / "other.json"
            )
        )

        learning_service = (
            AssistedLearningService(
                detector=(
                    LearningSuggestionDetector()
                ),
                repository=repository,
            )
        )

        with self.assertRaises(ValueError):
            WorkspaceLearningService(
                user_id="",
                learning_service=(
                    learning_service
                ),
            )
def test_accept_updates_listed_suggestion_status(
            self,
        ) -> None:
            suggestions = self.service.analyze_jobs(
                self.jobs
            ).stored

            candidate = next(
                item
                for item in suggestions
                if item.status
                == SuggestionStatus.CANDIDATE
            )

            self.service.accept(
                candidate.suggestion_id
            )

            reloaded = self.service.list_suggestions()

            updated = next(
                item
                for item in reloaded
                if item.suggestion_id
                == candidate.suggestion_id
            )

            self.assertEqual(
                updated.status,
                SuggestionStatus.ACCEPTED,
            )

if __name__ == "__main__":
    unittest.main()