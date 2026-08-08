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
from src.career.search_workflow import CareerSearchResult


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

    PROFILE_ID = "data-profile"

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
            ],
            profile_id=self.PROFILE_ID,
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
            ],
            profile_id=self.PROFILE_ID,
        )

        self.assertEqual(
            result.detected,
            (),
        )

    def test_search_result_uses_only_career_relevant_jobs(self):
        relevant_one = self.create_job("relevant-1")
        relevant_two = self.create_job("relevant-2")
        irrelevant_jobs = [
            Job(
                title="Directeur SI",
                company="Noise",
                location="Paris",
                description="Définir la stratégie des SI.",
                source="France Travail",
                external_id=f"noise-{index}",
                skills=["Stratégie SI"],
            )
            for index in range(3)
        ]
        result = self.service.analyze_search_result(
            CareerSearchResult(
                jobs=[relevant_one, relevant_two],
                all_jobs=[relevant_one, relevant_two, *irrelevant_jobs],
            ),
            profile_id=self.PROFILE_ID,
        )

        terms = {item.normalized_term for item in result.detected}
        self.assertIn("microsoft fabric", terms)
        self.assertNotIn("strategie si", terms)

    def test_two_profiles_have_distinct_learning_populations(self):
        dsi_jobs = [
            Job(
                title="DSI",
                company="Example",
                location="Paris",
                description="Microsoft Fabric requis.",
                source="France Travail",
                external_id=f"dsi-{index}",
                skills=["Microsoft Fabric"],
            )
            for index in range(2)
        ]
        daf_jobs = [
            Job(
                title="DAF",
                company="Example",
                location="Paris",
                description="Pilotage financier requis.",
                source="France Travail",
                external_id=f"daf-{index}",
                skills=["Pilotage financier"],
            )
            for index in range(2)
        ]

        self.service.analyze_jobs(dsi_jobs, profile_id="dsi")
        self.service.analyze_jobs(daf_jobs, profile_id="daf")

        dsi_terms = {
            item.normalized_term
            for item in self.service.list_suggestions(profile_id="dsi")
        }
        daf_terms = {
            item.normalized_term
            for item in self.service.list_suggestions(profile_id="daf")
        }
        self.assertIn("microsoft fabric", dsi_terms)
        self.assertNotIn("microsoft fabric", daf_terms)
        self.assertIn("pilotage financier", daf_terms)
        self.assertNotIn("pilotage financier", dsi_terms)

    def test_two_users_use_distinct_learning_repositories(self):
        other_repository = LearningSuggestionRepository(
            Path(self.temporary_directory.name)
            / "other-user"
            / "suggestions.json"
        )
        other_service = WorkspaceLearningService(
            user_id="user-456",
            learning_service=AssistedLearningService(
                detector=LearningSuggestionDetector(
                    minimum_occurrences=2
                ),
                repository=other_repository,
            ),
        )
        jobs = [
            self.create_job("other-1"),
            self.create_job("other-2"),
        ]
        other_service.analyze_jobs(jobs, profile_id="dsi")

        self.assertEqual(
            self.service.list_suggestions(profile_id="dsi"),
            (),
        )
        self.assertTrue(
            other_service.list_suggestions(profile_id="dsi")
        )

    def test_accepts_suggestion(
        self,
    ) -> None:
        result = self.service.analyze_jobs(
            [
                self.create_job("ft-1"),
                self.create_job("ft-2"),
            ],
            profile_id=self.PROFILE_ID,
        )

        suggestion = next(
            item
            for item in result.detected
            if item.normalized_term
            == "microsoft fabric"
        )

        accepted = self.service.accept(
            self.PROFILE_ID,
            suggestion.suggestion_id,
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
            ],
            profile_id=self.PROFILE_ID,
        )

        suggestion = next(
            item
            for item in result.detected
            if item.normalized_term
            == "microsoft fabric"
        )

        rejected = self.service.reject(
            self.PROFILE_ID,
            suggestion.suggestion_id,
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
            ],
            profile_id=self.PROFILE_ID,
        )

        suggestion = next(
            item
            for item in result.detected
            if item.normalized_term
            == "microsoft fabric"
        )

        self.service.ignore(
            self.PROFILE_ID,
            suggestion.suggestion_id,
        )

        ignored = (
            self.service
            .list_suggestions(
                profile_id=self.PROFILE_ID,
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
            self.service.accept(self.PROFILE_ID, "")

    def test_invalid_job_is_rejected(
        self,
    ) -> None:
        with self.assertRaises(TypeError):
            self.service.analyze_jobs(
                [object()],
                profile_id=self.PROFILE_ID,
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


if __name__ == "__main__":
    unittest.main()
