from __future__ import annotations

import unittest

from src.domain import Job
from src.market import (
    MarketAnalyzer,
)
from src.profile import Profile
from src.career.search_workflow import CareerSearchResult


class FakeSkillExtractor:
    """
    Extracteur déterministe destiné aux tests.

    Il simule le comportement du catalogue central
    sans dépendre de son contenu exact.
    """

    SKILLS = (
        "Python",
        "SQL",
        "Azure",
        "Spark",
        "Terraform",
        "Docker",
    )

    def extract(
        self,
        text: str,
    ) -> list[str]:
        normalized = str(
            text
            or ""
        ).casefold()

        return [
            skill
            for skill in self.SKILLS
            if skill.casefold()
            in normalized
        ]


class TestMarketAnalyzer(
    unittest.TestCase
):

    def test_explicit_cv_skills_override_profile_keywords(
        self,
    ):
        report = self.analyzer.analyze(
            profile=self.profile,
            jobs=self.create_jobs(),
            profile_skills=(
                "Terraform",
                "Docker",
            ),
            profile_skill_source="cv",
        )

        stats = {
            item.skill: item
            for item in report.skill_stats
        }

        self.assertTrue(
            stats["Terraform"]
            .present_in_profile
        )

        self.assertTrue(
            stats["Docker"]
            .present_in_profile
        )

        self.assertFalse(
            stats["Python"]
            .present_in_profile
        )

        self.assertEqual(
            report.profile_skill_source,
            "cv",
        )

    def test_default_behavior_keeps_keywords_fallback(
        self,
    ):
        report = self.analyzer.analyze(
            profile=self.profile,
            jobs=self.create_jobs(),
        )

        stats = {
            item.skill: item
            for item in report.skill_stats
        }

        self.assertTrue(
            stats["Python"]
            .present_in_profile
        )

        self.assertEqual(
            report.profile_skill_source,
            "keywords",
        )


    def setUp(self) -> None:
        self.profile = Profile(
            name="Data Engineer",
            keywords=[
                "Python",
                "SQL",
                "Azure",
            ],
            locations=["Paris"],
            salary_min=65000,
            remote=True,
        )

        self.analyzer = MarketAnalyzer(
            skill_extractor=(
                FakeSkillExtractor()
            ),
            top_skill_limit=20,
            top_pair_limit=20,
            minimum_pair_count=1,
        )

    @staticmethod
    def create_jobs() -> list[Job]:
        return [
            Job(
                title=(
                    "Data Engineer Python Azure"
                ),
                company="Example One",
                location="Paris",
                description=(
                    "Python SQL Azure Terraform"
                ),
                source="France Travail",
                external_id="ft-1",
            ),
            Job(
                title="Data Engineer Spark",
                company="Example Two",
                location="Remote",
                description=(
                    "Python SQL Spark Terraform"
                ),
                source="RemoteOK",
                external_id="remote-1",
                remote_type="remote",
            ),
            Job(
                title="Cloud Data Engineer",
                company="Example Three",
                location="Lyon",
                description=(
                    "Azure Docker Terraform"
                ),
                source="France Travail",
                external_id="ft-2",
            ),
        ]

    def test_analyze_counts_each_skill_once_per_job(
        self,
    ):
        jobs = self.create_jobs()

        jobs[0].description += (
            " Python Python Python"
        )

        report = self.analyzer.analyze(
            profile=self.profile,
            jobs=jobs,
        )

        stats = {
            item.skill: item
            for item in report.skill_stats
        }

        self.assertEqual(
            stats["Python"].job_count,
            2,
        )

        self.assertEqual(
            stats["Terraform"].job_count,
            3,
        )

    def test_missing_gap_exposes_job_context(self):
        report = self.analyzer.analyze(
            profile=self.profile,
            jobs=self.create_jobs()[:1],
        )
        terraform = next(
            item for item in report.missing_skill_stats
            if item.skill == "Terraform"
        )

        self.assertEqual(terraform.job_count, 1)
        self.assertEqual(len(terraform.evidence), 1)
        evidence = terraform.evidence[0]
        self.assertEqual(evidence.job_reference, "ft-1")
        self.assertEqual(evidence.job_title, "Data Engineer Python Azure")
        self.assertEqual(evidence.company, "Example One")
        self.assertEqual(evidence.source, "France Travail")
        self.assertIn("Terraform", evidence.context)

    def test_gap_evidence_is_limited_but_count_is_complete(self):
        analyzer = MarketAnalyzer(
            skill_extractor=FakeSkillExtractor(),
            maximum_evidence_per_skill=2,
            minimum_pair_count=1,
        )
        report = analyzer.analyze(
            profile=self.profile,
            jobs=self.create_jobs(),
        )
        terraform = next(
            item for item in report.missing_skill_stats
            if item.skill == "Terraform"
        )

        self.assertEqual(terraform.job_count, 3)
        self.assertEqual(len(terraform.evidence), 2)

    def test_provider_skill_without_text_has_safe_empty_context(self):
        job = Job(
            title="Data Engineer",
            company=None,
            location="Paris",
            description="Mission data.",
            source="RemoteOK",
            external_id="remote-tag",
            skills=["Docker"],
        )
        report = self.analyzer.analyze(profile=self.profile, jobs=[job])
        docker = next(
            item for item in report.missing_skill_stats
            if item.skill == "Docker"
        )
        self.assertEqual(docker.evidence[0].context, "")
        self.assertEqual(
            docker.evidence[0].company,
            "Entreprise inconnue",
        )

    def test_career_portrait_excludes_rejected_remoteok_job(self):
        relevant = self.create_jobs()[0]
        rejected = Job(
            title="Backend Engineer",
            company="Remote Company",
            location="Remote",
            description="Docker Kubernetes",
            source="RemoteOK",
            external_id="remote-rejected",
        )
        report = self.analyzer.analyze_career_result(
            profile=self.profile,
            search_result=CareerSearchResult(
                jobs=[relevant],
                all_jobs=[relevant, rejected],
            ),
        )

        self.assertEqual(report.total_jobs, 1)
        skills = {item.skill for item in report.skill_stats}
        self.assertIn("Terraform", skills)
        self.assertNotIn("Docker", skills)

    def test_analyze_calculates_percentages(
        self,
    ):
        report = self.analyzer.analyze(
            profile=self.profile,
            jobs=self.create_jobs(),
        )

        stats = {
            item.skill: item
            for item in report.skill_stats
        }

        self.assertEqual(
            stats["Terraform"].percentage,
            100.0,
        )

        self.assertEqual(
            stats["Python"].percentage,
            66.7,
        )

    def test_analyze_marks_profile_and_missing_skills(
        self,
    ):
        report = self.analyzer.analyze(
            profile=self.profile,
            jobs=self.create_jobs(),
        )

        stats = {
            item.skill: item
            for item in report.skill_stats
        }

        self.assertTrue(
            stats["Python"].present_in_profile
        )

        self.assertTrue(
            stats["Azure"].present_in_profile
        )

        self.assertFalse(
            stats["Terraform"].present_in_profile
        )

        missing = {
            item.skill
            for item
            in report.missing_skill_stats
        }

        self.assertIn(
            "Terraform",
            missing,
        )

        self.assertIn(
            "Docker",
            missing,
        )

    def test_analyze_builds_source_statistics(
        self,
    ):
        report = self.analyzer.analyze(
            profile=self.profile,
            jobs=self.create_jobs(),
        )

        sources = {
            item.source: item
            for item in report.source_stats
        }

        self.assertEqual(
            sources[
                "France Travail"
            ].job_count,
            2,
        )

        self.assertEqual(
            sources[
                "RemoteOK"
            ].job_count,
            1,
        )

        self.assertEqual(
            sources[
                "France Travail"
            ].coverage_percentage,
            100.0,
        )

    def test_analyze_builds_cooccurrences(
        self,
    ):
        report = self.analyzer.analyze(
            profile=self.profile,
            jobs=self.create_jobs(),
        )

        pairs = {
            frozenset(
                (
                    item.first_skill,
                    item.second_skill,
                )
            ): item
            for item in report.cooccurrences
        }

        key = frozenset(
            (
                "Python",
                "SQL",
            )
        )

        self.assertIn(
            key,
            pairs,
        )

        self.assertEqual(
            pairs[key].job_count,
            2,
        )

    def test_analyze_uses_provider_skills_as_text(
        self,
    ):
        job = Job(
            title="Engineering role",
            company="Example",
            location="Remote",
            description="General description",
            source="RemoteOK",
            skills=[
                "Python",
                "Terraform",
            ],
        )

        report = self.analyzer.analyze(
            profile=self.profile,
            jobs=[job],
        )

        detected = {
            item.skill
            for item in report.skill_stats
        }

        self.assertIn(
            "Python",
            detected,
        )

        self.assertIn(
            "Terraform",
            detected,
        )

    def test_empty_market_returns_stable_report(
        self,
    ):
        report = self.analyzer.analyze(
            profile=self.profile,
            jobs=[],
        )

        self.assertEqual(
            report.total_jobs,
            0,
        )

        self.assertEqual(
            report.coverage_percentage,
            0.0,
        )

        self.assertTrue(
            report.warnings
        )

    def test_invalid_job_is_rejected(
        self,
    ):
        with self.assertRaises(TypeError):
            self.analyzer.analyze(
                profile=self.profile,
                jobs=[object()],
            )

    def test_invalid_profile_is_rejected(
        self,
    ):
        with self.assertRaises(TypeError):
            self.analyzer.analyze(
                profile=object(),
                jobs=[],
            )


if __name__ == "__main__":
    unittest.main()
