from __future__ import annotations

from dataclasses import dataclass

from src.matching.engine import MatchingEngine
from src.matching.models import MatchResult, SemanticMatch


@dataclass
class DummyProfile:
    keywords: list[str]
    locations: list[str]
    salary_min: float
    remote: bool


@dataclass
class DummyJob:
    title: str
    description: str
    location: str
    salary: float
    remote: bool


def test_engine_returns_match_result() -> None:
    engine = MatchingEngine()

    profile = DummyProfile(
        keywords=["Python"],
        locations=["Paris"],
        salary_min=60_000,
        remote=True,
    )

    job = DummyJob(
        title="Développeur Python",
        description="Développement de services Python.",
        location="Paris",
        salary=65_000,
        remote=True,
    )

    result = engine.match(profile, job)

    assert isinstance(result, MatchResult)
    assert result.score == 100
    assert result.matched_skills == ["python"]
    assert result.exact_matches == ["python"]
    assert result.semantic_matches == []
    assert result.missing_skills == []


def test_engine_uses_same_category_matching() -> None:
    engine = MatchingEngine()

    profile = DummyProfile(
        keywords=["Azure"],
        locations=[],
        salary_min=0,
        remote=False,
    )

    job = DummyJob(
        title="Cloud Architect AWS",
        description="Conception de plateformes AWS.",
        location="Remote",
        salary=0,
        remote=True,
    )

    result = engine.match(profile, job)

    assert result.matched_skills == []
    assert result.missing_skills == []
    assert len(result.semantic_matches) == 1

    semantic_match = result.semantic_matches[0]

    assert isinstance(
        semantic_match,
        SemanticMatch,
    )

    assert semantic_match.profile_skill == "azure"
    assert semantic_match.job_skill.casefold() == "aws"
    assert semantic_match.reason == "same_category"
    assert semantic_match.weight == 0.70

    assert result.details["skills"] == 70
    assert result.details["semantic_weight"] == 0.70

    # Skill 70 % pondéré à 50 %, tous les autres critères à 100 %.
    assert result.score == 85


def test_engine_exact_match_scores_more_than_semantic_match() -> None:
    engine = MatchingEngine()

    profile = DummyProfile(
        keywords=["Azure"],
        locations=[],
        salary_min=0,
        remote=False,
    )

    exact_job = DummyJob(
        title="Architecte Azure",
        description="Architecture Azure.",
        location="Remote",
        salary=0,
        remote=True,
    )

    semantic_job = DummyJob(
        title="Architecte AWS",
        description="Architecture AWS.",
        location="Remote",
        salary=0,
        remote=True,
    )

    exact_result = engine.match(
        profile,
        exact_job,
    )

    semantic_result = engine.match(
        profile,
        semantic_job,
    )

    assert exact_result.details["skills"] == 100
    assert semantic_result.details["skills"] == 70
    assert exact_result.score > semantic_result.score


def test_engine_reports_missing_skills() -> None:
    engine = MatchingEngine()

    profile = DummyProfile(
        keywords=["Python", "PostgreSQL"],
        locations=[],
        salary_min=0,
        remote=False,
    )

    job = DummyJob(
        title="Développeur Python",
        description="Développement Python.",
        location="Paris",
        salary=0,
        remote=False,
    )

    result = engine.match(profile, job)

    assert result.matched_skills == ["python"]
    assert result.semantic_matches == []
    assert result.missing_skills == ["sql"]
    assert result.details["skills"] == 50
    assert result.score == 75


def test_engine_combines_exact_and_semantic_matches() -> None:
    engine = MatchingEngine()

    profile = DummyProfile(
        keywords=[
            "Python",
            "Azure",
            "PostgreSQL",
        ],
        locations=[],
        salary_min=0,
        remote=False,
    )

    job = DummyJob(
        title="Python Cloud Engineer",
        description=(
            "Développement Python sur AWS "
            "avec conteneurisation Docker."
        ),
        location="Remote",
        salary=0,
        remote=True,
    )

    result = engine.match(profile, job)

    assert result.matched_skills == ["python"]
    assert len(result.semantic_matches) == 1
    assert result.missing_skills == ["sql"]

    # (1 exact + 0.70 sémantique) / 3 = 56.67 %, arrondi à 57.
    assert result.details["skills"] == 57

    # 57 * 0.50 + 100 * 0.50 = 78.5, arrondi Python à 78.
    assert result.score == 78


def test_engine_handles_empty_profile_skills() -> None:
    engine = MatchingEngine()

    profile = DummyProfile(
        keywords=[],
        locations=[],
        salary_min=0,
        remote=False,
    )

    job = DummyJob(
        title="Développeur Python",
        description="Python Azure Docker.",
        location="Paris",
        salary=0,
        remote=False,
    )

    result = engine.match(profile, job)

    assert result.matched_skills == []
    assert result.semantic_matches == []
    assert result.missing_skills == []
    assert result.details["skills"] == 0
    assert result.score == 0


def test_engine_handles_missing_job_attributes() -> None:
    class MinimalJob:
        title = "Développeur Python"

    engine = MatchingEngine()

    profile = DummyProfile(
        keywords=["Python"],
        locations=[],
        salary_min=0,
        remote=False,
    )

    result = engine.match(
        profile,
        MinimalJob(),
    )

    assert result.matched_skills == ["python"]
    assert result.details["skills"] == 100
    assert 0 <= result.score <= 100


def display_example() -> None:
    engine = MatchingEngine()

    profile = DummyProfile(
        keywords=[
            "Python",
            "Azure",
            "PostgreSQL",
        ],
        locations=["Paris"],
        salary_min=60_000,
        remote=True,
    )

    job = DummyJob(
        title="Cloud Engineer Python",
        description=(
            "Développement Python sur AWS "
            "et déploiement Docker."
        ),
        location="Paris",
        salary=65_000,
        remote=True,
    )

    result = engine.match(profile, job)

    print("\n" + "=" * 80)
    print("UNIFIED SEMANTIC MATCHING")
    print("=" * 80)

    print("Score global :", result.score)
    print("Score skills :", result.details["skills"])
    print("Exact        :", result.matched_skills)
    print("Missing      :", result.missing_skills)

    print("\nSemantic matches:")

    for match in result.semantic_matches:
        print(
            f"- {match.profile_skill} -> {match.job_skill}"
            f" | category={match.category}"
            f" | reason={match.reason}"
            f" | weight={match.weight:.2f}"
            f" | confidence={match.confidence:.2f}"
        )


if __name__ == "__main__":
    test_engine_returns_match_result()
    test_engine_uses_same_category_matching()
    test_engine_exact_match_scores_more_than_semantic_match()
    test_engine_reports_missing_skills()
    test_engine_combines_exact_and_semantic_matches()
    test_engine_handles_empty_profile_skills()
    test_engine_handles_missing_job_attributes()

    display_example()

    print("\n✅ test_matching_engine OK")
