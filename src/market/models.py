from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(
    frozen=True,
    slots=True,
)
class MarketSkillStat:
    """
    Fréquence d'une compétence dans l'échantillon
    d'offres analysé.

    `job_count` compte le nombre d'offres distinctes
    contenant cette compétence.
    """

    skill: str
    job_count: int
    percentage: float
    present_in_profile: bool = False

    @property
    def missing_from_profile(self) -> bool:
        return not self.present_in_profile


@dataclass(
    frozen=True,
    slots=True,
)
class MarketSourceStat:
    """
    Couverture de l'analyse pour une source d'offres.
    """

    source: str
    job_count: int
    jobs_with_skills: int
    detected_skill_count: int

    @property
    def coverage_percentage(self) -> float:
        if self.job_count <= 0:
            return 0.0

        return round(
            (
                self.jobs_with_skills
                / self.job_count
            )
            * 100,
            1,
        )


@dataclass(
    frozen=True,
    slots=True,
)
class SkillCooccurrence:
    """
    Nombre d'offres contenant simultanément deux
    compétences.
    """

    first_skill: str
    second_skill: str
    job_count: int
    percentage: float


@dataclass(
    frozen=True,
    slots=True,
)
class MarketReport:
    """
    Portrait statistique d'un marché observé pour
    un profil et un ensemble d'offres.

    Ce rapport décrit uniquement l'échantillon fourni.
    Il ne prétend pas représenter tout le marché.
    """

    profile_name: str
    total_jobs: int
    jobs_with_detected_skills: int
    jobs_without_detected_skills: int

    profile_skills: tuple[str, ...] = ()
    skill_stats: tuple[
        MarketSkillStat,
        ...
    ] = ()
    missing_skill_stats: tuple[
        MarketSkillStat,
        ...
    ] = ()
    source_stats: tuple[
        MarketSourceStat,
        ...
    ] = ()
    cooccurrences: tuple[
        SkillCooccurrence,
        ...
    ] = ()

    warnings: tuple[str, ...] = ()

    metadata: dict[str, object] = field(
        default_factory=dict
    )

    @property
    def coverage_percentage(self) -> float:
        if self.total_jobs <= 0:
            return 0.0

        return round(
            (
                self.jobs_with_detected_skills
                / self.total_jobs
            )
            * 100,
            1,
        )

    @property
    def detected_skill_count(self) -> int:
        return len(
            self.skill_stats
        )

    @property
    def top_skills(
        self,
    ) -> tuple[MarketSkillStat, ...]:
        return self.skill_stats

    @property
    def top_missing_skills(
        self,
    ) -> tuple[MarketSkillStat, ...]:
        return self.missing_skill_stats