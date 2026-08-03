from __future__ import annotations

import re
import unicodedata
from collections import Counter

from src.domain import Skill

from .skill_taxonomy import (
    SKILL_TAXONOMY,
    UNKNOWN_CATEGORY,
    get_category_for_exact_skill,
    normalize_taxonomy_value,
)


class SkillClassifier:
    """
    Classe les compétences à partir de la taxonomie sémantique.

    Le classifieur applique deux niveaux de recherche :

    1. correspondance exacte ;
    2. recherche de termes connus dans une phrase complète.

    Lorsqu'une phrase contient plusieurs catégories, celle qui possède
    le plus grand nombre de correspondances est sélectionnée.
    """

    DEFAULT_CONFIDENCE = 1.0
    UNKNOWN_CONFIDENCE = 0.0

    def classify(self, skill: Skill) -> Skill:
        """
        Enrichit directement un objet Skill.

        L'objet reçu est retourné afin de permettre une utilisation
        simple dans une compréhension de liste ou un pipeline.
        """

        category, confidence = self.classify_name(skill.name)

        skill.category = category
        skill.confidence = confidence

        return skill

    def classify_many(self, skills: list[Skill]) -> list[Skill]:
        """
        Classe une collection de compétences.
        """

        return [
            self.classify(skill)
            for skill in skills
        ]

    def classify_name(self, skill_name: str) -> tuple[str, float]:
        """
        Retourne la catégorie et le niveau de confiance d'un texte.

        Une correspondance exacte obtient une confiance de 1.0.

        Pour une phrase contenant plusieurs termes, la confiance
        correspond à la proportion des correspondances appartenant
        à la catégorie retenue.

        Exemple :
            "Azure et Kubernetes"

            Cloud  : Azure
            DevOps : Kubernetes

            Une égalité est résolue selon l'ordre de la taxonomie.
            Confiance : 1 / 2 = 0.5
        """

        normalized_name = normalize_taxonomy_value(skill_name)

        if not normalized_name:
            return UNKNOWN_CATEGORY, self.UNKNOWN_CONFIDENCE

        exact_category = get_category_for_exact_skill(normalized_name)

        if exact_category != UNKNOWN_CATEGORY:
            return exact_category, self.DEFAULT_CONFIDENCE

        matches = self._find_category_matches(normalized_name)

        if not matches:
            return UNKNOWN_CATEGORY, self.UNKNOWN_CONFIDENCE

        category_counts = Counter(matches)
        selected_category = self._select_category(category_counts)

        selected_count = category_counts[selected_category]
        total_count = sum(category_counts.values())

        confidence = selected_count / total_count

        return selected_category, confidence

    def _find_category_matches(self, normalized_text: str) -> list[str]:
        """
        Recherche les termes de la taxonomie présents dans le texte.

        Une catégorie est ajoutée une fois par terme reconnu.
        """

        matches: list[str] = []

        normalized_without_accents = self._remove_accents(normalized_text)

        for category, known_skills in SKILL_TAXONOMY.items():
            for known_skill in known_skills:
                if self._contains_term(
                    normalized_text=normalized_text,
                    normalized_without_accents=normalized_without_accents,
                    term=known_skill,
                ):
                    matches.append(category)

        return matches

    def _select_category(
        self,
        category_counts: Counter[str],
    ) -> str:
        """
        Sélectionne la catégorie ayant le plus grand nombre de résultats.

        En cas d'égalité, l'ordre de SKILL_TAXONOMY sert de priorité
        déterministe.
        """

        highest_count = max(category_counts.values())

        for category in SKILL_TAXONOMY:
            if category_counts.get(category, 0) == highest_count:
                return category

        return UNKNOWN_CATEGORY

    def _contains_term(
        self,
        normalized_text: str,
        normalized_without_accents: str,
        term: str,
    ) -> bool:
        """
        Vérifie la présence d'un terme complet dans un texte.

        Les limites empêchent par exemple :
            "go" de correspondre à "gouvernance"
            "c" de correspondre à "cloud"
            "ia" de correspondre à "social"
        """

        normalized_term = normalize_taxonomy_value(term)
        term_without_accents = self._remove_accents(normalized_term)

        return (
            self._matches_complete_term(
                normalized_text,
                normalized_term,
            )
            or self._matches_complete_term(
                normalized_without_accents,
                term_without_accents,
            )
        )

    def _matches_complete_term(
        self,
        text: str,
        term: str,
    ) -> bool:
        """
        Recherche un terme avec des limites alphanumériques.

        Cette stratégie conserve la compatibilité avec les termes
        techniques tels que :
            C++
            C#
            CI/CD
            .NET
        """

        if not term:
            return False

        pattern = (
            rf"(?<![a-z0-9])"
            rf"{re.escape(term)}"
            rf"(?![a-z0-9])"
        )

        return re.search(pattern, text) is not None

    def _remove_accents(self, value: str) -> str:
        """
        Retire les accents afin de tolérer les différences d'encodage
        ou de saisie entre le CV et la taxonomie.
        """

        decomposed = unicodedata.normalize("NFKD", value)

        return "".join(
            character
            for character in decomposed
            if not unicodedata.combining(character)
        )