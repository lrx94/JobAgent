from __future__ import annotations

import re
import unicodedata
from collections.abc import Iterable

from src.analysis.evidence import Evidence
from src.analysis.models import (
    ExperienceRequirement,
    ManagementScope,
    StructuredAnalysis,
)
from src.career.models import CareerAnalysis
from src.career.role_detector import RoleDetector
from src.cvs.results import CVAnalysisResult
from src.skills import ConceptMatcher

class CandidateAnalyzer:
    """
    Produit une analyse structurée du candidat à partir
    des résultats déjà générés par JobAgent.

    Réutilisation :
    - CVAnalysisResult fournit le texte et les skills ;
    - RoleDetector fournit la seniorité et le métier ;
    - aucun nouveau parsing PDF ;
    - aucun nouveau catalogue de hard skills.
    """

    EXPERIENCE_PATTERN = re.compile(
        r"\b(?:plus\s+de\s+|au\s+moins\s+|minimum\s+)?"
        r"(\d{1,2})\s*(?:ans?|années?)"
        r"(?:\s+d['’]expérience)?\b",
        re.IGNORECASE,
    )

    TEAM_SIZE_PATTERN = re.compile(
        r"\b(?:équipe|team)\s+(?:de\s+)?"
        r"(?:plus\s+de\s+|environ\s+)?"
        r"(\d{1,4})\s+(?:personnes?|collaborateurs?|membres?)\b",
        re.IGNORECASE,
    )

    BUDGET_PATTERN = re.compile(
        r"\b(\d+(?:[.,]\d+)?)\s*"
        r"(k|m|million|millions)?\s*"
        r"(?:€|euros?)"
        r"(?:\s*(?:opex|capex))?"
        r"(?!\w)",
        re.IGNORECASE,
    )

    MANAGEMENT_MARKERS = (
        "management",
        "manager",
        "encadrement",
        "animation d'équipe",
        "animation des équipes",
        "pilotage des équipes",
        "direction d'équipe",
        "responsable d'équipe",
        "management d'équipe",
        "management des équipes",
    )

    SOFT_SKILLS: dict[str, tuple[str, ...]] = {
        "Leadership": (
            "leadership",
            "leader",
        ),
        "Communication": (
            "communication",
            "communicant",
            "communication orale",
            "communication écrite",
        ),
        "Autonomie": (
            "autonomie",
            "autonome",
        ),
        "Esprit d'analyse": (
            "esprit d'analyse",
            "capacité d'analyse",
            "capacite d'analyse",
            "analyse et synthèse",
        ),
        "Capacité de synthèse": (
            "capacité de synthèse",
            "capacite de synthese",
            "esprit de synthèse",
        ),
        "Gestion des parties prenantes": (
            "parties prenantes",
            "stakeholders",
            "stakeholder management",
        ),
        "Travail en équipe": (
            "travail en équipe",
            "travail en equipe",
            "esprit d'équipe",
        ),
        "Adaptabilité": (
            "adaptabilité",
            "adaptabilite",
            "capacité d'adaptation",
        ),
    }

    CERTIFICATIONS: dict[str, tuple[str, ...]] = {
        "ITIL": (
            "itil",
            "itilv4",
            "itil v4",
            "itil 4",
            "itil foundation",
        ),
        "COBIT": (
            "cobit",
            "cobit 2019",
            "cobit2019",
        ),
        "PMP": (
            "pmp",
            "project management professional",
        ),
        "PRINCE2": (
            "prince2",
            "prince 2",
        ),
        "TOGAF": (
            "togaf",
        ),
        "Scrum Master": (
            "scrum master",
            "psm i",
            "psm ii",
            "csm",
        ),
    }

    LANGUAGES: dict[str, tuple[str, ...]] = {
        "Anglais": (
            "anglais",
            "english",
        ),
        "Français": (
            "français",
            "francais",
            "french",
        ),
        "Espagnol": (
            "espagnol",
            "spanish",
        ),
        "Allemand": (
            "allemand",
            "german",
        ),
        "Italien": (
            "italien",
            "italian",
        ),
    }

    def __init__(
        self,
        role_detector: RoleDetector | None = None,
        concept_matcher: ConceptMatcher | None = None,
    ) -> None:
        self.role_detector = (
            role_detector
            or RoleDetector()
        )

        self.concept_matcher = (
            concept_matcher
            or ConceptMatcher()
        )

    def analyze(
        self,
        *,
        cv_analysis: CVAnalysisResult,
        career_analysis: CareerAnalysis | None = None,
    ) -> StructuredAnalysis:
        if not isinstance(
            cv_analysis,
            CVAnalysisResult,
        ):
            raise TypeError(
                "cv_analysis doit être une instance "
                "de CVAnalysisResult."
            )

        text = cv_analysis.text

        resolved_career_analysis = (
            career_analysis
            or self.role_detector.analyze(
                cv_text=text,
                extracted_skills=(
                    cv_analysis.skills
                ),
            )
        )

        if not isinstance(
            resolved_career_analysis,
            CareerAnalysis,
        ):
            raise TypeError(
                "career_analysis doit être une instance "
                "de CareerAnalysis."
            )

        experience = self._extract_experience(
            text,
            source="cv",
            required=False,
        )

        management = self._extract_management(
            text,
            source="cv",
        )

        soft_skills = self._extract_catalog_values(
            text=text,
            catalog=self.SOFT_SKILLS,
        )

        certifications = self._extract_catalog_values(
            text=text,
            catalog=self.CERTIFICATIONS,
        )

        languages = self._extract_catalog_values(
            text=text,
            catalog=self.LANGUAGES,
        )

        evidence = self._collect_evidence(
            experience=experience,
            management=management,
        )

        warnings: list[str] = []

        if not cv_analysis.skills:
            warnings.append(
                "Aucune compétence technique n'a été "
                "détectée dans le CV."
            )

        if not experience:
            warnings.append(
                "Aucune durée d'expérience explicite "
                "n'a été détectée."
            )

        concept_skills = (
            self.concept_matcher
            .extract_labels(text)
        )

        hard_skills = self._merge_values(
            concept_skills,
            cv_analysis.skills,
        )
        
        return StructuredAnalysis(
            hard_skills=hard_skills,
            soft_skills=soft_skills,
            seniority=(
                resolved_career_analysis.seniority
            ),
            experience=experience,
            management=management,
            certifications=certifications,
            languages=languages,
            evidence=evidence,
            warnings=tuple(warnings),
        )

    def _extract_experience(
        self,
        text: str,
        *,
        source: str,
        required: bool,
    ) -> tuple[ExperienceRequirement, ...]:
        matches: list[
            ExperienceRequirement
        ] = []

        seen_years: set[float] = set()

        for match in self.EXPERIENCE_PATTERN.finditer(
            text
        ):
            years = float(
                match.group(1)
            )

            if years in seen_years:
                continue

            seen_years.add(years)

            evidence = Evidence(
                value=f"{years:g} ans",
                source=source,
                excerpt=self._excerpt(
                    text,
                    match.start(),
                    match.end(),
                ),
                confidence=0.9,
            )

            matches.append(
                ExperienceRequirement(
                    years=years,
                    required=required,
                    evidence=(
                        evidence,
                    ),
                )
            )

        matches.sort(
            key=lambda item: (
                item.years or 0
            ),
            reverse=True,
        )

        return tuple(matches)

    def _extract_management(
        self,
        text: str,
        *,
        source: str,
    ) -> ManagementScope:
        normalized = self._normalize_text(
            text
        )

        management_detected = any(
            marker in normalized
            for marker in self.MANAGEMENT_MARKERS
        )

        team_size: int | None = None
        budget_amount: int | None = None
        evidence: list[Evidence] = []

        team_match = self.TEAM_SIZE_PATTERN.search(
            text
        )

        if team_match is not None:
            team_size = int(
                team_match.group(1)
            )

            evidence.append(
                Evidence(
                    value=(
                        f"Équipe de {team_size} personnes"
                    ),
                    source=source,
                    excerpt=self._excerpt(
                        text,
                        team_match.start(),
                        team_match.end(),
                    ),
                    confidence=0.95,
                )
            )

            management_detected = True

        budget_match = self.BUDGET_PATTERN.search(
            text
        )

        if budget_match is not None:
            number = float(
                budget_match
                .group(1)
                .replace(",", ".")
            )

            unit = str(
                budget_match.group(2)
                or ""
            ).casefold()

            multiplier = 1

            if unit == "k":
                multiplier = 1_000
            elif unit in {
                "m",
                "million",
                "millions",
            }:
                multiplier = 1_000_000

            budget_amount = int(
                number * multiplier
            )

            evidence.append(
                Evidence(
                    value=(
                        f"Budget de {budget_amount} €"
                    ),
                    source=source,
                    excerpt=self._excerpt(
                        text,
                        budget_match.start(),
                        budget_match.end(),
                    ),
                    confidence=0.9,
                )
            )

        return ManagementScope(
            required=management_detected,
            team_size=team_size,
            budget_amount=budget_amount,
            evidence=tuple(evidence),
        )

    def _extract_catalog_values(
        self,
        *,
        text: str,
        catalog: dict[
            str,
            tuple[str, ...],
        ],
    ) -> tuple[str, ...]:
        normalized_text = self._normalize_text(
            text
        )

        detected: list[str] = []

        for canonical, aliases in catalog.items():
            candidates = (
                canonical,
                *aliases,
            )

            if any(
                self._contains_term(
                    normalized_text,
                    self._normalize_text(
                        candidate
                    ),
                )
                for candidate in candidates
            ):
                detected.append(
                    canonical
                )

        return tuple(detected)

    @staticmethod
    def _collect_evidence(
        *,
        experience: tuple[
            ExperienceRequirement,
            ...
        ],
        management: ManagementScope,
    ) -> tuple[Evidence, ...]:
        evidence: list[Evidence] = []

        for item in experience:
            evidence.extend(
                item.evidence
            )

        evidence.extend(
            management.evidence
        )

        return tuple(evidence)

    @staticmethod
    def _normalize_text(
        value: str,
    ) -> str:
        normalized = unicodedata.normalize(
            "NFKD",
            str(value or ""),
        )

        without_accents = "".join(
            character
            for character in normalized
            if not unicodedata.combining(
                character
            )
        )

        return " ".join(
            without_accents
            .casefold()
            .split()
        )

    @staticmethod
    def _contains_term(
        normalized_text: str,
        normalized_term: str,
    ) -> bool:
        if not normalized_term:
            return False

        pattern = (
            r"(?<!\w)"
            + re.escape(
                normalized_term
            )
            + r"(?!\w)"
        )

        return bool(
            re.search(
                pattern,
                normalized_text,
            )
        )

    @staticmethod
    def _merge_values(
        *collections,
    ) -> tuple[str, ...]:
        result: list[str] = []
        seen: set[str] = set()

        for collection in collections:
            for value in collection or ():
                cleaned = str(
                    value or ""
                ).strip()

                if not cleaned:
                    continue

                identity = cleaned.casefold()

                if identity in seen:
                    continue

                seen.add(identity)
                result.append(cleaned)

        return tuple(result)

    @staticmethod
    def _excerpt(
        text: str,
        start: int,
        end: int,
        radius: int = 80,
    ) -> str:
        excerpt_start = max(
            0,
            start - radius,
        )

        excerpt_end = min(
            len(text),
            end + radius,
        )

        return " ".join(
            text[
                excerpt_start:excerpt_end
            ].split()
        )