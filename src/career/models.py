from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True, slots=True)
class JobRoleDefinition:
    """
    Définition canonique d'une famille de métiers.
    """

    role_id: str
    label: str
    aliases: tuple[str, ...]
    core_skills: tuple[str, ...] = ()
    supporting_skills: tuple[str, ...] = ()
    excluded_terms: tuple[str, ...] = ()
    categories: tuple[str, ...] = ()
    preferred_providers: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class RoleSuggestion:
    """
    Proposition de métier issue de l'analyse d'un CV.
    """

    role_id: str
    label: str
    score: float
    matched_aliases: tuple[str, ...] = ()
    matched_skills: tuple[str, ...] = ()
    missing_core_skills: tuple[str, ...] = ()
    preferred_providers: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, object]:
        return {
            "role_id": self.role_id,
            "label": self.label,
            "score": self.score,
            "matched_aliases": list(self.matched_aliases),
            "matched_skills": list(self.matched_skills),
            "missing_core_skills": list(
                self.missing_core_skills
            ),
            "preferred_providers": list(
                self.preferred_providers
            ),
        }


@dataclass(frozen=True, slots=True)
class CareerAnalysis:
    """
    Résultat global de l'analyse métier d'un CV.
    """

    suggested_title: str
    seniority: str
    extracted_skills: tuple[str, ...]
    role_suggestions: tuple[RoleSuggestion, ...]
    search_terms: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()

    @property
    def primary_role(self) -> RoleSuggestion | None:
        if not self.role_suggestions:
            return None

        return self.role_suggestions[0]

    def to_dict(self) -> dict[str, object]:
        return {
            "suggested_title": self.suggested_title,
            "seniority": self.seniority,
            "extracted_skills": list(
                self.extracted_skills
            ),
            "search_terms": list(self.search_terms),
            "warnings": list(self.warnings),
            "role_suggestions": [
                suggestion.to_dict()
                for suggestion in self.role_suggestions
            ],
        }


@dataclass(slots=True)
class GeneratedProfile:
    """
    Profil temporaire accompagné de ses métadonnées.

    `profile` contient l'objet Profile historique de JobAgent.
    """

    profile: object
    analysis: CareerAnalysis
    selected_role: RoleSuggestion | None
    added_keywords: list[str] = field(
        default_factory=list
    )