from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from src.analysis import (
    ScoreComparison,
    StructuredAnalysis,
    StructuredScore,
)
from src.auth.models import (
    CurrentUser,
    Role,
)
from src.auth.user_context import (
    UserContext,
)
from src.cvs.results import (
    CVAnalysisResult,
)
from src.domain import Job
from src.profile import Profile
from src.workspace.analysis_service import (
    WorkspaceAnalysisError,
)
from src.workspace.builder import (
    build_workspace,
)


PDF_CONTENT = (
    b"%PDF-1.4\n"
    b"Workspace analysis test\n"
    b"%%EOF\n"
)


class FakeCandidateAnalyzer:

    def __init__(self) -> None:
        self.calls = 0

    def analyze(
        self,
        *,
        cv_analysis,
    ) -> StructuredAnalysis:
        self.calls += 1

        return StructuredAnalysis(
            hard_skills=(
                "Azure",
                "ITIL",
            ),
            seniority="executive",
        )


class FakeComparativeScoringService:

    def __init__(self) -> None:
        self.calls = 0
        self.jobs: tuple[Job, ...] = ()

    def compare(
        self,
        *,
        candidate,
        jobs,
    ):
        self.calls += 1
        self.jobs = tuple(jobs)

        results = []

        for job in self.jobs:
            job.match_details[
                "structured"
            ] = {
                "legacy_score": job.score,
                "global_score": 88.0,
                "dimensions": [],
            }

            results.append(
                ScoreComparison(
                    job_identity=job.identity,
                    legacy_score=job.score,
                    structured_score=88.0,
                    difference=round(
                        88.0 - job.score,
                        1,
                    ),
                    structured_result=(
                        StructuredScore(
                            global_score=88.0,
                            dimensions=(),
                        )
                    ),
                )
            )

        return tuple(results)


class TestWorkspaceAnalysisService(
    unittest.TestCase
):

    def setUp(self) -> None:
        self.temporary_directory = (
            tempfile.TemporaryDirectory()
        )

        context = UserContext(
            current_user=CurrentUser(
                user_id="user-123",
                subject="subject-123",
                email="user@example.com",
                display_name="User",
                authenticated=True,
                authorized=True,
                roles=(Role.USER,),
            )
        )

        self.workspace = build_workspace(
            user_context=context,
            storage_root=Path(
                self.temporary_directory.name
            ),
        )

        self.profile = Profile(
            name="DSI / CIO",
            keywords=[
                "DSI",
                "CIO",
            ],
            locations=["Paris"],
            salary_min=0,
            remote=True,
        )

        onboarding = (
            self.workspace
            .onboarding_service
            .create_from_bytes(
                content=PDF_CONTENT,
                original_filename="cv.pdf",
                profile=self.profile,
                analyze=False,
            )
        )

        self.profile_id = (
            onboarding.profile_id
        )

        self.candidate_analyzer = (
            FakeCandidateAnalyzer()
        )

        self.comparison_service = (
            FakeComparativeScoringService()
        )

        self.service = (
            self.workspace.analysis_service
        )

        self.service.candidate_analyzer = (
            self.candidate_analyzer
        )

        self.service.comparative_scoring_service = (
            self.comparison_service
        )

    def tearDown(self) -> None:
        self.temporary_directory.cleanup()

    def test_builds_candidate_from_primary_cv(
        self,
    ):
        cv_analysis = CVAnalysisResult(
            text="DSI certifié ITIL.",
            skills=(
                "ITIL",
                "Azure",
            ),
        )

        with patch.object(
            self.workspace.cv_service,
            "analyze",
            return_value=cv_analysis,
        ) as analyze_mock:
            result = (
                self.service
                .build_candidate_analysis(
                    self.profile_id
                )
            )

        self.assertIsNotNone(result)

        self.assertEqual(
            result.profile_id,
            self.profile_id,
        )

        self.assertIn(
            "Azure",
            result.analysis.hard_skills,
        )

        self.assertEqual(
            self.candidate_analyzer.calls,
            1,
        )

        analyze_mock.assert_called_once()

    def test_absent_primary_cv_returns_none(
        self,
    ):
        result = (
            self.service
            .build_candidate_analysis(
                "profil-sans-cv"
            )
        )

        self.assertIsNone(result)

    def test_enriches_jobs_without_changing_score(
        self,
    ):
        job = Job(
            title="DSI",
            company="Example",
            location="Paris",
            description="Description",
            source="France Travail",
            score=72.0,
        )

        self.service.enrich_jobs(
            candidate=StructuredAnalysis(
                hard_skills=(
                    "ITIL",
                )
            ),
            jobs=[job],
        )

        self.assertEqual(
            job.score,
            72.0,
        )

        self.assertEqual(
            job.match_details[
                "structured"
            ]["global_score"],
            88.0,
        )

    def test_duplicate_job_object_is_analyzed_once(
        self,
    ):
        job = Job(
            title="DSI",
            company="Example",
            location="Paris",
            description="Description",
            source="France Travail",
        )

        self.service.enrich_jobs(
            candidate=StructuredAnalysis(),
            jobs=[
                job,
                job,
            ],
        )

        self.assertEqual(
            len(
                self.comparison_service.jobs
            ),
            1,
        )

    def test_empty_profile_id_is_rejected(
        self,
    ):
        with self.assertRaises(
            WorkspaceAnalysisError
        ):
            (
                self.service
                .build_candidate_analysis("")
            )

    def test_invalid_candidate_is_rejected(
        self,
    ):
        with self.assertRaises(TypeError):
            self.service.enrich_jobs(
                candidate=object(),
                jobs=[],
            )


if __name__ == "__main__":
    unittest.main()