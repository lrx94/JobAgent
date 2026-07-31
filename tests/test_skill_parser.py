from src.cv.skills import SkillParser


TEXT = """
Python
Azure
Docker
ITIL
"""


def main() -> None:

    parser = SkillParser()

    skills = parser.parse(TEXT)

    print("=" * 80)
    print("SKILL PARSER")
    print("=" * 80)

    print(f"\n{len(skills)} compétence(s)\n")

    for skill in skills:
        print(skill)

    assert len(skills) == 4
    assert skills[0].name == "Python"
    assert skills[1].name == "Azure"
    assert skills[2].name == "Docker"
    assert skills[3].name == "ITIL"

    print("\n✅ Test OK")


if __name__ == "__main__":
    main()
    