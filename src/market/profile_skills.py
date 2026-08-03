from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable


@dataclass(
    frozen=True,
    slots=True,
)
class MarketProfileSkills:
    """
    Compétences utilisées pour comparer le candidat
    avec le marché observé.

    Sources possibles :
    - cv : compétences du CV principal analysé ;
    - keywords : repli sur les mots-clés du profil ;
    - none : aucune compétence disponible.
    """

    skills: tuple[str, ...]
    source: str
    cv_id: str | None = None
    warnings: tuple[str, ...] = ()

    @property
    def source_label(self) -> str:
        if self.source == "cv":
            return "CV principal analysé"

        if self.source == "keywords":
            return "Mots-clés du profil (repli)"

        return "Aucune source disponible"


class MarketProfileSkillResolver:
    """
    Sélectionne les compétences représentant réellement
    le candidat pour l'analyse du marché.

    La priorité est toujours donnée au CV principal.

    Les mots-clés ne sont utilisés qu'en l'absence de CV
    exploitable, afin de ne pas mélanger :
    - critères de recherche ;
    - compétences du candidat.
    """

    def __init__(
        self,
        cv_service: Any,
    ) -> None:
        if cv_service is None:
            raise TypeError(
                "cv_service est obligatoire."
            )

        self.cv_service = cv_service

    def resolve(
        self,
        *,
        primary_cv_id: str | None,
        fallback_keywords: Iterable[str] | None,
    ) -> MarketProfileSkills:
        normalized_cv_id = str(
            primary_cv_id or ""
        ).strip()

        if normalized_cv_id:
            try:
                analysis = (
                    self.cv_service.analyze(
                        normalized_cv_id
                    )
                )

                skills = self._normalize(
                    getattr(
                        analysis,
                        "skills",
                        (),
                    )
                )

            except Exception as error:
                fallback = self._normalize(
                    fallback_keywords
                )

                return MarketProfileSkills(
                    skills=fallback,
                    source=(
                        "keywords"
                        if fallback
                        else "none"
                    ),
                    cv_id=normalized_cv_id,
                    warnings=(
                        "Le CV principal n'a pas pu être "
                        "analysé pour le portrait du marché : "
                        f"{error}",
                    ),
                )

            if skills:
                return MarketProfileSkills(
                    skills=skills,
                    source="cv",
                    cv_id=normalized_cv_id,
                )

            fallback = self._normalize(
                fallback_keywords
            )

            return MarketProfileSkills(
                skills=fallback,
                source=(
                    "keywords"
                    if fallback
                    else "none"
                ),
                cv_id=normalized_cv_id,
                warnings=(
                    "Aucune compétence n'a été détectée "
                    "dans le CV principal. Les mots-clés "
                    "du profil sont utilisés en repli."
                    if fallback
                    else
                    "Aucune compétence n'a été détectée "
                    "dans le CV principal.",
                ),
            )

        fallback = self._normalize(
            fallback_keywords
        )

        if fallback:
            return MarketProfileSkills(
                skills=fallback,
                source="keywords",
                warnings=(
                    "Aucun CV principal n'est associé. "
                    "La comparaison utilise provisoirement "
                    "les mots-clés du profil.",
                ),
            )

        return MarketProfileSkills(
            skills=(),
            source="none",
            warnings=(
                "Aucun CV principal ni aucune compétence "
                "de repli ne sont disponibles.",
            ),
        )

    @staticmethod
    def _normalize(
        values: Iterable[str] | None,
    ) -> tuple[str, ...]:
        result: list[str] = []
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
            result.append(cleaned)

        return tuple(result)