from src.cv.normalizers import TextNormalizer


def test_trim():
    assert TextNormalizer.normalize("  Python  ") == "Python"


def test_multiple_spaces():
    assert TextNormalizer.normalize("SQL    Server") == "SQL Server"


def test_tab():
    assert TextNormalizer.normalize("Bonjour\tMonde") == "Bonjour Monde"


def test_apostrophe():
    assert TextNormalizer.normalize("L’IA") == "L'IA"


def test_dash():
    assert TextNormalizer.normalize("Front–End") == "Front-End"


def test_blank_lines():
    assert (
        TextNormalizer.normalize("RGPD\n\n\nCybersécurité")
        == "RGPD\nCybersécurité"
    )


if __name__ == "__main__":
    test_trim()
    test_multiple_spaces()
    test_tab()
    test_apostrophe()
    test_dash()
    test_blank_lines()
    print("✅ test_text_normalizer OK")