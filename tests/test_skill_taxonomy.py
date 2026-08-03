from src.matching.skill_taxonomy import (
    CATEGORY_AGILE,
    CATEGORY_AI,
    CATEGORY_ARCHITECTURE,
    CATEGORY_CLOUD,
    CATEGORY_CYBERSECURITY,
    CATEGORY_DATA,
    CATEGORY_DATABASE,
    CATEGORY_DEVOPS,
    CATEGORY_GOVERNANCE,
    CATEGORY_PRODUCT_MANAGEMENT,
    CATEGORY_PROGRAMMING_LANGUAGE,
    CATEGORY_PROJECT_MANAGEMENT,
    CATEGORY_SOFT_SKILL,
    UNKNOWN_CATEGORY,
    get_category_for_exact_skill,
    get_known_categories,
    get_skills_for_category,
    normalize_taxonomy_value,
)


def test_normalize_taxonomy_value() -> None:
    assert normalize_taxonomy_value("  Azure  ") == "azure"
    assert normalize_taxonomy_value("ITIL   V4") == "itil v4"
    assert normalize_taxonomy_value("C++") == "c++"
    assert normalize_taxonomy_value("CI/CD") == "ci/cd"


def test_empty_skill_returns_unknown_category() -> None:
    assert get_category_for_exact_skill("") == UNKNOWN_CATEGORY
    assert get_category_for_exact_skill("   ") == UNKNOWN_CATEGORY


def test_classifies_programming_languages() -> None:
    assert (
        get_category_for_exact_skill("Python")
        == CATEGORY_PROGRAMMING_LANGUAGE
    )
    assert (
        get_category_for_exact_skill("C#")
        == CATEGORY_PROGRAMMING_LANGUAGE
    )
    assert (
        get_category_for_exact_skill("SQL")
        == CATEGORY_PROGRAMMING_LANGUAGE
    )


def test_classifies_databases() -> None:
    assert get_category_for_exact_skill("PostgreSQL") == CATEGORY_DATABASE
    assert get_category_for_exact_skill("SQL Server") == CATEGORY_DATABASE
    assert get_category_for_exact_skill("MongoDB") == CATEGORY_DATABASE


def test_classifies_cloud_skills() -> None:
    assert get_category_for_exact_skill("Azure") == CATEGORY_CLOUD
    assert get_category_for_exact_skill("AWS") == CATEGORY_CLOUD
    assert get_category_for_exact_skill("GCP") == CATEGORY_CLOUD
    assert get_category_for_exact_skill("Cloud hybride") == CATEGORY_CLOUD


def test_classifies_devops_skills() -> None:
    assert get_category_for_exact_skill("Docker") == CATEGORY_DEVOPS
    assert get_category_for_exact_skill("Kubernetes") == CATEGORY_DEVOPS
    assert get_category_for_exact_skill("Terraform") == CATEGORY_DEVOPS


def test_classifies_data_skills() -> None:
    assert get_category_for_exact_skill("Spark") == CATEGORY_DATA
    assert get_category_for_exact_skill("ETL") == CATEGORY_DATA
    assert get_category_for_exact_skill("Data Lake") == CATEGORY_DATA


def test_classifies_artificial_intelligence_skills() -> None:
    assert get_category_for_exact_skill("IA") == CATEGORY_AI
    assert get_category_for_exact_skill("Machine Learning") == CATEGORY_AI
    assert get_category_for_exact_skill("LLM") == CATEGORY_AI


def test_classifies_architecture_skills() -> None:
    assert (
        get_category_for_exact_skill("Architecture SI")
        == CATEGORY_ARCHITECTURE
    )
    assert (
        get_category_for_exact_skill("Design Authority")
        == CATEGORY_ARCHITECTURE
    )
    assert (
        get_category_for_exact_skill("Urbanisation")
        == CATEGORY_ARCHITECTURE
    )


def test_classifies_cybersecurity_skills() -> None:
    assert get_category_for_exact_skill("RGPD") == CATEGORY_CYBERSECURITY
    assert (
        get_category_for_exact_skill("Privacy by design")
        == CATEGORY_CYBERSECURITY
    )
    assert (
        get_category_for_exact_skill("Cybersécurité")
        == CATEGORY_CYBERSECURITY
    )


def test_classifies_governance_frameworks() -> None:
    assert get_category_for_exact_skill("COBIT") == CATEGORY_GOVERNANCE
    assert get_category_for_exact_skill("ITIL v4") == CATEGORY_GOVERNANCE
    assert get_category_for_exact_skill("TOGAF") == CATEGORY_GOVERNANCE


def test_classifies_project_management_skills() -> None:
    assert (
        get_category_for_exact_skill("PRINCE2")
        == CATEGORY_PROJECT_MANAGEMENT
    )
    assert (
        get_category_for_exact_skill("PMP")
        == CATEGORY_PROJECT_MANAGEMENT
    )
    assert (
        get_category_for_exact_skill("PMO")
        == CATEGORY_PROJECT_MANAGEMENT
    )


def test_classifies_product_management_skills() -> None:
    assert (
        get_category_for_exact_skill("Product Manager")
        == CATEGORY_PRODUCT_MANAGEMENT
    )
    assert (
        get_category_for_exact_skill("Product Owner")
        == CATEGORY_PRODUCT_MANAGEMENT
    )


def test_classifies_agile_skills() -> None:
    assert get_category_for_exact_skill("Scrum") == CATEGORY_AGILE
    assert get_category_for_exact_skill("Kanban") == CATEGORY_AGILE
    assert get_category_for_exact_skill("SAFe") == CATEGORY_AGILE


def test_classifies_soft_skills() -> None:
    assert get_category_for_exact_skill("Leadership") == CATEGORY_SOFT_SKILL
    assert get_category_for_exact_skill("Management") == CATEGORY_SOFT_SKILL
    assert (
        get_category_for_exact_skill("Conduite du changement")
        == CATEGORY_SOFT_SKILL
    )


def test_unknown_skill_returns_unknown_category() -> None:
    assert (
        get_category_for_exact_skill("Compétence totalement inconnue")
        == UNKNOWN_CATEGORY
    )


def test_get_known_categories() -> None:
    categories = get_known_categories()

    assert CATEGORY_CLOUD in categories
    assert CATEGORY_DATA in categories
    assert CATEGORY_AI in categories
    assert CATEGORY_ARCHITECTURE in categories
    assert CATEGORY_PROJECT_MANAGEMENT in categories


def test_get_skills_for_existing_category() -> None:
    cloud_skills = get_skills_for_category(CATEGORY_CLOUD)

    assert isinstance(cloud_skills, frozenset)
    assert "azure" in cloud_skills
    assert "aws" in cloud_skills
    assert "gcp" in cloud_skills


def test_get_skills_for_unknown_category() -> None:
    result = get_skills_for_category("Invalid Category")

    assert result == frozenset()


if __name__ == "__main__":
    test_normalize_taxonomy_value()
    test_empty_skill_returns_unknown_category()
    test_classifies_programming_languages()
    test_classifies_databases()
    test_classifies_cloud_skills()
    test_classifies_devops_skills()
    test_classifies_data_skills()
    test_classifies_artificial_intelligence_skills()
    test_classifies_architecture_skills()
    test_classifies_cybersecurity_skills()
    test_classifies_governance_frameworks()
    test_classifies_project_management_skills()
    test_classifies_product_management_skills()
    test_classifies_agile_skills()
    test_classifies_soft_skills()
    test_unknown_skill_returns_unknown_category()
    test_get_known_categories()
    test_get_skills_for_existing_category()
    test_get_skills_for_unknown_category()

    print("✅ test_skill_taxonomy OK")