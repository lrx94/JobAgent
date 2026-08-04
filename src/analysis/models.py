from __future__ import annotations

from dataclasses import dataclass, field

from src.analysis.evidence import Evidence


SENIORITY_LEVELS = {
    "junior",
    "confirmed",
    "senior",
    "lead",
    "manager",
    "executive",
    "unknown",
}


@dataclass(
    frozen=True,
    slots=True,
)
class ExperienceRequirement:
    """
    Expérience générale ou spécifique détectée.
    """

    years: float | None = None
    domain: str | None = None
    required: bool = False
    evidence: tuple[Evidence, ...] = ()

    def __post_init__(self) -> None:
        normalized_years = None

        if self.years is not None:
            normalized_years = max(
                0.0,
                float(self.years),
            )

        normalized_domain = (
            str(self.domain).strip()
            if self.domain is not None
            else None
        )

        if not normalized_domain:
            normalized_domain = None

        object.__setattr__(
            self,
            "years",
            normalized_years,
        )

        object.__setattr__(
            self,
            "domain",
            normalized_domain,
        )

        object.__setattr__(
            self,
            "required",
            bool(self.required),
        )

        object.__setattr__(
            self,
            "evidence",
            tuple(self.evidence or ()),
        )


@dataclass(
    frozen=True,
    slots=True,
)
class ManagementScope:
    """
    Périmètre managérial observé ou requis.
    """

    required: bool = False
    team_size: int | None = None
    budget_amount: int | None = None
    evidence: tuple[Evidence, ...] = ()

    def __post_init__(self) -> None:
        normalized_team_size = (
            max(0, int(self.team_size))
            if self.team_size is not None
            else None
        )

        normalized_budget = (
            max(0, int(self.budget_amount))
            if self.budget_amount is not None
            else None
        )

        object.__setattr__(
            self,
            "required",
            bool(self.required),
        )

        object.__setattr__(
            self,
            "team_size",
            normalized_team_size,
        )

        object.__setattr__(
            self,
            "budget_amount",
            normalized_budget,
        )

        object.__setattr__(
            self,
            "evidence",
            tuple(self.evidence or ()),
        )


@dataclass(
    frozen=True,
    slots=True,
)
class StructuredAnalysis:
    """
    Socle commun aux futures analyses CV et annonce.

    Ce modèle ne remplace pas encore CareerAnalysis
    ni CVAnalysisResult.
    """

    hard_skills: tuple[str, ...] = ()
    soft_skills: tuple[str, ...] = ()
    seniority: str = "unknown"

    experience: tuple[
        ExperienceRequirement,
        ...
    ] = ()

    management: ManagementScope = field(
        default_factory=ManagementScope
    )

    certifications: tuple[str, ...] = ()
    languages: tuple[str, ...] = ()
    sectors: tuple[str, ...] = ()
    responsibilities: tuple[str, ...] = ()

    evidence: tuple[Evidence, ...] = ()
    warnings: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "hard_skills",
            self._normalize_values(
                self.hard_skills
            ),
        )

        object.__setattr__(
            self,
            "soft_skills",
            self._normalize_values(
                self.soft_skills
            ),
        )

        normalized_seniority = str(
            self.seniority or "unknown"
        ).strip().casefold()

        if normalized_seniority not in SENIORITY_LEVELS:
            normalized_seniority = "unknown"

        object.__setattr__(
            self,
            "seniority",
            normalized_seniority,
        )

        object.__setattr__(
            self,
            "experience",
            tuple(self.experience or ()),
        )

        object.__setattr__(
            self,
            "certifications",
            self._normalize_values(
                self.certifications
            ),
        )

        object.__setattr__(
            self,
            "languages",
            self._normalize_values(
                self.languages
            ),
        )

        object.__setattr__(
            self,
            "sectors",
            self._normalize_values(
                self.sectors
            ),
        )

        object.__setattr__(
            self,
            "responsibilities",
            self._normalize_values(
                self.responsibilities
            ),
        )

        object.__setattr__(
            self,
            "evidence",
            tuple(self.evidence or ()),
        )

        object.__setattr__(
            self,
            "warnings",
            self._normalize_values(
                self.warnings
            ),
        )

    @staticmethod
    def _normalize_values(
        values: tuple[str, ...] | list[str],
    ) -> tuple[str, ...]:
        normalized: list[str] = []
        seen: set[str] = set()

        for value in values or ():
            cleaned = str(
                value or ""
            ).strip()

            if not cleaned:
                continue

            identity = cleaned.casefold()

            if identity in seen:
                continue

            seen.add(identity)
            normalized.append(cleaned)

        return tuple(normalized)