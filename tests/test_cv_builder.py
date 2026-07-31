from __future__ import annotations

from src.cv import CVBuilder, PdfReader
from src.domain import Skill
from src.matching.skill_taxonomy import (
    CATEGORY_AI,
    CATEGORY_ARCHITECTURE,
    CATEGORY_CYBERSECURITY,
    CATEGORY_GOVERNANCE,
    CATEGORY_SOFT_SKILL,
    UNKNOWN_CATEGORY,
)


def build_test_cv():
    """
    Construit le CV de référence utilisé par les tests.
    """

    reader = PdfReader()
    builder = CVBuilder()

    text = reader.extract_text("data/cv/test_cv.pdf")

    return builder.build(text)


def find_skill_starting_with(cv, prefix: str) -> Skill:
    """
    Recherche une compétence à partir du début de son libellé.
    """

    for skill in cv.skills:
        if skill.name.startswith(prefix):
            return skill

    raise AssertionError(
        f"Aucune compétence ne commence par : {prefix!r}"
    )


def test_cv_builder_structure() -> None:
    cv = build_test_cv()

    assert len(cv.summary) > 0
    assert len(cv.experiences) == 5
    assert len(cv.education) == 3
    assert len(cv.languages) == 3
    assert len(cv.skills) >= 20
    assert len(cv.interests) == 6


def test_cv_builder_first_experience() -> None:
    cv = build_test_cv()

    experience = cv.experiences[0]

    assert experience.company == "Gustave Roussy"
    assert (
        experience.title
        == "Responsable Étude et Développement / PMO Applicatif"
    )
    assert experience.period == "D'août 2023 à déc. 2025"


def test_cv_builder_returns_skill_objects() -> None:
    cv = build_test_cv()

    assert cv.skills

    assert all(
        isinstance(skill, Skill)
        for skill in cv.skills
    )

    assert all(
        skill.name
        for skill in cv.skills
    )


def test_cv_builder_classifies_all_skills() -> None:
    cv = build_test_cv()

    assert all(
        skill.category
        for skill in cv.skills
    )

    assert all(
        0.0 <= skill.confidence <= 1.0
        for skill in cv.skills
    )


def test_cv_builder_classifies_architecture_skill() -> None:
    cv = build_test_cv()

    skill = find_skill_starting_with(
        cv,
        "Architecture, urbanisation",
    )

    assert skill.category == CATEGORY_ARCHITECTURE
    assert skill.confidence > 0.0


def test_cv_builder_classifies_cybersecurity_skill() -> None:
    cv = build_test_cv()

    skill = find_skill_starting_with(
        cv,
        "RGPD, privacy by design",
    )

    assert skill.category == CATEGORY_CYBERSECURITY
    assert skill.confidence > 0.0


def test_cv_builder_classifies_governance_skill() -> None:
    cv = build_test_cv()

    skill = find_skill_starting_with(
        cv,
        "Alignement Dir/DSI COBIT",
    )

    assert skill.category == CATEGORY_GOVERNANCE
    assert skill.confidence > 0.0


def test_cv_builder_classifies_governance_setup_skill() -> None:
    """
    Vérifie que la compétence est bien passée dans le classifieur.

    Cette phrase est sémantiquement ambiguë : elle peut relever de la
    gouvernance, de la gestion de projet ou rester inconnue selon la
    taxonomie. Le test d'intégration ne doit donc pas imposer une
    catégorie métier précise.
    """

    cv = build_test_cv()

    skill = find_skill_starting_with(
        cv,
        "Mise en place d'une gouvernance dédiée",
    )
    
    assert skill.category
    assert 0.0 <= skill.confidence <= 1.0

    if skill.category == UNKNOWN_CATEGORY:
        assert skill.confidence == 0.0
    else:
        assert skill.confidence > 0.0


def test_cv_builder_classifies_ai_skill() -> None:
    cv = build_test_cv()

    skill = find_skill_starting_with(
        cv,
        "Intégration d'outils d'IA",
    )

    assert skill.category == CATEGORY_AI
    assert skill.confidence > 0.0


def test_cv_builder_classifies_soft_skill() -> None:
    cv = build_test_cv()

    skill = find_skill_starting_with(
        cv,
        "Conduite du changement",
    )

    assert skill.category == CATEGORY_SOFT_SKILL
    assert skill.confidence > 0.0


def test_cv_builder_keeps_unknown_skills_valid() -> None:
    cv = build_test_cv()

    unknown_skills = [
        skill
        for skill in cv.skills
        if skill.category == UNKNOWN_CATEGORY
    ]

    assert all(
        skill.confidence == 0.0
        for skill in unknown_skills
    )


def test_cv_builder_contains_expected_skills() -> None:
    cv = build_test_cv()

    assert any(
        skill.name.startswith(
            "Transformation d'organisations Tech et SI"
        )
        for skill in cv.skills
    )

    assert any(
        skill.name.startswith(
            "Mise en place d'une gouvernance dédiée"
        )
        for skill in cv.skills
    )

    assert any(
        skill.name.startswith(
            "Alignement Dir/DSI COBIT"
        )
        for skill in cv.skills
    )


def display_cv_result() -> None:
    """
    Affiche le résultat complet pour le contrôle manuel.
    """

    cv = build_test_cv()

    print("\n" + "=" * 80)
    print("INTERESTS")
    print("=" * 80)

    for interest in cv.interests:
        print(repr(interest))

    print("\n" + "=" * 80)
    print("EXPERIENCES")
    print("=" * 80)

    for index, experience in enumerate(
        cv.experiences,
        start=1,
    ):
        print(
            f"{index}. "
            f"{experience.company} | "
            f"{experience.title} | "
            f"{experience.period}"
        )

    print("\n" + "=" * 80)
    print("CV")
    print("=" * 80)

    print()
    print("Summary      :", len(cv.summary), "caractères")
    print("Experiences  :", len(cv.experiences))
    print("Education    :", len(cv.education))
    print("Languages    :", len(cv.languages))
    print("Skills       :", len(cv.skills))
    print("Interests    :", len(cv.interests))

    print("\n" + "=" * 80)
    print("PREMIÈRE EXPÉRIENCE")
    print("=" * 80)

    experience = cv.experiences[0]

    print("Company :", experience.company)
    print("Title   :", experience.title)
    print("Period  :", experience.period)

    print("\n" + "=" * 80)
    print("COMPÉTENCES CLASSIFIÉES")
    print("=" * 80)

    for skill in cv.skills:
        print(
            f"- {skill.name}\n"
            f"  category   : {skill.category}\n"
            f"  confidence : {skill.confidence:.2f}"
        )


if __name__ == "__main__":
    test_cv_builder_structure()
    test_cv_builder_first_experience()
    test_cv_builder_returns_skill_objects()
    test_cv_builder_classifies_all_skills()
    test_cv_builder_classifies_architecture_skill()
    test_cv_builder_classifies_cybersecurity_skill()
    test_cv_builder_classifies_governance_skill()
    test_cv_builder_classifies_governance_setup_skill()
    test_cv_builder_classifies_ai_skill()
    test_cv_builder_classifies_soft_skill()
    test_cv_builder_keeps_unknown_skills_valid()
    test_cv_builder_contains_expected_skills()

    display_cv_result()

    print("\n✅ test_cv_builder OK")