from __future__ import annotations

import re
import unicodedata
from collections.abc import Iterable

from src.career.job_role_catalog import (
    JOB_ROLE_CATALOG,
)
from src.career.models import (
    CareerAnalysis,
    JobRoleDefinition,
    RoleSuggestion,
)


class RoleDetector:
    """
    Détecte les métiers probables à partir du texte d'un CV
    et des compétences déjà extraites.

    Le calcul est déterministe :

    - présence d'un intitulé métier : poids fort ;
    - compétences cœur : poids important ;
    - compétences complémentaires : poids secondaire ;
    - termes explicitement incompatibles : pénalité.
    """

    TITLE_WEIGHT = 60.0
    CORE_SKILL_WEIGHT = 30.0
    SUPPORTING_SKILL_WEIGHT = 10.0
    EXCLUSION_PENALTY = 35.0

    SENIORITY_LEVELS: tuple[
        tuple[str, tuple[str, ...]],
        ...,
    ] = (
        (
            "executive",
            (
                "chief ",
                "directeur",
                "directrice",
                "direction générale",
                "comex",
                "codir",
                "vice president",
                "vp ",
                "head of ",
                "c-level",
            ),
        ),
        (
            "senior",
            (
                "senior",
                "responsable",
                "manager",
                "lead",
                "plus de 10 ans",
                "10 ans d'expérience",
                "15 ans d'expérience",
                "20 ans d'expérience",
            ),
        ),
        (
            "confirmed",
            (
                "confirmé",
                "confirmee",
                "experienced",
                "expérimenté",
                "5 ans d'expérience",
            ),
        ),
        (
            "junior",
            (
                "junior",
                "débutant",
                "graduate",
                "entry level",
                "alternance",
                "stage",
            ),
        ),
    )

    def __init__(
        self,
        catalog: Iterable[
            JobRoleDefinition
        ] | None = None,
    ) -> None:
        self.catalog = tuple(
            catalog
            if catalog is not None
            else JOB_ROLE_CATALOG
        )

    def analyze(
        self,
        cv_text: str,
        extracted_skills: list[str] | tuple[str, ...],
        limit: int = 5,
    ) -> CareerAnalysis:
        normalized_text = self._normalize_text(
            cv_text
        )

        normalized_skills = tuple(
            self._normalize_collection(
                extracted_skills
            )
        )

        suggestions = [
            self._score_role(
                role=role,
                normalized_text=normalized_text,
                normalized_skills=normalized_skills,
            )
            for role in self.catalog
        ]

        suggestions = [
            suggestion
            for suggestion in suggestions
            if suggestion.score > 0
        ]

        suggestions.sort(
            key=lambda item: (
                item.score,
                len(item.matched_aliases),
                len(item.matched_skills),
                item.label,
            ),
            reverse=True,
        )

        normalized_limit = max(
            1,
            int(limit),
        )

        selected_suggestions = tuple(
            suggestions[:normalized_limit]
        )

        primary_role = (
            selected_suggestions[0]
            if selected_suggestions
            else None
        )

        suggested_title = (
            primary_role.label
            if primary_role is not None
            else "Profil professionnel"
        )

        search_terms = self._build_search_terms(
            selected_suggestions
        )

        warnings: list[str] = []

        if not selected_suggestions:
            warnings.append(
                "Aucune famille de métiers n'a été "
                "identifiée avec suffisamment d'indices."
            )

        if not normalized_skills:
            warnings.append(
                "Aucune compétence normalisée n'a été "
                "fournie à l'analyse métier."
            )

        return CareerAnalysis(
            suggested_title=suggested_title,
            seniority=self.detect_seniority(
                cv_text
            ),
            extracted_skills=normalized_skills,
            role_suggestions=selected_suggestions,
            search_terms=search_terms,
            warnings=tuple(warnings),
        )

    def detect_seniority(
        self,
        cv_text: str,
    ) -> str:
        normalized_text = self._normalize_text(
            cv_text
        )

        for level, markers in self.SENIORITY_LEVELS:
            if any(
                self._contains_phrase(
                    normalized_text,
                    marker,
                )
                for marker in markers
            ):
                return level

        return "unknown"

    def _score_role(
        self,
        role: JobRoleDefinition,
        normalized_text: str,
        normalized_skills: tuple[str, ...],
    ) -> RoleSuggestion:
        matched_aliases = tuple(
            alias
            for alias in role.aliases
            if self._contains_phrase(
                normalized_text,
                alias,
            )
        )

        normalized_skill_set = set(
            normalized_skills
        )

        matched_core = tuple(
            skill
            for skill in role.core_skills
            if self._normalize_text(skill)
            in normalized_skill_set
        )

        matched_supporting = tuple(
            skill
            for skill in role.supporting_skills
            if self._normalize_text(skill)
            in normalized_skill_set
        )

        missing_core = tuple(
            skill
            for skill in role.core_skills
            if self._normalize_text(skill)
            not in normalized_skill_set
        )

        title_score = (
            self.TITLE_WEIGHT
            if matched_aliases
            else 0.0
        )

        core_score = self._ratio_score(
            matches=len(matched_core),
            total=len(role.core_skills),
            maximum=self.CORE_SKILL_WEIGHT,
        )

        supporting_score = self._ratio_score(
            matches=len(matched_supporting),
            total=len(role.supporting_skills),
            maximum=self.SUPPORTING_SKILL_WEIGHT,
        )

        exclusion_matches = sum(
            1
            for term in role.excluded_terms
            if self._contains_phrase(
                normalized_text,
                term,
            )
        )

        penalty = (
            self.EXCLUSION_PENALTY
            if exclusion_matches
            else 0.0
        )

        score = max(
            0.0,
            min(
                100.0,
                title_score
                + core_score
                + supporting_score
                - penalty,
            ),
        )

        matched_skills = tuple(
            dict.fromkeys(
                (
                    *matched_core,
                    *matched_supporting,
                )
            )
        )

        return RoleSuggestion(
            role_id=role.role_id,
            label=role.label,
            score=round(score, 2),
            matched_aliases=matched_aliases,
            matched_skills=matched_skills,
            missing_core_skills=missing_core,
            preferred_providers=(
                role.preferred_providers
            ),
        )

    @classmethod
    def _build_search_terms(
        cls,
        suggestions: tuple[
            RoleSuggestion,
            ...,
        ],
    ) -> tuple[str, ...]:
        terms: list[str] = []
        seen: set[str] = set()

        role_by_id = {
            role.role_id: role
            for role in JOB_ROLE_CATALOG
        }

        for suggestion in suggestions[:3]:
            role = role_by_id.get(
                suggestion.role_id
            )

            if role is None:
                continue

            for term in (
                role.label,
                *role.aliases,
            ):
                cleaned = str(term).strip()

                if not cleaned:
                    continue

                key = cleaned.casefold()

                if key in seen:
                    continue

                seen.add(key)
                terms.append(cleaned)

        return tuple(terms)

    @staticmethod
    def _ratio_score(
        matches: int,
        total: int,
        maximum: float,
    ) -> float:
        if total <= 0:
            return 0.0

        return (
            min(
                max(matches, 0),
                total,
            )
            / total
            * maximum
        )

    @classmethod
    def _contains_phrase(
        cls,
        normalized_text: str,
        phrase: str,
    ) -> bool:
        normalized_phrase = cls._normalize_text(
            phrase
        )

        if not normalized_phrase:
            return False

        pattern = (
            r"(?<!\w)"
            + re.escape(normalized_phrase)
            + r"(?!\w)"
        )

        return (
            re.search(
                pattern,
                normalized_text,
            )
            is not None
        )

    @staticmethod
    def _normalize_collection(
        values: Iterable[str],
    ) -> list[str]:
        normalized: list[str] = []
        seen: set[str] = set()

        for value in values or []:
            cleaned = RoleDetector._normalize_text(
                value
            )

            if not cleaned:
                continue

            if cleaned in seen:
                continue

            seen.add(cleaned)
            normalized.append(cleaned)

        return normalized

    @staticmethod
    def _normalize_text(
        value: str,
    ) -> str:
        text = str(value or "").strip().casefold()

        decomposed = unicodedata.normalize(
            "NFKD",
            text,
        )

        without_accents = "".join(
            character
            for character in decomposed
            if not unicodedata.combining(
                character
            )
        )

        return " ".join(
            without_accents.split()
        )