from __future__ import annotations

import hashlib
import re
import unicodedata
from collections import defaultdict
from collections.abc import Iterable

from src.learning.models import (
    LearningObservation,
    LearningSuggestion,
    SuggestionType,
)
from src.learning.origin import (
    LearningObservationOrigin,
)
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
    BLOCKED_PHRASES = {
        "description du poste",
        "profil recherche",
        "companies can search",
        "avoid spam applicants",
        "mention the word",
        "and tag",
        "un cet",
        "une mutuelle sante",
        "cheques cadeaux",
    }

    BLOCKED_FRAGMENTS = {
        "spam applicants",
        "companies can",
        "mention the word",
        "and tag",
        "mutuelle",
        "cheques cadeaux",
        "epargne a",
        "indemnite",
    }

    INCOMPLETE_ENDINGS = {
        "d",
        "l",
        "de",
        "du",
        "des",
        "and",
        "of",
        "the",
    }

    URL_PATTERN = re.compile(
        r"""
        (
            https?://
            |
            www\.
            |
            \b
            [a-z0-9.-]+
            \.
            (?:com|fr|io|org|net|ai)
            \b
        )
        """,
        re.IGNORECASE | re.VERBOSE,
    )

    RANDOM_TOKEN_PATTERN = re.compile(
        r"""
        \b
        (?=[A-Za-z0-9]*[A-Za-z])
        (?=[A-Za-z0-9]*[0-9])
        [A-Za-z0-9]{16,}
        \b
        """,
        re.VERBOSE,
    )

    def __init__(
        self,
        *,
        known_terms: Iterable[str] = (),
        minimum_occurrences: int = 3,
        minimum_sources: int = 1,
        maximum_contexts: int = 5,
        allow_raw_text_only: bool = False,
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
        self.allow_raw_text_only = bool(
            allow_raw_text_only
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

            if not self._is_quality_candidate(
                raw_term=observation.term,
                normalized_term=normalized,
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
            origins = tuple(
                sorted(
                    {
                        item.origin
                        for item in items
                    },
                    key=lambda origin: (
                        origin.value
                    ),
                )
            )

            if (
                not self.allow_raw_text_only
                and set(origins)
                == {
                    LearningObservationOrigin
                    .RAW_TEXT_FALLBACK
                }
            ):
                continue

            contexts = self._contexts(items)

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
                        occurrence_count=len(items),
                        source_count=len(sources),
                        context_count=len(contexts),
                    ),
                    origins=origins,
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
            allow_raw_text_only=(
                self.allow_raw_text_only
            ),
        )

    @classmethod
    def _is_quality_candidate(
        cls,
        *,
        raw_term: str,
        normalized_term: str,
    ) -> bool:
        raw_value = " ".join(
            str(raw_term or "").split()
        )

        normalized_value = " ".join(
            str(normalized_term or "").split()
        )

        if not raw_value or not normalized_value:
            return False

        if normalized_value in cls.BLOCKED_PHRASES:
            return False

        if any(
            fragment in normalized_value
            for fragment in cls.BLOCKED_FRAGMENTS
        ):
            return False

        words = normalized_value.split()

        if len(words) > 4:
            return False

        if words[-1] in cls.INCOMPLETE_ENDINGS:
            return False

        if any(
            marker in raw_value
            for marker in (
                "€",
                "%",
                "$",
            )
        ):
            return False

        if cls.URL_PATTERN.search(
            raw_value
        ):
            return False

        if cls.RANDOM_TOKEN_PATTERN.search(
            raw_value
        ):
            return False

        return True

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