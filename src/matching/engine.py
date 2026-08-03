from __future__ import annotations

from .models import MatchResult
from .scorer import Scorer
from .skill_matcher import SkillMatcher


class MatchingEngine:
    """
    Orchestre le matching des compétences et le calcul du score global.
    """

    def __init__(self) -> None:
        self.matcher = SkillMatcher()
        self.scorer = Scorer()

    def match(
        self,
        profile,
        job,
    ) -> MatchResult:
        """
        Compare un profil à une offre et retourne un résultat
        détaillé et explicable.
        """

        profile_skills = list(
            getattr(profile, "keywords", []) or []
        )

        job_text = self._build_job_text(job)

        (
            matched,
            semantic_matches,
            missing,
        ) = self.matcher.match(
            profile_skills,
            job_text,
        )

        skill_score = self.scorer.semantic_skill_score(
            exact_matches=matched,
            semantic_matches=semantic_matches,
            total=len(profile_skills),
        )

        location_score = self.scorer.location_score(
            profile,
            job,
        )

        remote_score = self.scorer.remote_score(
            profile,
            job,
        )

        salary_score = self.scorer.salary_score(
            profile,
            job,
        )

        global_score = self.scorer.global_score(
            skill=skill_score,
            location=location_score,
            remote=remote_score,
            salary=salary_score,
        )

        return MatchResult(
            score=global_score,
            matched_skills=matched,
            semantic_matches=semantic_matches,
            missing_skills=missing,
            details={
                "skills": skill_score,
                "exact_matches": matched,
                "semantic_matches": semantic_matches,
                "semantic_weight": sum(
                    match.weight
                    for match in semantic_matches
                ),
                "location": location_score,
                "remote": remote_score,
                "salary": salary_score,
            },
        )

    def _build_job_text(
        self,
        job,
    ) -> str:
        """
        Construit le texte analysé à partir des champs disponibles.
        """

        title = str(
            getattr(job, "title", "") or ""
        )

        description = str(
            getattr(job, "description", "") or ""
        )

        return " ".join(
            part
            for part in (title, description)
            if part
        )