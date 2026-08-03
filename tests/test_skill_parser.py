from src.cv.skills.parser import SkillParser
from src.domain import Skill


def test_parse_empty_text() -> None:
    parser = SkillParser()

    result = parser.parse("")

    assert result == []


def test_parse_returns_skill_objects() -> None:
    parser = SkillParser()

    result = parser.parse(
        """
        Architecture SI.
        Cloud hybride.
        """
    )

    assert len(result) == 2

    assert isinstance(result[0], Skill)
    assert isinstance(result[1], Skill)

    assert result[0].name == "Architecture SI."
    assert result[1].name == "Cloud hybride."


def test_parse_reconstructs_wrapped_skill() -> None:
    parser = SkillParser()

    result = parser.parse(
        """
        Gouvernance
        Reporting DG/CODIR, KPI,
        gestion des risques,
        dépendances et engagements.
        """
    )

    assert len(result) == 1
    assert isinstance(result[0], Skill)

    assert result[0].name == (
        "Reporting DG/CODIR, KPI, gestion des risques, "
        "dépendances et engagements."
    )


if __name__ == "__main__":
    test_parse_empty_text()
    test_parse_returns_skill_objects()
    test_parse_reconstructs_wrapped_skill()

    print("✅ test_skill_parser OK")