from .skill_matcher import SkillMatcher
from .scorer import Scorer
from .models import MatchResult


class MatchingEngine:

    def __init__(self):
        self.matcher = SkillMatcher()
        self.scorer = Scorer()

    def match(self, profile, job):

        matched, missing = self.matcher.match(
            profile.keywords,
            job.title + " " + job.description
        )

        skill = self.scorer.skill_score(
            matched,
            len(profile.keywords)
        )

        location = self.scorer.location_score(
            profile,
            job
        )

        remote = self.scorer.remote_score(
            profile,
            job
        )

        salary = self.scorer.salary_score(
            profile,
            job
        )

        score = self.scorer.global_score(
            skill,
            location,
            remote,
            salary
        )

        return MatchResult(
            score=score,
            matched_skills=matched,
            missing_skills=missing,
            details={
                "skills": skill,
                "location": location,
                "remote": remote,
                "salary": salary
            }
        )