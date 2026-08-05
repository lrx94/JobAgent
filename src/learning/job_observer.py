from __future__ import annotations

import re
from collections.abc import Iterable

from src.domain import Job
from src.learning.models import LearningObservation
from src.analysis import JobAnalyzer

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

    TECH_TERM_PATTERN = re.compile(
        r"""
        (?<![\w.+#-])
        (
            [A-Za-zÀ-ÿ][A-Za-zÀ-ÿ0-9.+#-]*
            (?:
                \s+
                [A-Za-zÀ-ÿ0-9][A-Za-zÀ-ÿ0-9.+#-]*
            ){0,2}
        )
        (?![\w.+#-])
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

    def __init__(
        self,
        *,
        analyzer: JobAnalyzer | None = None,
        stop_terms: Iterable[str] = (),
        context_radius: int = 90,
        raw_text_fallback_enabled: bool = False,
    ) -> None:
        self.analyzer = (
            analyzer
            or JobAnalyzer()
        )

        self.raw_text_fallback_enabled = bool(
            raw_text_fallback_enabled
        )

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

        analysis = self.analyzer.analyze_job(
            job
        )
        
        structured_terms_list: list[str] = []
        structured_terms_seen: set[str] = set()

        for term in (
            *analysis.hard_skills,
            *analysis.certifications,
        ):
            cleaned = " ".join(
                str(term or "").split()
            )

            if not cleaned:
                continue

            identity = cleaned.casefold()

            if identity in structured_terms_seen:
                continue

            structured_terms_seen.add(identity)
            structured_terms_list.append(cleaned)

        structured_terms = tuple(
            structured_terms_list
        )

        for term in structured_terms:
            self._append_observation(
                observations=observations,
                seen=seen,
                term=term,
                source=source,
                reference_id=reference_id,
                context=job.title,
            )

        
        # Le texte brut n'est utilisé qu'en dernier recours.
        if (
            not structured_terms
            and self.raw_text_fallback_enabled
        ):
            text = "\n".join(
                value
                for value in (
                    job.title,
                    job.description,
                )
                if str(value or "").strip()
            )

            for match in (
                self.TECH_TERM_PATTERN
                .finditer(text)
            ):
                term = match.group(1).strip()

                if not self._is_candidate(term):
                    continue

                context = self._excerpt(
                    text=text,
                    start=match.start(),
                    end=match.end(),
                )

                self._append_observation(
                    observations=observations,
                    seen=seen,
                    term=term,
                    source=source,
                    reference_id=reference_id,
                    context=context,
                )

            

        return tuple(observations)

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