from __future__ import annotations

import hashlib
import re
import unicodedata
from collections import defaultdict
from collections.abc import Iterable
from enum import StrEnum

from src.learning.models import (
    LearningObservation,
    LearningSuggestion,
    SuggestionType,
)


class CandidateKind(StrEnum):
    """Classification explicable d'un terme candidat Learning."""

    SKILL = "skill"
    ROLE = "role"
    HEADER = "header"
    SYNTAX_FRAGMENT = "syntax_fragment"
    VERBAL_MISSION = "verbal_mission"
    GENERIC_TERM = "generic_term"


class LearningSuggestionDetector:
    """
    Agrège des termes observés et propose uniquement
    ceux qui ne figurent pas dans le référentiel connu.

    Les entrées peuvent provenir :
    - d'offres ;
    - de CV ;
    - du Market Analyzer ;
    - d'un futur extracteur de termes candidats.
    """

    URL_OR_EMAIL_PATTERN = re.compile(
        r"(?:https?://|www\.|\b[^\s@]+@[^\s@]+\.[^\s@]+)",
        re.IGNORECASE,
    )
    UUID_PATTERN = re.compile(
        r"\b[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-"
        r"[89ab][0-9a-f]{3}-[0-9a-f]{12}\b",
        re.IGNORECASE,
    )
    LONG_TECH_TOKEN_PATTERN = re.compile(
        r"[A-Za-z0-9+/=:_-]{24,}"
    )
    HEX_HASH_PATTERN = re.compile(
        r"\b[0-9a-f]{24,}\b",
        re.IGNORECASE,
    )
    MINIMUM_CANDIDATE_QUALITY_SCORE = 2
    DOCUMENT_HEADERS = {
        "a propos",
        "competences",
        "competences requises",
        "description du profil",
        "description du poste",
        "missions",
        "profil recherche",
        "qualifications",
        "responsabilites",
        "vos missions",
        "votre profil",
    }
    SUBJECT_PRONOUNS = {
        "elle",
        "elles",
        "il",
        "ils",
        "je",
        "nous",
        "on",
        "tu",
        "vous",
    }
    INCOMPLETE_FINAL_DETERMINERS = {
        "des",
        "du",
        "l",
        "la",
        "le",
        "les",
        "un",
        "une",
    }
    LEADING_FRAGMENT_WORDS = {
        "a",
        "au",
        "aux",
        "chez",
        "dans",
        "de",
        "des",
        "du",
        "la",
        "le",
        "les",
        "par",
        "pour",
        "sur",
    }
    TRAILING_FRAGMENT_WORDS = {
        "a",
        "d",
        "de",
        "des",
        "du",
        "l",
        "la",
        "le",
        "les",
        "qu",
    }
    MISSION_VERBS = {
        "accompagner",
        "assurer",
        "conduire",
        "definir",
        "diffuser",
        "encadrer",
        "garantir",
        "manager",
        "mettre",
        "organiser",
        "participer",
        "piloter",
        "realiser",
        "representer",
        "superviser",
    }
    ROLE_WORDS = {
        "directeur",
        "directrice",
        "responsable",
    }
    GENERIC_ISOLATED_TERMS = {
        "dsi",
        "enfin",
        "information",
        "it",
        "requis",
        "requise",
        "rh",
        "si",
    }

    def __init__(
        self,
        *,
        known_terms: Iterable[str] = (),
        minimum_occurrences: int = 3,
        minimum_sources: int = 1,
        maximum_contexts: int = 5,
    ) -> None:
        self.known_terms = {
            self.normalize_term(value)
            for value in known_terms
            if self.normalize_term(value)
        }

        self.minimum_occurrences = max(
            1,
            int(minimum_occurrences),
        )

        self.minimum_sources = max(
            1,
            int(minimum_sources),
        )

        self.maximum_contexts = max(
            1,
            int(maximum_contexts),
        )

    def detect(
        self,
        observations: Iterable[
            LearningObservation
        ],
    ) -> tuple[LearningSuggestion, ...]:
        grouped: dict[
            str,
            list[LearningObservation],
        ] = defaultdict(list)

        display_terms: dict[str, str] = {}

        for observation in observations or ():
            if not isinstance(
                observation,
                LearningObservation,
            ):
                raise TypeError(
                    "Toutes les observations doivent "
                    "être des LearningObservation."
                )

            normalized = self.normalize_term(
                observation.term
            )

            if not normalized:
                continue

            if not self.is_quality_term(
                observation.term
            ):
                continue

            if normalized in self.known_terms:
                continue

            grouped[normalized].append(
                observation
            )

            display_terms.setdefault(
                normalized,
                observation.term.strip(),
            )

        suggestions: list[
            LearningSuggestion
        ] = []

        for normalized, items in grouped.items():
            sources = sorted(
                {
                    item.source
                    for item in items
                }
            )

            if (
                len(items)
                < self.minimum_occurrences
            ):
                continue

            if (
                len(sources)
                < self.minimum_sources
            ):
                continue

            contexts = self._contexts(items)

            if self.candidate_quality_score(
                display_terms[normalized],
                occurrence_count=len(items),
                context_count=len(contexts),
            ) < self.MINIMUM_CANDIDATE_QUALITY_SCORE:
                continue

            suggestions.append(
                LearningSuggestion(
                    suggestion_id=(
                        self._suggestion_id(
                            normalized
                        )
                    ),
                    observed_term=(
                        display_terms[normalized]
                    ),
                    normalized_term=normalized,
                    suggestion_type=(
                        SuggestionType.SKILL
                    ),
                    occurrence_count=len(items),
                    source_count=len(sources),
                    sources=tuple(sources),
                    contexts=contexts,
                    confidence=self._confidence(
                        occurrence_count=(
                            len(items)
                        ),
                        source_count=(
                            len(sources)
                        ),
                        context_count=(
                            len(contexts)
                        ),
                    ),
                )
            )

        suggestions.sort(
            key=lambda item: (
                -item.confidence,
                -item.occurrence_count,
                item.normalized_term,
            )
        )

        return tuple(suggestions)

    @classmethod
    def is_quality_term(
        cls,
        value: str,
    ) -> bool:
        """Quality Gate statique, déterministe et indépendant du métier."""

        cleaned = " ".join(str(value or "").split())
        if not cleaned or len(cleaned) < 2 or len(cleaned) > 80:
            return False

        if len(cleaned.split()) > 6:
            return False

        if "<" in cleaned or ">" in cleaned:
            return False

        if cls.URL_OR_EMAIL_PATTERN.search(cleaned):
            return False

        if cls.UUID_PATTERN.search(cleaned):
            return False

        if cls.HEX_HASH_PATTERN.search(cleaned):
            return False

        if cls.LONG_TECH_TOKEN_PATTERN.search(cleaned):
            return False

        alphanumeric = sum(character.isalnum() for character in cleaned)
        if alphanumeric == 0:
            return False

        if cleaned.isdecimal():
            return False

        return cls.classify_candidate(cleaned) == CandidateKind.SKILL

    @classmethod
    def classify_candidate(cls, value: str) -> CandidateKind:
        """Classe un terme par sa forme, sans connaissance métier ciblée."""

        cleaned = " ".join(str(value or "").split())
        normalized = cls.normalize_term(cleaned)
        words = normalized.split()

        if normalized in cls.DOCUMENT_HEADERS:
            return CandidateKind.HEADER

        if not words:
            return CandidateKind.SYNTAX_FRAGMENT

        if (
            words[-1] in cls.TRAILING_FRAGMENT_WORDS
            or cleaned.endswith(("'", "’"))
        ):
            return CandidateKind.SYNTAX_FRAGMENT

        if words[0] in cls.LEADING_FRAGMENT_WORDS:
            return CandidateKind.SYNTAX_FRAGMENT

        if (
            len(words) >= 3
            and words[0] in cls.SUBJECT_PRONOUNS
            and words[-1] in cls.INCOMPLETE_FINAL_DETERMINERS
        ):
            return CandidateKind.SYNTAX_FRAGMENT

        if any(word in {"et", "ou"} for word in words[1:-1]):
            return CandidateKind.SYNTAX_FRAGMENT

        if words[0] in cls.MISSION_VERBS:
            return CandidateKind.VERBAL_MISSION

        if words[0] in cls.ROLE_WORDS:
            return CandidateKind.ROLE

        if normalized in cls.GENERIC_ISOLATED_TERMS:
            return CandidateKind.GENERIC_TERM

        return CandidateKind.SKILL

    @classmethod
    def candidate_quality_score(
        cls,
        value: str,
        *,
        occurrence_count: int,
        context_count: int,
    ) -> int:
        """Score déterministe fondé sur la forme et les preuves disponibles."""

        if not cls.is_quality_term(value):
            return 0

        cleaned = " ".join(str(value or "").split())
        score = 1

        if cls._is_plausible_acronym(cleaned):
            score += 1

        if occurrence_count >= 2:
            score += 1

        if context_count >= 2:
            score += 1

        return score

    @staticmethod
    def _is_plausible_acronym(value: str) -> bool:
        compact = value.replace("/", "").replace(".", "")
        return (
            2 <= len(compact) <= 10
            and any(character.isalpha() for character in compact)
            and compact.upper() == compact
        )

    def with_known_terms(
        self,
        values: Iterable[str],
    ) -> LearningSuggestionDetector:
        return LearningSuggestionDetector(
            known_terms=(
                self.known_terms
                | {
                    self.normalize_term(value)
                    for value in values
                    if self.normalize_term(value)
                }
            ),
            minimum_occurrences=(
                self.minimum_occurrences
            ),
            minimum_sources=(
                self.minimum_sources
            ),
            maximum_contexts=(
                self.maximum_contexts
            ),
        )

    def _contexts(
        self,
        observations: list[
            LearningObservation
        ],
    ) -> tuple[str, ...]:
        result: list[str] = []
        seen: set[str] = set()

        for observation in observations:
            context = observation.context.strip()

            if not context:
                continue

            identity = context.casefold()

            if identity in seen:
                continue

            seen.add(identity)
            result.append(context)

            if (
                len(result)
                >= self.maximum_contexts
            ):
                break

        return tuple(result)

    @staticmethod
    def _confidence(
        *,
        occurrence_count: int,
        source_count: int,
        context_count: int,
    ) -> float:
        """
        Heuristique volontairement prudente.

        Une fréquence élevée, plusieurs sources et
        plusieurs contextes renforcent la suggestion.
        """

        occurrence_score = min(
            occurrence_count / 20,
            1.0,
        )

        source_score = min(
            source_count / 3,
            1.0,
        )

        context_score = min(
            context_count / 5,
            1.0,
        )

        confidence = (
            occurrence_score * 0.55
            + source_score * 0.30
            + context_score * 0.15
        )

        return round(
            confidence,
            3,
        )

    @classmethod
    def normalize_term(
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

        punctuation_normalized = re.sub(
            r"[-_/|]+",
            " ",
            without_accents,
        )

        punctuation_normalized = re.sub(
            r"[^\w\s.+#]",
            " ",
            punctuation_normalized,
        )

        spaces_normalized = re.sub(
            r"\s+",
            " ",
            punctuation_normalized,
        )

        return (
            spaces_normalized
            .strip()
            .casefold()
        )

    @staticmethod
    def _suggestion_id(
        normalized_term: str,
    ) -> str:
        digest = hashlib.sha256(
            normalized_term.encode(
                "utf-8"
            )
        ).hexdigest()[:16]

        return f"skill-{digest}"
