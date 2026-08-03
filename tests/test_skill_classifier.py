from src.domain import Skill
from src.matching.skill_classifier import SkillClassifier
from src.matching.skill_taxonomy import (
    CATEGORY_AGILE,
    CATEGORY_AI,
    CATEGORY_ARCHITECTURE,
    CATEGORY_CLOUD,
    CATEGORY_CYBERSECURITY,
    CATEGORY_DATA,
    CATEGORY_DEVOPS,
    CATEGORY_GOVERNANCE,
    CATEGORY_PROGRAMMING_LANGUAGE,
    CATEGORY_PROJECT_MANAGEMENT,
    CATEGORY_SOFT_SKILL,
    UNKNOWN_CATEGORY,
)


def test_classify_exact_skill() -> None:
    classifier = SkillClassifier()
    skill = Skill(name="Azure")

    result = classifier.classify(skill)

    assert result is skill
    assert result.category == CATEGORY_CLOUD
    assert result.confidence == 1.0


def test_classify_exact_skill_is_case_insensitive() -> None:
    classifier = SkillClassifier()
    skill = Skill(name="pYtHoN")

    result = classifier.classify(skill)

    assert result.category == CATEGORY_PROGRAMMING_LANGUAGE
    assert result.confidence == 1.0


def test_classify_empty_skill() -> None:
    classifier = SkillClassifier()
    skill = Skill(name="")

    result = classifier.classify(skill)

    assert result.category == UNKNOWN_CATEGORY
    assert result.confidence == 0.0


def test_classify_unknown_skill() -> None:
    classifier = SkillClassifier()
    skill = Skill(name="Compétence totalement inconnue")

    result = classifier.classify(skill)

    assert result.category == UNKNOWN_CATEGORY
    assert result.confidence == 0.0


def test_classify_cloud_sentence() -> None:
    classifier = SkillClassifier()

    skill = Skill(
        name=(
            "Architecture et exploitation de plateformes "
            "Azure en cloud hybride."
        )
    )

    result = classifier.classify(skill)

    assert result.category == CATEGORY_CLOUD
    assert result.confidence == 1.0


def test_classify_architecture_sentence() -> None:
    classifier = SkillClassifier()

    skill = Skill(
        name=(
            "Architecture SI, urbanisation et "
            "interopérabilité des applications."
        )
    )

    result = classifier.classify(skill)

    assert result.category == CATEGORY_ARCHITECTURE
    assert result.confidence == 1.0


def test_classify_cybersecurity_sentence() -> None:
    classifier = SkillClassifier()

    skill = Skill(
        name=(
            "RGPD, privacy by design et cybersécurité "
            "des plateformes critiques."
        )
    )

    result = classifier.classify(skill)

    assert result.category == CATEGORY_CYBERSECURITY
    assert result.confidence == 1.0


def test_classify_governance_sentence() -> None:
    classifier = SkillClassifier()

    skill = Skill(
        name="Alignement DSI avec COBIT et ITIL v4."
    )

    result = classifier.classify(skill)

    assert result.category == CATEGORY_GOVERNANCE
    assert result.confidence == 1.0


def test_classify_project_management_sentence() -> None:
    classifier = SkillClassifier()

    skill = Skill(
        name=(
            "Pilotage PMO avec les référentiels "
            "PRINCE2 et PMP."
        )
    )

    result = classifier.classify(skill)

    assert result.category == CATEGORY_PROJECT_MANAGEMENT
    assert result.confidence == 1.0


def test_classify_data_sentence() -> None:
    classifier = SkillClassifier()

    skill = Skill(
        name="Conception de pipelines ETL avec Spark et Airflow."
    )

    result = classifier.classify(skill)

    assert result.category == CATEGORY_DATA
    assert result.confidence == 1.0


def test_classify_ai_sentence() -> None:
    classifier = SkillClassifier()

    skill = Skill(
        name=(
            "Intégration d'outils d'IA et de "
            "machine learning dans les parcours métiers."
        )
    )

    result = classifier.classify(skill)

    assert result.category == CATEGORY_AI
    assert result.confidence == 1.0


def test_classify_agile_sentence() -> None:
    classifier = SkillClassifier()

    skill = Skill(
        name="Delivery Agile avec Scrum et Kanban."
    )

    result = classifier.classify(skill)

    assert result.category == CATEGORY_AGILE
    assert result.confidence == 1.0


def test_classify_soft_skill_sentence() -> None:
    classifier = SkillClassifier()

    skill = Skill(
        name=(
            "Leadership, management d'équipe "
            "et conduite du changement."
        )
    )

    result = classifier.classify(skill)

    assert result.category == CATEGORY_SOFT_SKILL
    assert result.confidence == 1.0


def test_classifier_does_not_match_go_inside_gouvernance() -> None:
    classifier = SkillClassifier()

    skill = Skill(
        name="Structuration de la gouvernance transverse."
    )

    result = classifier.classify(skill)

    assert result.category == UNKNOWN_CATEGORY
    assert result.confidence == 0.0


def test_classifier_does_not_match_ia_inside_unrelated_word() -> None:
    classifier = SkillClassifier()

    skill = Skill(name="Pilotage social et organisationnel.")

    result = classifier.classify(skill)

    assert result.category == UNKNOWN_CATEGORY
    assert result.confidence == 0.0


def test_classify_mixed_sentence_uses_majority_category() -> None:
    classifier = SkillClassifier()

    skill = Skill(
        name=(
            "Architecture SI, architecture applicative, "
            "urbanisation et Azure."
        )
    )

    result = classifier.classify(skill)

    assert result.category == CATEGORY_ARCHITECTURE
    assert result.confidence == 0.75


def test_classify_mixed_sentence_returns_partial_confidence() -> None:
    classifier = SkillClassifier()

    skill = Skill(
        name="Azure et Kubernetes."
    )

    result = classifier.classify(skill)

    assert result.category == CATEGORY_CLOUD
    assert result.confidence == 0.5


def test_classify_many() -> None:
    classifier = SkillClassifier()

    skills = [
        Skill(name="Python"),
        Skill(name="Docker"),
        Skill(name="COBIT"),
    ]

    result = classifier.classify_many(skills)

    assert result is not skills
    assert len(result) == 3

    assert result[0].category == CATEGORY_PROGRAMMING_LANGUAGE
    assert result[1].category == CATEGORY_DEVOPS
    assert result[2].category == CATEGORY_GOVERNANCE


def test_classification_tolerates_missing_accents() -> None:
    classifier = SkillClassifier()

    skill = Skill(name="Cybersecurite et securite des plateformes.")

    result = classifier.classify(skill)

    assert result.category == CATEGORY_CYBERSECURITY
    assert result.confidence == 1.0


if __name__ == "__main__":
    test_classify_exact_skill()
    test_classify_exact_skill_is_case_insensitive()
    test_classify_empty_skill()
    test_classify_unknown_skill()
    test_classify_cloud_sentence()
    test_classify_architecture_sentence()
    test_classify_cybersecurity_sentence()
    test_classify_governance_sentence()
    test_classify_project_management_sentence()
    test_classify_data_sentence()
    test_classify_ai_sentence()
    test_classify_agile_sentence()
    test_classify_soft_skill_sentence()
    test_classifier_does_not_match_go_inside_gouvernance()
    test_classifier_does_not_match_ia_inside_unrelated_word()
    test_classify_mixed_sentence_uses_majority_category()
    test_classify_mixed_sentence_returns_partial_confidence()
    test_classify_many()
    test_classification_tolerates_missing_accents()

    print("✅ test_skill_classifier OK")