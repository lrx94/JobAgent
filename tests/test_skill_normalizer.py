from src.cv.normalizers import SkillNormalizer


def test_sql_server():
    assert SkillNormalizer.normalize("sqlserver") == "SQL Server"
    assert SkillNormalizer.normalize("SQL Server") == "SQL Server"
    assert SkillNormalizer.normalize("MS SQL") == "SQL Server"


def test_dotnet():
    assert SkillNormalizer.normalize("dotnet") == ".NET"
    assert SkillNormalizer.normalize(".NET") == ".NET"


def test_js():
    assert SkillNormalizer.normalize("js") == "JavaScript"


def test_unknown():
    assert SkillNormalizer.normalize("Kubernetes") == "Kubernetes"


if __name__ == "__main__":
    test_sql_server()
    test_dotnet()
    test_js()
    test_unknown()
    print("✅ test_skill_normalizer OK")