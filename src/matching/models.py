from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class SemanticMatch:
    """
    Décrit un rapprochement non exact entre une compétence du profil
    et une compétence détectée dans l'offre.

    Attributes:
        profile_skill:
            Compétence demandée par le profil.

        job_skill:
            Compétence détectée dans l'offre.

        category:
            Catégorie sémantique commune lorsqu'elle existe.

        reason:
            Origine du rapprochement :
            - same_category ;
            - skill_graph.

        weight:
            Poids utilisé dans le calcul du score.

        confidence:
            Niveau de confiance produit par la couche sémantique.
    """

    profile_skill: str
    job_skill: str
    category: str
    reason: str
    weight: float
    confidence: float

    def __post_init__(self) -> None:
        if not self.profile_skill.strip():
            raise ValueError(
                "profile_skill ne peut pas être vide."
            )

        if not self.job_skill.strip():
            raise ValueError(
                "job_skill ne peut pas être vide."
            )

        if not 0.0 <= self.weight <= 1.0:
            raise ValueError(
                "weight doit être compris entre 0.0 et 1.0."
            )

        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError(
                "confidence doit être comprise entre 0.0 et 1.0."
            )


@dataclass
class MatchResult:
    """
    Résultat complet du matching entre un profil et une offre.

    `matched_skills` est conservé pour assurer la compatibilité
    avec les services et composants UI existants.
    """

    score: int
    matched_skills: list[str] = field(default_factory=list)
    semantic_matches: list[SemanticMatch] = field(
        default_factory=list
    )
    missing_skills: list[str] = field(default_factory=list)
    details: dict[str, Any] = field(default_factory=dict)

    @property
    def exact_matches(self) -> list[str]:
        """
        Alias explicite de matched_skills.

        Permet au nouveau moteur d'utiliser le vocabulaire
        `exact_matches` sans casser l'ancien code.
        """

        return self.matched_skills

    @property
    def semantic_weight(self) -> float:
        """
        Retourne la somme des poids des rapprochements sémantiques.
        """

        return sum(
            match.weight
            for match in self.semantic_matches
        )

    @property
    def total_skill_weight(self) -> float:
        """
        Retourne le nombre pondéré total de compétences reconnues.
        """

        return len(self.matched_skills) + self.semantic_weight