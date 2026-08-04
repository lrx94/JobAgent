from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass

from src.analysis.job import JobAnalyzer
from src.analysis.models import StructuredAnalysis
from src.analysis.scoring import (
    StructuredScore,
    StructuredScorer,
)
from src.domain import Job


@dataclass(
    frozen=True,
    slots=True,
)
class ScoreComparison:
    """
    Comparaison entre le score historique d'une offre
    et le nouveau score structuré.
    """

    job_identity: str
    legacy_score: float
    structured_score: float
    difference: float
    structured_result: StructuredScore


class ComparativeScoringService:
    """
    Exécute le scoring structuré en parallèle du score
    historique.

    Ce service ne modifie jamais Job.score.
    Le résultat détaillé est enregistré dans
    Job.match_details["structured"].
    """

    MATCH_DETAILS_KEY = "structured"

    def __init__(
        self,
        *,
        job_analyzer: JobAnalyzer | None = None,
        structured_scorer: StructuredScorer | None = None,
    ) -> None:
        self.job_analyzer = (
            job_analyzer
            or JobAnalyzer()
        )

        self.structured_scorer = (
            structured_scorer
            or StructuredScorer()
        )

    def compare(
        self,
        *,
        candidate: StructuredAnalysis,
        jobs: Iterable[Job],
    ) -> tuple[ScoreComparison, ...]:
        if not isinstance(
            candidate,
            StructuredAnalysis,
        ):
            raise TypeError(
                "candidate doit être un "
                "StructuredAnalysis."
            )

        comparisons: list[
            ScoreComparison
        ] = []

        for job in jobs or ():
            comparisons.append(
                self.compare_job(
                    candidate=candidate,
                    job=job,
                )
            )

        return tuple(comparisons)

    def compare_job(
        self,
        *,
        candidate: StructuredAnalysis,
        job: Job,
    ) -> ScoreComparison:
        if not isinstance(
            candidate,
            StructuredAnalysis,
        ):
            raise TypeError(
                "candidate doit être un "
                "StructuredAnalysis."
            )

        if not isinstance(
            job,
            Job,
        ):
            raise TypeError(
                "job doit être une instance de Job."
            )

        requirements = (
            self.job_analyzer
            .analyze_job(job)
        )

        structured_result = (
            self.structured_scorer.score(
                candidate=candidate,
                requirements=requirements,
            )
        )

        legacy_score = float(
            job.score or 0.0
        )

        structured_score = float(
            structured_result.global_score
        )

        job.match_details[
            self.MATCH_DETAILS_KEY
        ] = self._serialize_result(
            result=structured_result,
            requirements=requirements,
            legacy_score=legacy_score,
        )

        return ScoreComparison(
            job_identity=job.identity,
            legacy_score=legacy_score,
            structured_score=structured_score,
            difference=round(
                structured_score
                - legacy_score,
                1,
            ),
            structured_result=(
                structured_result
            ),
        )

    @staticmethod
    def _serialize_result(
        *,
        result: StructuredScore,
        requirements: StructuredAnalysis,
        legacy_score: float,
    ) -> dict[str, object]:
        return {
            "version": (
                result.metadata.get(
                    "scoring_version",
                    "unknown",
                )
            ),
            "legacy_score": legacy_score,
            "global_score": (
                result.global_score
            ),
            "dimensions": [
                {
                    "name": dimension.name,
                    "score": dimension.score,
                    "weight": dimension.weight,
                    "matched": list(
                        dimension.matched
                    ),
                    "missing": list(
                        dimension.missing
                    ),
                    "explanation": (
                        dimension.explanation
                    ),
                }
                for dimension
                in result.dimensions
            ],
            "strengths": list(
                result.strengths
            ),
            "gaps": list(
                result.gaps
            ),
            "warnings": list(
                result.warnings
            ),
            "requirements": {
                "hard_skills": list(
                    requirements.hard_skills
                ),
                "soft_skills": list(
                    requirements.soft_skills
                ),
                "seniority": (
                    requirements.seniority
                ),
                "certifications": list(
                    requirements.certifications
                ),
                "languages": list(
                    requirements.languages
                ),
                "experience_years": [
                    item.years
                    for item
                    in requirements.experience
                    if item.years is not None
                ],
                "management_required": (
                    requirements
                    .management
                    .required
                ),
                "team_size": (
                    requirements
                    .management
                    .team_size
                ),
            },
        }