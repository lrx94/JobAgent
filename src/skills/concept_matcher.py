from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from typing import Iterable

from src.skills.concepts import (
    BUSINESS_CONCEPTS,
    BusinessConcept,
)


@dataclass(
    frozen=True,
    slots=True,
)
class ConceptMatch:
    concept_id: str
    label: str
    matched_aliases: tuple[str, ...]
    confidence: float

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "confidence",
            max(
                0.0,
                min(
                    float(self.confidence),
                    1.0,
                ),
            ),
        )


class ConceptMatcher:
    """
    Détecte des concepts métier canoniques à partir
    de formulations présentes dans les CV et annonces.

    Le matcher est :
    - insensible à la casse ;
    - insensible aux accents ;
    - indépendant de Streamlit ;
    - partagé par CandidateAnalyzer et JobAnalyzer.
    """

    def __init__(
        self,
        concepts: Iterable[
            BusinessConcept
        ] | None = None,
    ) -> None:
        self.concepts = tuple(
            concepts
            if concepts is not None
            else BUSINESS_CONCEPTS
        )

        for concept in self.concepts:
            if not isinstance(
                concept,
                BusinessConcept,
            ):
                raise TypeError(
                    "Tous les concepts doivent être des "
                    "BusinessConcept."
                )

    def match(
        self,
        text: str,
    ) -> tuple[ConceptMatch, ...]:
        normalized_text = self.normalize_text(
            text
        )

        if not normalized_text:
            return ()

        result: list[ConceptMatch] = []

        for concept in self.concepts:
            matched_aliases = tuple(
                alias
                for alias in concept.aliases
                if self._contains_alias(
                    normalized_text=normalized_text,
                    alias=alias,
                )
            )

            if (
                len(matched_aliases)
                < concept.minimum_alias_matches
            ):
                continue

            confidence = self._confidence(
                matched_aliases
            )

            result.append(
                ConceptMatch(
                    concept_id=concept.concept_id,
                    label=concept.label,
                    matched_aliases=matched_aliases,
                    confidence=confidence,
                )
            )

        return tuple(result)

    def extract_labels(
        self,
        text: str,
    ) -> tuple[str, ...]:
        return tuple(
            item.label
            for item in self.match(text)
        )

    @classmethod
    def normalize_text(
        cls,
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

        normalized_punctuation = re.sub(
            r"[-_/|]+",
            " ",
            without_accents,
        )

        normalized_spaces = re.sub(
            r"\s+",
            " ",
            normalized_punctuation,
        )

        return normalized_spaces.strip().casefold()

    @classmethod
    def _contains_alias(
        cls,
        *,
        normalized_text: str,
        alias: str,
    ) -> bool:
        normalized_alias = cls.normalize_text(
            alias
        )

        if not normalized_alias:
            return False

        pattern = (
            r"(?<!\w)"
            + re.escape(normalized_alias)
            + r"(?!\w)"
        )

        return bool(
            re.search(
                pattern,
                normalized_text,
            )
        )

    @staticmethod
    def _confidence(
        matched_aliases: tuple[str, ...],
    ) -> float:
        if not matched_aliases:
            return 0.0

        longest_alias = max(
            len(alias.split())
            for alias in matched_aliases
        )

        if len(matched_aliases) >= 2:
            return 1.0

        if longest_alias >= 3:
            return 0.95

        if longest_alias == 2:
            return 0.90

        return 0.80