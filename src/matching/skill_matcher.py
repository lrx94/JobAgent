from __future__ import annotations

import re
import unicodedata
from typing import Iterable

from src.ai import SemanticMatcher
from src.ai.skill_normalizer import SkillNormalizer

from .models import SemanticMatch
from .skill_dictionary import SKILL_ALIASES
from .skill_taxonomy import (
    SKILL_TAXONOMY,
    UNKNOWN_CATEGORY,
    get_category_for_exact_skill,
    normalize_taxonomy_value,
)


class SkillMatcher:
    """
    Compare les compétences d'un profil avec le texte d'une offre.

    Ordre de recherche :

    1. compétence exacte ou alias ;
    2. compétence appartenant à la même catégorie ;
    3. compétence liée dans SKILL_GRAPH ;
    4. compétence absente.

    Une compétence de l'offre ne peut être consommée qu'une seule fois
    par le processus de matching.
    """

    SAME_CATEGORY_WEIGHT = 0.70
    SKILL_GRAPH_WEIGHT = 0.55
    MINIMUM_GRAPH_CONFIDENCE = 0.50

    def match(
        self,
        profile_skills: Iterable[str],
        text: str,
    ) -> tuple[
        list[str],
        list[SemanticMatch],
        list[str],
    ]:
        """
        Retourne :

        - les correspondances exactes ou par alias ;
        - les correspondances sémantiques ;
        - les compétences absentes.
        """

        normalized_text = self._normalize_text(text)

        matched: list[str] = []
        semantic_matches: list[SemanticMatch] = []
        missing: list[str] = []

        used_job_skills: set[str] = set()

        for raw_skill in profile_skills:
            canonical = SkillNormalizer.normalize(raw_skill)

            if not canonical:
                continue

            exact_job_skill = self._find_exact_or_alias_match(
                canonical=canonical,
                normalized_text=normalized_text,
                used_job_skills=used_job_skills,
            )

            if exact_job_skill is not None:
                matched.append(canonical)
                used_job_skills.add(
                    normalize_taxonomy_value(exact_job_skill)
                )
                continue

            category_match = self._find_category_match(
                canonical=canonical,
                normalized_text=normalized_text,
                used_job_skills=used_job_skills,
            )

            if category_match is not None:
                semantic_matches.append(category_match)
                used_job_skills.add(
                    normalize_taxonomy_value(
                        category_match.job_skill
                    )
                )
                continue

            graph_match = self._find_graph_match(
                canonical=canonical,
                normalized_text=normalized_text,
                used_job_skills=used_job_skills,
            )

            if graph_match is not None:
                semantic_matches.append(graph_match)
                used_job_skills.add(
                    normalize_taxonomy_value(
                        graph_match.job_skill
                    )
                )
                continue

            missing.append(canonical)

        return matched, semantic_matches, missing

    def _find_exact_or_alias_match(
        self,
        canonical: str,
        normalized_text: str,
        used_job_skills: set[str],
    ) -> str | None:
        """
        Recherche la compétence canonique ou l'un de ses alias.
        """

        aliases = SKILL_ALIASES.get(
            canonical,
            [canonical],
        )

        candidates = [canonical, *aliases]

        for candidate in self._deduplicate(candidates):
            normalized_candidate = normalize_taxonomy_value(
                candidate
            )

            if normalized_candidate in used_job_skills:
                continue

            if self._contains_term(
                normalized_text,
                normalized_candidate,
            ):
                return candidate

        return None

    def _find_category_match(
        self,
        canonical: str,
        normalized_text: str,
        used_job_skills: set[str],
    ) -> SemanticMatch | None:
        """
        Recherche dans l'offre une compétence appartenant à la même
        catégorie que la compétence du profil.
        """

        category = get_category_for_exact_skill(canonical)

        if category == UNKNOWN_CATEGORY:
            return None

        known_skills = SKILL_TAXONOMY.get(
            category,
            frozenset(),
        )

        normalized_canonical = normalize_taxonomy_value(canonical)

        for job_skill in sorted(
            known_skills,
            key=lambda value: (-len(value), value.casefold()),
        ):
            normalized_job_skill = normalize_taxonomy_value(
                job_skill
            )

            if normalized_job_skill == normalized_canonical:
                continue

            if normalized_job_skill in used_job_skills:
                continue

            if not self._contains_term(
                normalized_text,
                normalized_job_skill,
            ):
                continue

            return SemanticMatch(
                profile_skill=canonical,
                job_skill=job_skill,
                category=category,
                reason="same_category",
                weight=self.SAME_CATEGORY_WEIGHT,
                confidence=1.0,
            )

        return None

    def _find_graph_match(
        self,
        canonical: str,
        normalized_text: str,
        used_job_skills: set[str],
    ) -> SemanticMatch | None:
        """
        Recherche une compétence liée dans le graphe historique.
        """

        related_skills = self._get_related_skills(canonical)

        best_match: SemanticMatch | None = None

        for candidate in related_skills:
            normalized_candidate = normalize_taxonomy_value(
                candidate
            )

            if normalized_candidate in used_job_skills:
                continue

            if not self._contains_term(
                normalized_text,
                normalized_candidate,
            ):
                continue

            confidence = SemanticMatcher.proximity(
                canonical,
                candidate,
            )

            if confidence < self.MINIMUM_GRAPH_CONFIDENCE:
                continue

            category = get_category_for_exact_skill(candidate)

            current_match = SemanticMatch(
                profile_skill=canonical,
                job_skill=candidate,
                category=category,
                reason="skill_graph",
                weight=self.SKILL_GRAPH_WEIGHT,
                confidence=confidence,
            )

            if (
                best_match is None
                or current_match.confidence
                > best_match.confidence
            ):
                best_match = current_match

        return best_match

    def _get_related_skills(
        self,
        canonical: str,
    ) -> list[str]:
        """
        Charge les relations historiques sans rendre le moteur
        dépendant de la présence du graphe.
        """

        try:
            from src.ai.skill_graph import SKILL_GRAPH

            graph_entry = SKILL_GRAPH.get(
                canonical,
                {},
            )

            related = graph_entry.get(
                "related",
                [],
            )

            return list(related)

        except (ImportError, AttributeError, TypeError):
            return []

    def _contains_term(
        self,
        normalized_text: str,
        normalized_term: str,
    ) -> bool:
        """
        Recherche un terme complet en évitant les faux positifs.

        Exemples évités :
            go dans gouvernance ;
            ia dans social ;
            c dans cloud.
        """

        if not normalized_term:
            return False

        text_without_accents = self._remove_accents(
            normalized_text
        )
        term_without_accents = self._remove_accents(
            normalized_term
        )

        return (
            self._matches_complete_term(
                normalized_text,
                normalized_term,
            )
            or self._matches_complete_term(
                text_without_accents,
                term_without_accents,
            )
        )

    def _matches_complete_term(
        self,
        text: str,
        term: str,
    ) -> bool:
        """
        Recherche le terme avec des limites alphanumériques.

        Cette expression reste compatible avec :
            C++
            C#
            .NET
            CI/CD
        """

        pattern = (
            rf"(?<![a-z0-9])"
            rf"{re.escape(term)}"
            rf"(?![a-z0-9])"
        )

        return re.search(pattern, text) is not None

    def _normalize_text(self, value: str) -> str:
        """
        Normalise légèrement le texte de l'offre.
        """

        return normalize_taxonomy_value(value or "")

    def _remove_accents(self, value: str) -> str:
        """
        Retire les accents pour tolérer les variations de saisie.
        """

        decomposed = unicodedata.normalize(
            "NFKD",
            value,
        )

        return "".join(
            character
            for character in decomposed
            if not unicodedata.combining(character)
        )

    def _deduplicate(
        self,
        values: Iterable[str],
    ) -> list[str]:
        """
        Supprime les doublons en conservant l'ordre.
        """

        result: list[str] = []
        seen: set[str] = set()

        for value in values:
            normalized = normalize_taxonomy_value(value)

            if not normalized or normalized in seen:
                continue

            seen.add(normalized)
            result.append(value)

        return result