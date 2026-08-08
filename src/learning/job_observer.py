from __future__ import annotations

import re
from collections.abc import Iterable

from src.domain import Job
from src.learning.models import LearningObservation


class JobLearningObservationExtractor:
    """
    Produit des observations prudentes depuis les offres.

    Sont observés :
    - les tags transmis par les providers ;
    - les expressions techniques explicites du texte ;
    - les tokens comportant majuscules, chiffres ou
      séparateurs typiques des noms de technologies.

    Ce composant ne décide pas qu'un terme est une
    compétence. Il produit seulement des observations
    soumises au LearningSuggestionDetector.
    """

    WORD_PATTERN = (
        r"(?:\.[A-Za-z][A-Za-z0-9]*|"
        r"[A-Za-zÀ-ÿ0-9+#-]+"
        r"(?:['’][A-Za-zÀ-ÿ0-9+#-]+)*"
        r"(?:\.[A-Za-zÀ-ÿ0-9+#-]+)*)"
    )
    SENTENCE_BOUNDARY_PATTERN = re.compile(
        r"(?:\r?\n){2,}|[;•]+|(?<=[.!?])\s+(?=[A-ZÀ-Ý])"
    )
    CONTEXTUAL_TERM_PATTERN = re.compile(
        rf"""
        \b(?:aptitude|capacité|expérience|expertise|maîtrise|connaissance|compétences?|spécialisation)
        (?:\s+{WORD_PATTERN}){{0,2}}?
        \s+(?:à|dans|en|de|des|du|sur|avec)\s+
        (?P<term>
            {WORD_PATTERN}
            (?:\s+(?!(?:et|ou|avec|dans|pour)\b){WORD_PATTERN}){{0,2}}
        )
        """,
        re.IGNORECASE | re.VERBOSE,
    )
    BUSINESS_GROUP_PATTERN = re.compile(
        rf"""
        \b(?P<term>
            (?:gestion|pilotage|management|encadrement)
            \s+(?:(?:de|des|du)\s+|d['’])
            {WORD_PATTERN}
            (?:\s+(?!(?:et|ou|avec|dans|pour)\b){WORD_PATTERN}){{0,2}}
        )
        """,
        re.IGNORECASE | re.VERBOSE,
    )
    OPTIONAL_COMPLEMENT_PATTERN = re.compile(
        rf"""
        \bet\s+(?:idéalement\s+)?(?:(?:de|des|du)\s+|d['’])
        (?P<term>
            (?:l['’])?{WORD_PATTERN}
            (?:\s+(?!(?:et|ou|avec|dans|pour)\b){WORD_PATTERN}){{0,2}}
        )
        """,
        re.IGNORECASE | re.VERBOSE,
    )
    SOFT_SKILL_PATTERN = re.compile(
        rf"""
        \bvous\s+(?:avez|possédez)\s+(?:un|une)\s+
        (?P<term>{WORD_PATTERN}(?:\s+{WORD_PATTERN}){{0,3}})
        """,
        re.IGNORECASE | re.VERBOSE,
    )
    COORDINATED_NOUN_PATTERN = re.compile(
        rf"\b(?:esprit|capacité)\s+d['’](?P<first>{WORD_PATTERN})"
        rf"\s+et\s+de\s+(?P<second>{WORD_PATTERN})",
        re.IGNORECASE,
    )
    TECH_TERM_PATTERN = re.compile(
        r"""
        (?<![\w.+#'’-])
        (
            (?:
                [A-ZÀ-Ý][a-zà-ÿ]+(?:\s+[A-ZÀ-Ý][A-Za-zÀ-ÿ0-9.+#'’-]+){1,2}
                |
                [A-ZÀ-Ý0-9]{2,}(?:/[A-ZÀ-Ý0-9]+)*
                |
                \.[A-Za-z][A-Za-z0-9]*
                |
                [A-Za-z][A-Za-z0-9]*\.[A-Za-z0-9.]+
                |
                [A-Za-zÀ-ÿ]*[a-zà-ÿ][A-ZÀ-Ý][A-Za-zÀ-ÿ0-9]*
                |
                [A-Za-zÀ-ÿ0-9]*[0-9+#][A-Za-zÀ-ÿ0-9.+#/-]*
            )
        )
        (?![\w+#'’-])
        """,
        re.VERBOSE,
    )

    DEFAULT_STOP_TERMS = {
        "le",
        "la",
        "les",
        "un",
        "une",
        "des",
        "de",
        "du",
        "et",
        "ou",
        "avec",
        "pour",
        "dans",
        "sur",
        "poste",
        "profil",
        "équipe",
        "entreprise",
        "expérience",
        "mission",
        "missions",
        "responsable",
        "candidat",
        "candidate",
        "vous",
        "nous",
        "notre",
        "votre",
        "travail",
        "emploi",
    }
    SOFT_SKILL_MODIFIERS = {
        "bon",
        "bonne",
        "excellent",
        "excellente",
        "fort",
        "forte",
        "grande",
        "très",
    }
    EXPERIENCE_WORDS = {
        "compétence",
        "compétences",
        "connaissance",
        "expérience",
        "expertise",
        "maîtrise",
        "spécialisation",
    }

    def __init__(
        self,
        *,
        stop_terms: Iterable[str] = (),
        context_radius: int = 90,
    ) -> None:
        self.stop_terms = {
            str(value or "").strip().casefold()
            for value in (
                self.DEFAULT_STOP_TERMS
                | set(stop_terms or ())
            )
            if str(value or "").strip()
        }

        self.context_radius = max(
            20,
            int(context_radius),
        )

    def extract(
        self,
        jobs: Iterable[Job],
    ) -> tuple[LearningObservation, ...]:
        observations: list[LearningObservation] = []

        for job in jobs or ():
            if not isinstance(job, Job):
                raise TypeError(
                    "Toutes les offres doivent être "
                    "des instances de Job."
                )

            observations.extend(
                self.extract_job(job)
            )

        return tuple(observations)

    def extract_job(
        self,
        job: Job,
    ) -> tuple[LearningObservation, ...]:
        if not isinstance(job, Job):
            raise TypeError(
                "job doit être une instance de Job."
            )

        observations: list[LearningObservation] = []
        seen: set[str] = set()

        reference_id = str(
            job.external_id
            or job.identity
        )

        source = str(
            job.source
            or "unknown"
        )

        for skill in job.skills or ():
            self._append_observation(
                observations=observations,
                seen=seen,
                term=skill,
                source=source,
                reference_id=reference_id,
                context=job.title,
            )

        for text in (job.title, job.description):
            for segment in self._segments(text):
                for term in self._candidate_terms(segment):
                    self._append_observation(
                        observations=observations,
                        seen=seen,
                        term=term,
                        source=source,
                        reference_id=reference_id,
                        context=segment,
                    )

        return tuple(observations)

    def _candidate_terms(self, segment: str) -> tuple[str, ...]:
        terms: list[str] = []

        for match in self.CONTEXTUAL_TERM_PATTERN.finditer(segment):
            term = self._normalize_contextual_term(match.group("term"))
            if self._is_contextual_candidate(term):
                terms.append(term)

        for match in self.BUSINESS_GROUP_PATTERN.finditer(segment):
            term = self._normalize_contextual_term(match.group("term"))
            if self._is_contextual_candidate(term):
                terms.append(term)

        for match in self.OPTIONAL_COMPLEMENT_PATTERN.finditer(segment):
            term = self._normalize_contextual_term(match.group("term"))
            if self._is_contextual_candidate(term):
                terms.append(term)

        for match in self.SOFT_SKILL_PATTERN.finditer(segment):
            term = self._soft_skill_term(match.group("term"))
            if term and self._is_contextual_candidate(term):
                terms.append(term)

        for match in self.COORDINATED_NOUN_PATTERN.finditer(segment):
            terms.extend(
                term for term in (
                    match.group("first"),
                    match.group("second"),
                )
                if self._is_contextual_candidate(term)
            )

        for match in self.TECH_TERM_PATTERN.finditer(segment):
            term = match.group(1)
            if self._is_candidate(term):
                terms.append(term)

        return tuple(terms)

    @staticmethod
    def _normalize_contextual_term(term: str) -> str:
        cleaned = " ".join(str(term or "").split())
        lowered = cleaned.casefold()

        for prefix in ("l'", "l’", "la ", "le ", "les "):
            if lowered.startswith(prefix):
                return cleaned[len(prefix):]

        return cleaned

    def _soft_skill_term(self, term: str) -> str | None:
        words = " ".join(str(term or "").split()).split()
        normalized_words = [word.casefold() for word in words]

        if any(word in self.EXPERIENCE_WORDS for word in normalized_words):
            return None

        while (
            words
            and words[0].casefold() in self.SOFT_SKILL_MODIFIERS
        ):
            words.pop(0)

        if not words or len(words) > 2:
            return None

        return " ".join(words)

    def _is_contextual_candidate(self, term: str) -> bool:
        cleaned = " ".join(str(term or "").split())
        words = cleaned.casefold().split()
        return bool(
            cleaned
            and words
            and words[0] not in self.stop_terms
            and words[-1] not in self.stop_terms
        )

    @classmethod
    def _segments(cls, value: str) -> tuple[str, ...]:
        return tuple(
            cleaned
            for part in cls.SENTENCE_BOUNDARY_PATTERN.split(
                str(value or "")
            )
            if (cleaned := " ".join(part.split()))
        )

    def _is_candidate(
        self,
        term: str,
    ) -> bool:
        cleaned = " ".join(
            str(term or "").split()
        )

        if len(cleaned) < 2:
            return False

        if cleaned.casefold() in self.stop_terms:
            return False

        words = cleaned.split()

        if all(
            word.casefold() in self.stop_terms
            for word in words
        ):
            return False

        has_technical_signal = any(
            (
                any(character.isdigit() for character in word)
                or any(
                    character in ".+#-"
                    for character in word
                )
                or (
                    len(word) >= 2
                    and word.isupper()
                )
                or (
                    len(word) >= 2
                    and word[0].isupper()
                )
            )
            for word in words
        )

        return has_technical_signal

    @staticmethod
    def _append_observation(
        *,
        observations: list[LearningObservation],
        seen: set[str],
        term: str,
        source: str,
        reference_id: str,
        context: str,
    ) -> None:
        cleaned = " ".join(
            str(term or "").split()
        )

        if not cleaned:
            return

        identity = cleaned.casefold()

        if identity in seen:
            return

        seen.add(identity)

        observations.append(
            LearningObservation(
                term=cleaned,
                source=source,
                reference_id=reference_id,
                context=context,
            )
        )

    def _excerpt(
        self,
        *,
        text: str,
        start: int,
        end: int,
    ) -> str:
        excerpt_start = max(
            0,
            start - self.context_radius,
        )

        excerpt_end = min(
            len(text),
            end + self.context_radius,
        )

        return " ".join(
            text[
                excerpt_start:excerpt_end
            ].split()
        )
