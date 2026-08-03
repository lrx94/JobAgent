from __future__ import annotations

from dataclasses import dataclass

from src.matching.models import SemanticMatch
from src.matching.scorer import Scorer


@dataclass
class DummyProfile:
    locations: list[str]
    remote: bool
    salary_min: float


@dataclass
class DummyJob:
    location: str
    remote: bool
    salary: float


def build_semantic_match(
    weight: float,
) -> SemanticMatch:
    return SemanticMatch(
        profile_skill="Azure",
        job_skill="AWS",
        category="Cloud",
        reason="same_category",
        weight=weight,
        confidence=1.0,
    )


def test_skill_score_without_skills() -> None:
    scorer = Scorer()

    assert scorer.skill_score(
        matches=0,
        total=0,
    ) == 0


def test_skill_score_exact_matches() -> None:
    scorer = Scorer()

    assert scorer.skill_score(
        matches=2,
        total=4,
    ) == 50


def test_skill_score_is_bounded_to_one_hundred() -> None:
    scorer = Scorer()

    assert scorer.skill_score(
        matches=10,
        total=2,
    ) == 100


def test_semantic_skill_score() -> None:
    scorer = Scorer()

    score = scorer.semantic_skill_score(
        exact_matches=["Python"],
        semantic_matches=[
            build_semantic_match(0.70),
        ],
        total=3,
    )

    assert score == 57


def test_location_score_without_preference() -> None:
    scorer = Scorer()

    profile = DummyProfile(
        locations=[],
        remote=False,
        salary_min=0,
    )

    job = DummyJob(
        location="Lyon",
        remote=False,
        salary=0,
    )

    assert scorer.location_score(profile, job) == 100


def test_location_score_matches_case_insensitively() -> None:
    scorer = Scorer()

    profile = DummyProfile(
        locations=["Paris"],
        remote=False,
        salary_min=0,
    )

    job = DummyJob(
        location="PARIS, France",
        remote=False,
        salary=0,
    )

    assert scorer.location_score(profile, job) == 100


def test_location_score_is_zero_when_missing() -> None:
    scorer = Scorer()

    profile = DummyProfile(
        locations=["Paris"],
        remote=False,
        salary_min=0,
    )

    job = DummyJob(
        location="Lyon",
        remote=False,
        salary=0,
    )

    assert scorer.location_score(profile, job) == 0


def test_remote_score_when_remote_is_required() -> None:
    scorer = Scorer()

    profile = DummyProfile(
        locations=[],
        remote=True,
        salary_min=0,
    )

    remote_job = DummyJob(
        location="Paris",
        remote=True,
        salary=0,
    )

    onsite_job = DummyJob(
        location="Paris",
        remote=False,
        salary=0,
    )

    assert scorer.remote_score(
        profile,
        remote_job,
    ) == 100

    assert scorer.remote_score(
        profile,
        onsite_job,
    ) == 0


def test_remote_score_when_remote_is_not_required() -> None:
    scorer = Scorer()

    profile = DummyProfile(
        locations=[],
        remote=False,
        salary_min=0,
    )

    job = DummyJob(
        location="Paris",
        remote=False,
        salary=0,
    )

    assert scorer.remote_score(profile, job) == 100


def test_salary_score_without_minimum() -> None:
    scorer = Scorer()

    profile = DummyProfile(
        locations=[],
        remote=False,
        salary_min=0,
    )

    job = DummyJob(
        location="Paris",
        remote=False,
        salary=0,
    )

    assert scorer.salary_score(profile, job) == 100


def test_salary_score_above_minimum() -> None:
    scorer = Scorer()

    profile = DummyProfile(
        locations=[],
        remote=False,
        salary_min=60_000,
    )

    job = DummyJob(
        location="Paris",
        remote=False,
        salary=70_000,
    )

    assert scorer.salary_score(profile, job) == 100


def test_salary_score_below_minimum() -> None:
    scorer = Scorer()

    profile = DummyProfile(
        locations=[],
        remote=False,
        salary_min=60_000,
    )

    job = DummyJob(
        location="Paris",
        remote=False,
        salary=45_000,
    )

    assert scorer.salary_score(profile, job) == 75


def test_salary_score_with_missing_salary() -> None:
    scorer = Scorer()

    profile = DummyProfile(
        locations=[],
        remote=False,
        salary_min=60_000,
    )

    job = DummyJob(
        location="Paris",
        remote=False,
        salary=0,
    )

    assert scorer.salary_score(profile, job) == 0


def test_global_score() -> None:
    scorer = Scorer()

    score = scorer.global_score(
        skill=80,
        location=100,
        remote=100,
        salary=100,
    )

    assert score == 90


def test_global_score_is_bounded() -> None:
    scorer = Scorer()

    assert scorer.global_score(
        skill=200,
        location=200,
        remote=200,
        salary=200,
    ) == 100


if __name__ == "__main__":
    test_skill_score_without_skills()
    test_skill_score_exact_matches()
    test_skill_score_is_bounded_to_one_hundred()
    test_semantic_skill_score()
    test_location_score_without_preference()
    test_location_score_matches_case_insensitively()
    test_location_score_is_zero_when_missing()
    test_remote_score_when_remote_is_required()
    test_remote_score_when_remote_is_not_required()
    test_salary_score_without_minimum()
    test_salary_score_above_minimum()
    test_salary_score_below_minimum()
    test_salary_score_with_missing_salary()
    test_global_score()
    test_global_score_is_bounded()

    print("✅ test_scorer OK")