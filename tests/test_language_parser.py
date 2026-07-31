from src.cv.language_parser import LanguageParser
from src.domain import Language


def test_language_parser():

    parser = LanguageParser()

    languages = parser.parse(
        """
        Français
        Anglais
        EN
        """
    )

    assert len(languages) == 3
    assert isinstance(languages[0], Language)
    assert languages[0].name == "French"
    assert languages[1].name == "English"
    assert languages[2].name == "English"


if __name__ == "__main__":
    test_language_parser()
    print("✅ test_language_parser OK")