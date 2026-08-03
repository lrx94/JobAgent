from __future__ import annotations

from collections import Counter, defaultdict
from collections.abc import Iterable
from itertools import combinations
from typing import Any

from src.ai.skill_extractor import (
    SkillExtractor,
)
from src.domain import Job
from src.market.models import (
    MarketReport,
    MarketSkillStat,
    MarketSourceStat,
    SkillCooccurrence,
)
from src.profile import Profile


class MarketAnalyzer:
    """
    Analyse un ensemble d'offres pour produire un
    portrait statistique du profil type recherché.

    L'analyse réutilise le SkillExtractor de JobAgent.
    Elle ne possède aucun catalogue parallèle.
    """

    def __init__(
        self,
        skill_extractor: Any | None = None,
        top_skill_limit: int = 25,
        top_pair_limit: int = 20,
        minimum_pair_count: int = 2,
    ) -> None:
        self.skill_extractor = (
            skill_extractor
            or SkillExtractor()
        )

        self.top_skill_limit = max(
            1,
            int(top_skill_limit),
        )

        self.top_pair_limit = max(
            1,
            int(top_pair_limit),
        )

        self.minimum_pair_count = max(
            1,
            int(minimum_pair_count),
        )

    def analyze(
        self,
        *,
        profile: Profile,
        jobs: Iterable[Job],
        profile_skills: (
            Iterable[str] | None
        ) = None,
        profile_skill_source: str = "keywords",
    ) -> MarketReport:
        """
        Analyse les offres fournies et compare les
        compétences observées avec celles du profil.

        Une compétence n'est comptée qu'une seule fois
        par offre, même si elle apparaît plusieurs fois
        dans le texte.
        """

        if not isinstance(
            profile,
            Profile,
        ):
            raise TypeError(
                "profile doit être une instance "
                "de Profile."
            )

        normalized_jobs = self._normalize_jobs(
            jobs
        )

        if profile_skills is None:
            normalized_profile_skills = tuple(
                self._extract_profile_skills(
                    profile
                )
            )

            normalized_profile_skill_source = (
                "keywords"
            )

        else:
            normalized_profile_skills = tuple(
                self._normalize_profile_skills(
                    profile_skills
                )
            )

            normalized_profile_skill_source = (
                str(
                    profile_skill_source
                    or "unknown"
                ).strip()
                or "unknown"
            )

        profile_skill_keys = {
            value.casefold()
            for value
            in normalized_profile_skills
        }

        skill_job_counts: Counter[str] = (
            Counter()
        )

        pair_job_counts: Counter[
            tuple[str, str]
        ] = Counter()

        source_job_counts: Counter[str] = (
            Counter()
        )

        source_jobs_with_skills: Counter[
            str
        ] = Counter()

        source_distinct_skills: dict[
            str,
            set[str],
        ] = defaultdict(set)

        jobs_with_skills = 0

        for job in normalized_jobs:
            source = str(
                job.source
                or "Source inconnue"
            ).strip()

            source_job_counts[source] += 1

            job_skills = (
                self._extract_job_skills(
                    job
                )
            )

            if not job_skills:
                continue

            jobs_with_skills += 1

            source_jobs_with_skills[
                source
            ] += 1

            source_distinct_skills[
                source
            ].update(
                job_skills
            )

            for skill in job_skills:
                skill_job_counts[
                    skill
                ] += 1

            for first, second in combinations(
                sorted(
                    job_skills,
                    key=str.casefold,
                ),
                2,
            ):
                pair_job_counts[
                    (
                        first,
                        second,
                    )
                ] += 1

        total_jobs = len(
            normalized_jobs
        )

        skill_stats = self._build_skill_stats(
            skill_job_counts=(
                skill_job_counts
            ),
            total_jobs=total_jobs,
            profile_skill_keys=(
                profile_skill_keys
            ),
        )

        missing_stats = tuple(
            item
            for item in skill_stats
            if item.missing_from_profile
        )

        source_stats = self._build_source_stats(
            source_job_counts=(
                source_job_counts
            ),
            source_jobs_with_skills=(
                source_jobs_with_skills
            ),
            source_distinct_skills=(
                source_distinct_skills
            ),
        )

        cooccurrences = (
            self._build_cooccurrences(
                pair_job_counts=(
                    pair_job_counts
                ),
                total_jobs=total_jobs,
            )
        )

        warnings: list[str] = []

        if not normalized_jobs:
            warnings.append(
                "Aucune offre n'a été fournie "
                "à l'analyse de marché."
            )

        elif jobs_with_skills == 0:
            warnings.append(
                "Aucune compétence du catalogue "
                "n'a été détectée dans les offres."
            )

        elif (
            jobs_with_skills
            < total_jobs
        ):
            warnings.append(
                "Certaines offres ne contiennent "
                "aucune compétence reconnue par "
                "le catalogue actuel."
            )

        return MarketReport(
            profile_name=profile.name,
            total_jobs=total_jobs,
            jobs_with_detected_skills=(
                jobs_with_skills
            ),
            jobs_without_detected_skills=(
                total_jobs
                - jobs_with_skills
            ),
            profile_skills=(
                normalized_profile_skills
            ),
            profile_skill_source=(
                normalized_profile_skill_source
            ),
            skill_stats=skill_stats,
            missing_skill_stats=(
                missing_stats
            ),
            source_stats=source_stats,
            cooccurrences=cooccurrences,
            warnings=tuple(warnings),
            metadata={
                "top_skill_limit": (
                    self.top_skill_limit
                ),
                "top_pair_limit": (
                    self.top_pair_limit
                ),
                "minimum_pair_count": (
                    self.minimum_pair_count
                ),
            },
        )

    def _extract_profile_skills(
        self,
        profile: Profile,
    ) -> list[str]:
        text = " ".join(
            str(value)
            for value in (
                profile.keywords
                or []
            )
            if str(value).strip()
        )

        return self._normalize_skills(
            self.skill_extractor.extract(
                text
            )
        )

    def _normalize_profile_skills(
        self,
        values: Iterable[str],
    ) -> list[str]:
        """
        Normalise les compétences provenant du CV avec
        le même SkillExtractor que celui utilisé pour
        les offres.

        Les valeurs originales sont conservées en repli
        afin de rester compatible avec les analyses CV
        déjà normalisées.
        """

        supplied = self._normalize_skills(
            values
        )

        if not supplied:
            return []

        extracted = self._normalize_skills(
            self.skill_extractor.extract(
                " ".join(supplied)
            )
        )

        merged: list[str] = []
        seen: set[str] = set()

        for skill in (
            extracted
            + supplied
        ):
            identity = skill.casefold()

            if identity in seen:
                continue

            seen.add(identity)
            merged.append(skill)

        return sorted(
            merged,
            key=str.casefold,
        )

    def _extract_job_skills(
        self,
        job: Job,
    ) -> list[str]:
        """
        Fusionne les compétences déjà fournies par
        le provider et celles extraites du texte.

        Cela permet :
        - d'exploiter les tags RemoteOK ;
        - d'exploiter les descriptions France Travail ;
        - de conserver le catalogue central comme
          mécanisme de normalisation.
        """

        text = " ".join(
            [
                str(
                    job.title
                    or ""
                ),
                str(
                    job.description
                    or ""
                ),
                " ".join(
                    str(value)
                    for value in (
                        job.skills
                        or []
                    )
                ),
            ]
        )

        extracted = (
            self.skill_extractor.extract(
                text
            )
        )

        return self._normalize_skills(
            extracted
        )

    def _build_skill_stats(
        self,
        *,
        skill_job_counts: Counter[str],
        total_jobs: int,
        profile_skill_keys: set[str],
    ) -> tuple[MarketSkillStat, ...]:
        ordered = sorted(
            skill_job_counts.items(),
            key=lambda item: (
                -item[1],
                item[0].casefold(),
            ),
        )

        result: list[
            MarketSkillStat
        ] = []

        for skill, job_count in ordered[
            : self.top_skill_limit
        ]:
            percentage = (
                round(
                    (
                        job_count
                        / total_jobs
                    )
                    * 100,
                    1,
                )
                if total_jobs > 0
                else 0.0
            )

            result.append(
                MarketSkillStat(
                    skill=skill,
                    job_count=job_count,
                    percentage=percentage,
                    present_in_profile=(
                        skill.casefold()
                        in profile_skill_keys
                    ),
                )
            )

        return tuple(result)

    def _build_source_stats(
        self,
        *,
        source_job_counts: Counter[str],
        source_jobs_with_skills: Counter[
            str
        ],
        source_distinct_skills: dict[
            str,
            set[str],
        ],
    ) -> tuple[MarketSourceStat, ...]:
        result = [
            MarketSourceStat(
                source=source,
                job_count=job_count,
                jobs_with_skills=(
                    source_jobs_with_skills[
                        source
                    ]
                ),
                detected_skill_count=len(
                    source_distinct_skills[
                        source
                    ]
                ),
            )
            for source, job_count
            in source_job_counts.items()
        ]

        result.sort(
            key=lambda item: (
                -item.job_count,
                item.source.casefold(),
            )
        )

        return tuple(result)

    def _build_cooccurrences(
        self,
        *,
        pair_job_counts: Counter[
            tuple[str, str]
        ],
        total_jobs: int,
    ) -> tuple[
        SkillCooccurrence,
        ...
    ]:
        eligible_pairs = [
            (
                pair,
                count,
            )
            for pair, count
            in pair_job_counts.items()
            if count
            >= self.minimum_pair_count
        ]

        eligible_pairs.sort(
            key=lambda item: (
                -item[1],
                item[0][0].casefold(),
                item[0][1].casefold(),
            )
        )

        result: list[
            SkillCooccurrence
        ] = []

        for (
            first_skill,
            second_skill,
        ), job_count in eligible_pairs[
            : self.top_pair_limit
        ]:
            percentage = (
                round(
                    (
                        job_count
                        / total_jobs
                    )
                    * 100,
                    1,
                )
                if total_jobs > 0
                else 0.0
            )

            result.append(
                SkillCooccurrence(
                    first_skill=(
                        first_skill
                    ),
                    second_skill=(
                        second_skill
                    ),
                    job_count=job_count,
                    percentage=percentage,
                )
            )

        return tuple(result)

    @staticmethod
    def _normalize_jobs(
        jobs: Iterable[Job],
    ) -> list[Job]:
        result: list[Job] = []

        for job in jobs or []:
            if not isinstance(
                job,
                Job,
            ):
                raise TypeError(
                    "Toutes les offres doivent "
                    "être des instances de Job."
                )

            result.append(job)

        return result

    @staticmethod
    def _normalize_skills(
        values: Iterable[Any],
    ) -> list[str]:
        result: list[str] = []
        seen: set[str] = set()

        for value in values or []:
            cleaned = str(
                value
                or ""
            ).strip()

            if not cleaned:
                continue

            identity = cleaned.casefold()

            if identity in seen:
                continue

            seen.add(identity)
            result.append(cleaned)

        return sorted(
            result,
            key=str.casefold,
        )