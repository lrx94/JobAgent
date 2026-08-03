from __future__ import annotations

from src.career.models import (
    CareerAnalysis,
    GeneratedProfile,
    RoleSuggestion,
)
from src.profile import Profile


class CareerProfileBuilder:
    """
    Construit un profil de recherche à partir d'une analyse métier.
    """

    def build(
        self,
        analysis: CareerAnalysis,
        role_id: str | None = None,
        locations: list[str] | None = None,
        salary_min: int | None = None,
        remote: bool = True,
    ) -> GeneratedProfile:
        selected_role = self._select_role(
            analysis=analysis,
            role_id=role_id,
        )

        keywords = self._build_keywords(
            analysis=analysis,
            selected_role=selected_role,
        )

        profile_name = (
            selected_role.label
            if selected_role is not None
            else analysis.suggested_title
        )

        profile = Profile(
            name=profile_name,
            keywords=keywords,
            locations=list(
                locations or []
            ),
            salary_min=salary_min or 0,
            remote=remote,
        )

        return GeneratedProfile(
            profile=profile,
            analysis=analysis,
            selected_role=selected_role,
            added_keywords=keywords,
        )

    @staticmethod
    def _select_role(
        analysis: CareerAnalysis,
        role_id: str | None,
    ) -> RoleSuggestion | None:
        if not analysis.role_suggestions:
            return None

        if role_id is None:
            return analysis.role_suggestions[0]

        normalized_role_id = str(
            role_id
        ).strip().casefold()

        for suggestion in analysis.role_suggestions:
            if (
                suggestion.role_id.casefold()
                == normalized_role_id
            ):
                return suggestion

        raise ValueError(
            "Le métier demandé ne figure pas dans "
            f"les suggestions : {role_id}"
        )

    @staticmethod
    def _build_keywords(
        analysis: CareerAnalysis,
        selected_role: RoleSuggestion | None,
    ) -> list[str]:
        values: list[str] = []

        if selected_role is not None:
            values.append(
                selected_role.label
            )
            values.extend(
                selected_role.matched_aliases
            )

        values.extend(
            analysis.extracted_skills
        )

        normalized: list[str] = []
        seen: set[str] = set()

        for value in values:
            cleaned = str(value).strip()

            if not cleaned:
                continue

            key = cleaned.casefold()

            if key in seen:
                continue

            seen.add(key)
            normalized.append(cleaned)

        return normalized