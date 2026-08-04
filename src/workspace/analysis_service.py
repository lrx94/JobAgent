from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from typing import Any

from src.analysis import (
    CandidateAnalyzer,
    ComparativeScoringService,
    ScoreComparison,
    StructuredAnalysis,
)
from src.cvs.profile_cv_service import (
    ProfileCVService,
)
from src.cvs.service import (
    CVService,
)
from src.domain import Job


class WorkspaceAnalysisError(
    RuntimeError
):
    """
    Une analyse structurée du Workspace a échoué.
    """


@dataclass(
    frozen=True,
    slots=True,
)
class WorkspaceCandidateAnalysis:
    """
    Analyse structurée construite depuis le CV principal
    d'un profil utilisateur.
    """

    profile_id: str
    cv_id: str
    analysis: StructuredAnalysis


class WorkspaceAnalysisService:
    """
    Point d'entrée de l'analyse structurée du Workspace.

    Responsabilités :
    - retrouver le CV principal du profil ;
    - analyser ce CV une seule fois ;
    - produire le StructuredAnalysis candidat ;
    - enrichir les offres avec le score structuré.

    Le score historique Job.score n'est jamais remplacé.
    """

    def __init__(
        self,
        *,
        cv_service: CVService,
        association_service: ProfileCVService,
        candidate_analyzer: Any | None = None,
        comparative_scoring_service: Any | None = None,
    ) -> None:
        if not isinstance(
            cv_service,
            CVService,
        ):
            raise TypeError(
                "cv_service doit être un CVService."
            )

        if not isinstance(
            association_service,
            ProfileCVService,
        ):
            raise TypeError(
                "association_service doit être un "
                "ProfileCVService."
            )

        self.cv_service = cv_service
        self.association_service = (
            association_service
        )

        self.candidate_analyzer = (
            candidate_analyzer
            or CandidateAnalyzer()
        )

        self.comparative_scoring_service = (
            comparative_scoring_service
            or ComparativeScoringService()
        )

    @property
    def user_id(self) -> str:
        return self.cv_service.user_id

    def build_candidate_analysis(
        self,
        profile_id: str,
    ) -> WorkspaceCandidateAnalysis | None:
        """
        Construit l'analyse structurée du CV principal.

        Retourne None lorsqu'aucun CV principal n'est
        associé au profil.
        """

        normalized_profile_id = str(
            profile_id or ""
        ).strip()

        if not normalized_profile_id:
            raise WorkspaceAnalysisError(
                "Le profile_id est obligatoire."
            )

        try:
            primary_cv = (
                self.association_service
                .get_primary_cv(
                    normalized_profile_id
                )
            )
        except Exception as error:
            raise WorkspaceAnalysisError(
                "Impossible de retrouver le CV principal."
            ) from error

        if primary_cv is None:
            return None

        try:
            cv_analysis = (
                self.cv_service.analyze(
                    primary_cv.cv_id
                )
            )

            candidate_analysis = (
                self.candidate_analyzer.analyze(
                    cv_analysis=cv_analysis
                )
            )

        except Exception as error:
            raise WorkspaceAnalysisError(
                "Impossible de construire l'analyse "
                "structurée du candidat."
            ) from error

        return WorkspaceCandidateAnalysis(
            profile_id=normalized_profile_id,
            cv_id=primary_cv.cv_id,
            analysis=candidate_analysis,
        )

    def enrich_jobs(
        self,
        *,
        candidate: StructuredAnalysis,
        jobs: Iterable[Job],
    ) -> tuple[ScoreComparison, ...]:
        """
        Ajoute les diagnostics structurés aux offres.

        ComparativeScoringService conserve le score
        historique et écrit uniquement dans :

            job.match_details["structured"]
        """

        if not isinstance(
            candidate,
            StructuredAnalysis,
        ):
            raise TypeError(
                "candidate doit être un "
                "StructuredAnalysis."
            )

        normalized_jobs = self._unique_jobs(
            jobs
        )

        if not normalized_jobs:
            return ()

        try:
            return (
                self.comparative_scoring_service
                .compare(
                    candidate=candidate,
                    jobs=normalized_jobs,
                )
            )
        except Exception as error:
            raise WorkspaceAnalysisError(
                "Impossible d'enrichir les offres avec "
                "le scoring structuré."
            ) from error

    def enrich_profile_jobs(
        self,
        *,
        profile_id: str,
        jobs: Iterable[Job],
    ) -> tuple[ScoreComparison, ...]:
        """
        Méthode pratique exécutant tout le pipeline :

        CV principal
        → analyse candidat
        → enrichissement des offres.
        """

        candidate = (
            self.build_candidate_analysis(
                profile_id
            )
        )

        if candidate is None:
            return ()

        return self.enrich_jobs(
            candidate=candidate.analysis,
            jobs=jobs,
        )

    @staticmethod
    def _unique_jobs(
        jobs: Iterable[Job] | None,
    ) -> tuple[Job, ...]:
        result: list[Job] = []
        seen_objects: set[int] = set()

        for job in jobs or ():
            if not isinstance(
                job,
                Job,
            ):
                raise TypeError(
                    "Toutes les offres doivent être "
                    "des instances de Job."
                )

            object_identity = id(job)

            if object_identity in seen_objects:
                continue

            seen_objects.add(
                object_identity
            )

            result.append(job)

        return tuple(result)