from src.cv.normalizers import LanguageNormalizer


def test_english():
    assert LanguageNormalizer.normalize("anglais") == "English"
    assert LanguageNormalizer.normalize("English") == "English"
    assert LanguageNormalizer.normalize("EN") == "English"


def test_french():
    assert LanguageNormalizer.normalize("français") == "French"
    assert LanguageNormalizer.normalize("FR") == "French"


def test_spanish():
    assert LanguageNormalizer.normalize("espagnol") == "Spanish"


def test_unknown():
    assert LanguageNormalizer.normalize("Japonais") == "Japonais"


if __name__ == "__main__":
    test_english()
    test_french()
    test_spanish()
    test_unknown()
    print("✅ test_language_normalizer OK")