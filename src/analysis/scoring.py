from __future__ import annotations

from dataclasses import dataclass, field

from src.analysis.models import (
    StructuredAnalysis,
)


@dataclass(
    frozen=True,
    slots=True,
)
class DimensionScore:
    name: str
    score: float
    weight: float
    matched: tuple[str, ...] = ()
    missing: tuple[str, ...] = ()
    explanation: str = ""

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "score",
            max(
                0.0,
                min(float(self.score), 100.0),
            ),
        )

        object.__setattr__(
            self,
            "weight",
            max(0.0, float(self.weight)),
        )

        object.__setattr__(
            self,
            "matched",
            tuple(self.matched or ()),
        )

        object.__setattr__(
            self,
            "missing",
            tuple(self.missing or ()),
        )


@dataclass(
    frozen=True,
    slots=True,
)
class StructuredScore:
    global_score: float
    dimensions: tuple[DimensionScore, ...]
    strengths: tuple[str, ...] = ()
    gaps: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()
    metadata: dict[str, object] = field(
        default_factory=dict
    )

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "global_score",
            max(
                0.0,
                min(
                    float(self.global_score),
                    100.0,
                ),
            ),
        )

        object.__setattr__(
            self,
            "dimensions",
            tuple(self.dimensions or ()),
        )


class StructuredScorer:
    """
    Compare deux StructuredAnalysis.

    Le candidat et l'annonce ont déjà été parsés.
    Ce composant ne réalise aucune extraction.
    """

    DEFAULT_WEIGHTS = {
        "hard_skills": 0.40,
        "experience": 0.20,
        "seniority": 0.15,
        "management": 0.10,
        "certifications": 0.07,
        "languages": 0.05,
        "soft_skills": 0.03,
    }

    SENIORITY_ORDER = {
        "unknown": 0,
        "junior": 1,
        "confirmed": 2,
        "senior": 3,
        "lead": 4,
        "manager": 5,
        "executive": 6,
    }

    def __init__(
        self,
        weights: dict[str, float] | None = None,
    ) -> None:
        self.weights = dict(
            weights or self.DEFAULT_WEIGHTS
        )

    def score(
        self,
        *,
        candidate: StructuredAnalysis,
        requirements: StructuredAnalysis,
    ) -> StructuredScore:
        if not isinstance(
            candidate,
            StructuredAnalysis,
        ):
            raise TypeError(
                "candidate doit être un "
                "StructuredAnalysis."
            )

        if not isinstance(
            requirements,
            StructuredAnalysis,
        ):
            raise TypeError(
                "requirements doit être un "
                "StructuredAnalysis."
            )

        dimensions = (
            self._score_collection(
                name="hard_skills",
                candidate_values=(
                    candidate.hard_skills
                ),
                required_values=(
                    requirements.hard_skills
                ),
            ),
            self._score_experience(
                candidate,
                requirements,
            ),
            self._score_seniority(
                candidate.seniority,
                requirements.seniority,
            ),
            self._score_management(
                candidate,
                requirements,
            ),
            self._score_collection(
                name="certifications",
                candidate_values=(
                    candidate.certifications
                ),
                required_values=(
                    requirements.certifications
                ),
            ),
            self._score_collection(
                name="languages",
                candidate_values=(
                    candidate.languages
                ),
                required_values=(
                    requirements.languages
                ),
            ),
            self._score_collection(
                name="soft_skills",
                candidate_values=(
                    candidate.soft_skills
                ),
                required_values=(
                    requirements.soft_skills
                ),
            ),
        )

        active_dimensions = tuple(
            dimension
            for dimension in dimensions
            if dimension.weight > 0
        )

        total_weight = sum(
            dimension.weight
            for dimension in active_dimensions
        )

        global_score = (
            sum(
                dimension.score
                * dimension.weight
                for dimension
                in active_dimensions
            )
            / total_weight
            if total_weight > 0
            else 0.0
        )

        strengths: list[str] = []
        gaps: list[str] = []

        for dimension in active_dimensions:
            strengths.extend(
                dimension.matched
            )
            gaps.extend(
                dimension.missing
            )

        warnings: list[str] = []

        if not requirements.hard_skills:
            warnings.append(
                "Aucune hard skill obligatoire "
                "n'a été détectée dans l'annonce."
            )

        return StructuredScore(
            global_score=round(
                global_score,
                1,
            ),
            dimensions=active_dimensions,
            strengths=self._deduplicate(
                strengths
            ),
            gaps=self._deduplicate(
                gaps
            ),
            warnings=tuple(warnings),
            metadata={
                "scoring_version": "3.16.4",
            },
        )

    def _score_collection(
        self,
        *,
        name: str,
        candidate_values: tuple[str, ...],
        required_values: tuple[str, ...],
    ) -> DimensionScore:
        weight = self.weights.get(
            name,
            0.0,
        )

        candidate_index = {
            value.casefold(): value
            for value in candidate_values
        }

        required_index = {
            value.casefold(): value
            for value in required_values
        }

        if not required_index:
            return DimensionScore(
                name=name,
                score=100.0,
                weight=weight,
                explanation=(
                    "Aucune exigence détectée."
                ),
            )

        matched_keys = (
            candidate_index.keys()
            & required_index.keys()
        )

        missing_keys = (
            required_index.keys()
            - candidate_index.keys()
        )

        matched = tuple(
            required_index[key]
            for key in sorted(
                matched_keys
            )
        )

        missing = tuple(
            required_index[key]
            for key in sorted(
                missing_keys
            )
        )

        score = (
            len(matched)
            / len(required_index)
        ) * 100

        return DimensionScore(
            name=name,
            score=score,
            weight=weight,
            matched=matched,
            missing=missing,
            explanation=(
                f"{len(matched)} exigence(s) "
                f"sur {len(required_index)} "
                "satisfaite(s)."
            ),
        )

    def _score_experience(
        self,
        candidate: StructuredAnalysis,
        requirements: StructuredAnalysis,
    ) -> DimensionScore:
        weight = self.weights[
            "experience"
        ]

        candidate_years = self._maximum_years(
            candidate
        )

        required_years = self._maximum_years(
            requirements
        )

        if required_years is None:
            return DimensionScore(
                name="experience",
                score=100.0,
                weight=weight,
                explanation=(
                    "Aucune expérience minimale "
                    "détectée."
                ),
            )

        if candidate_years is None:
            return DimensionScore(
                name="experience",
                score=0.0,
                weight=weight,
                missing=(
                    f"{required_years:g} ans "
                    "d'expérience",
                ),
                explanation=(
                    "Expérience du candidat "
                    "non déterminée."
                ),
            )

        score = min(
            (
                candidate_years
                / required_years
            )
            * 100,
            100.0,
        )

        matched = (
            (
                f"{candidate_years:g} ans "
                "d'expérience"
            ),
        ) if candidate_years >= required_years else ()

        missing = (
            (
                f"{required_years:g} ans requis"
            ),
        ) if candidate_years < required_years else ()

        return DimensionScore(
            name="experience",
            score=score,
            weight=weight,
            matched=matched,
            missing=missing,
            explanation=(
                f"{candidate_years:g} ans détectés "
                f"pour {required_years:g} ans requis."
            ),
        )

    def _score_seniority(
        self,
        candidate_level: str,
        required_level: str,
    ) -> DimensionScore:
        weight = self.weights[
            "seniority"
        ]

        if required_level == "unknown":
            return DimensionScore(
                name="seniority",
                score=100.0,
                weight=weight,
                explanation=(
                    "Aucune seniorité explicite."
                ),
            )

        candidate_rank = self.SENIORITY_ORDER.get(
            candidate_level,
            0,
        )

        required_rank = self.SENIORITY_ORDER.get(
            required_level,
            0,
        )

        if candidate_rank >= required_rank:
            score = 100.0
        elif candidate_rank == 0:
            score = 0.0
        else:
            score = max(
                0.0,
                100.0
                - (
                    required_rank
                    - candidate_rank
                )
                * 25.0,
            )

        return DimensionScore(
            name="seniority",
            score=score,
            weight=weight,
            matched=(
                (candidate_level,)
                if score == 100.0
                else ()
            ),
            missing=(
                (required_level,)
                if score < 100.0
                else ()
            ),
            explanation=(
                f"Seniorité candidat : "
                f"{candidate_level}; "
                f"poste : {required_level}."
            ),
        )

    def _score_management(
        self,
        candidate: StructuredAnalysis,
        requirements: StructuredAnalysis,
    ) -> DimensionScore:
        weight = self.weights[
            "management"
        ]

        required = (
            requirements.management.required
        )

        demonstrated = (
            candidate.management.required
        )

        if not required:
            return DimensionScore(
                name="management",
                score=100.0,
                weight=weight,
                explanation=(
                    "Management non explicitement "
                    "requis."
                ),
            )

        if not demonstrated:
            return DimensionScore(
                name="management",
                score=0.0,
                weight=weight,
                missing=(
                    "Expérience managériale",
                ),
                explanation=(
                    "Management requis mais non "
                    "détecté dans le CV."
                ),
            )

        required_team = (
            requirements.management.team_size
        )

        candidate_team = (
            candidate.management.team_size
        )

        if (
            required_team is not None
            and candidate_team is not None
            and candidate_team < required_team
        ):
            score = min(
                (
                    candidate_team
                    / required_team
                )
                * 100,
                100.0,
            )
        else:
            score = 100.0

        return DimensionScore(
            name="management",
            score=score,
            weight=weight,
            matched=(
                "Expérience managériale",
            ),
            explanation=(
                "Expérience managériale détectée."
            ),
        )

    @staticmethod
    def _maximum_years(
        analysis: StructuredAnalysis,
    ) -> float | None:
        years = [
            item.years
            for item in analysis.experience
            if item.years is not None
        ]

        return max(years) if years else None

    @staticmethod
    def _deduplicate(
        values: list[str],
    ) -> tuple[str, ...]:
        result: list[str] = []
        seen: set[str] = set()

        for value in values:
            identity = value.casefold()

            if identity in seen:
                continue

            seen.add(identity)
            result.append(value)

        return tuple(result)