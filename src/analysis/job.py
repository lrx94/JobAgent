from __future__ import annotations

from typing import Any

from src.ai.skill_extractor import (
    SkillExtractor,
)
from src.analysis.candidate import (
    CandidateAnalyzer,
)
from src.analysis.models import (
    StructuredAnalysis,
)
from src.career.role_detector import (
    RoleDetector,
)
from src.domain import Job


class JobAnalyzer(
    CandidateAnalyzer
):
    """
    Analyse structurellement une annonce canonique.

    Réutilise les règles du CandidateAnalyzer pour :
    - l'expérience ;
    - le management ;
    - les soft skills ;
    - les certifications ;
    - les langues ;
    - la normalisation textuelle.

    Les hard skills restent extraites par le
    SkillExtractor central.
    """

    REQUIRED_MARKERS = (
        "obligatoire",
        "indispensable",
        "impératif",
        "imperatif",
        "exigé",
        "exige",
        "requis",
        "requise",
        "minimum",
        "au moins",
        "vous justifiez",
        "vous disposez",
    )

    def __init__(
        self,
        *,
        skill_extractor: Any | None = None,
        role_detector: RoleDetector | None = None,
    ) -> None:
        super().__init__(
            role_detector=role_detector
        )

        self.skill_extractor = (
            skill_extractor
            or SkillExtractor()
        )

    def analyze_job(
        self,
        job: Job,
    ) -> StructuredAnalysis:
        if not isinstance(
            job,
            Job,
        ):
            raise TypeError(
                "job doit être une instance de Job."
            )

        text = self._build_job_text(
            job
        )

        extracted_skills = (
            self.skill_extractor.extract(
                text
            )
        )

        hard_skills = self._merge_skills(
            extracted_skills,
            job.skills,
        )

        experience = self._extract_experience(
            text,
            source="job",
            required=True,
        )

        management = self._extract_management(
            text,
            source="job",
        )

        soft_skills = (
            self._extract_catalog_values(
                text=text,
                catalog=self.SOFT_SKILLS,
            )
        )

        certifications = (
            self._extract_catalog_values(
                text=text,
                catalog=self.CERTIFICATIONS,
            )
        )

        languages = (
            self._extract_catalog_values(
                text=text,
                catalog=self.LANGUAGES,
            )
        )

        evidence = self._collect_evidence(
            experience=experience,
            management=management,
        )

        warnings: list[str] = []

        if not hard_skills:
            warnings.append(
                "Aucune compétence technique "
                "n'a été détectée dans l'annonce."
            )

        if not experience:
            warnings.append(
                "Aucune durée d'expérience explicite "
                "n'a été détectée dans l'annonce."
            )

        return StructuredAnalysis(
            hard_skills=hard_skills,
            soft_skills=soft_skills,
            seniority=(
                self.role_detector
                .detect_seniority(text)
            ),
            experience=experience,
            management=management,
            certifications=certifications,
            languages=languages,
            evidence=evidence,
            warnings=tuple(warnings),
        )

    @staticmethod
    def _build_job_text(
        job: Job,
    ) -> str:
        return "\n".join(
            value
            for value in (
                job.title,
                job.description,
                " ".join(
                    job.skills
                    or []
                ),
                job.experience_level or "",
                job.contract_type or "",
            )
            if str(value or "").strip()
        )

    @staticmethod
    def _merge_skills(
        *collections,
    ) -> tuple[str, ...]:
        result: list[str] = []
        seen: set[str] = set()

        for collection in collections:
            for value in collection or ():
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