from __future__ import annotations

from unittest.mock import patch

from src.matching.models import SemanticMatch
from src.matching.skill_matcher import SkillMatcher
from src.matching.skill_taxonomy import CATEGORY_CLOUD


def test_exact_skill_match() -> None:
    matcher = SkillMatcher()

    matched, semantic, missing = matcher.match(
        ["Python"],
        "Nous recherchons un développeur Python.",
    )

    assert matched == ["python"]
    assert semantic == []
    assert missing == []


def test_unknown_skill_is_missing() -> None:
    matcher = SkillMatcher()

    matched, semantic, missing = matcher.match(
        ["Compétence totalement inconnue"],
        "Offre généraliste sans compétence technique.",
    )

    assert matched == []
    assert semantic == []
    assert missing == [
        "compétence totalement inconnue"
    ]


def test_same_category_creates_semantic_match() -> None:
    matcher = SkillMatcher()

    matched, semantic, missing = matcher.match(
        ["Azure"],
        "Environnement AWS et architecture distribuée.",
    )

    assert matched == []
    assert missing == []
    assert len(semantic) == 1

    result = semantic[0]

    assert isinstance(result, SemanticMatch)
    assert result.profile_skill == "azure"
    assert result.job_skill.casefold() == "aws"
    assert result.category == CATEGORY_CLOUD
    assert result.reason == "same_category"
    assert result.weight == 0.70
    assert result.confidence == 1.0


def test_exact_match_has_priority_over_category() -> None:
    matcher = SkillMatcher()

    matched, semantic, missing = matcher.match(
        ["Azure"],
        "Plateforme Azure avec extension AWS.",
    )

    assert matched == ["azure"]
    assert semantic == []
    assert missing == []


def test_small_term_does_not_create_false_positive() -> None:
    matcher = SkillMatcher()

    matched, semantic, missing = matcher.match(
        ["Go"],
        "Mise en place d'une gouvernance transverse.",
    )

    assert matched == []
    assert semantic == []
    assert missing == ["go"]


def test_matching_tolerates_missing_accents() -> None:
    matcher = SkillMatcher()

    matched, semantic, missing = matcher.match(
        ["Cybersécurité"],
        "Expertise en cybersecurite des plateformes.",
    )

    assert matched == ["cybersécurité"]
    assert semantic == []
    assert missing == []


def test_finance_pilotage_budgetaire_alias() -> None:
    matcher = SkillMatcher()

    matched, semantic, missing = matcher.match(
        ["pilotage budgétaire"],
        "Responsable du pilotage du budget annuel.",
    )

    assert matched == ["pilotage budgétaire"]
    assert semantic == []
    assert missing == []


def test_finance_controle_de_gestion_alias() -> None:
    matcher = SkillMatcher()

    matched, semantic, missing = matcher.match(
        ["contrôle de gestion"],
        "Animation du dialogue de gestion.",
    )

    assert matched == ["contrôle de gestion"]
    assert semantic == []
    assert missing == []


def test_finance_tresorerie_alias_without_accents() -> None:
    matcher = SkillMatcher()

    matched, semantic, missing = matcher.match(
        ["trésorerie"],
        "Mission de suivi de tresorerie.",
    )

    assert matched == ["trésorerie"]
    assert semantic == []
    assert missing == []


def test_finance_short_alias_does_not_match_substring() -> None:
    matcher = SkillMatcher()

    matched, semantic, missing = matcher.match(
        ["sap"],
        "Gestion durable des sapins de Noël.",
    )

    assert matched == []
    assert semantic == []
    assert missing == ["sap"]


def test_one_job_skill_is_not_used_twice() -> None:
    matcher = SkillMatcher()

    matched, semantic, missing = matcher.match(
        ["Azure", "GCP"],
        "Architecture AWS.",
    )

    assert matched == []
    assert len(semantic) == 1
    assert len(missing) == 1
    assert semantic[0].job_skill.casefold() == "aws"


def test_graph_match_creates_typed_result() -> None:
    matcher = SkillMatcher()

    with (
        patch.object(
            matcher,
            "_get_related_skills",
            return_value=["Kubernetes"],
        ),
        patch(
            "src.matching.skill_matcher."
            "SemanticMatcher.proximity",
            return_value=0.80,
        ),
        patch.object(
            matcher,
            "_find_category_match",
            return_value=None,
        ),
    ):
        matched, semantic, missing = matcher.match(
            ["Docker"],
            "Administration de clusters Kubernetes.",
        )

    assert matched == []
    assert missing == []
    assert len(semantic) == 1

    result = semantic[0]

    assert result.reason == "skill_graph"
    assert result.job_skill == "Kubernetes"
    assert result.weight == 0.55
    assert result.confidence == 0.80


def test_empty_profile_skills() -> None:
    matcher = SkillMatcher()

    matched, semantic, missing = matcher.match(
        [],
        "Python Azure Docker",
    )

    assert matched == []
    assert semantic == []
    assert missing == []


if __name__ == "__main__":
    test_exact_skill_match()
    test_unknown_skill_is_missing()
    test_same_category_creates_semantic_match()
    test_exact_match_has_priority_over_category()
    test_small_term_does_not_create_false_positive()
    test_matching_tolerates_missing_accents()
    test_one_job_skill_is_not_used_twice()
    test_graph_match_creates_typed_result()
    test_empty_profile_skills()

    print("✅ test_skill_matcher OK")
