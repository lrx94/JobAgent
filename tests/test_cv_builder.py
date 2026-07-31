
from src.cv import PdfReader
from src.cv import CVBuilder
from src.domain import Skill

reader = PdfReader()
builder = CVBuilder()

text = reader.extract_text("data/cv/test_cv.pdf")

cv = builder.build(text)
print("\n" + "=" * 80)
print("INTERESTS")
print("=" * 80)

for interest in cv.interests:
    print(repr(interest))

print("\n" + "=" * 80)
print("EXPERIENCES")
print("=" * 80)

for i, exp in enumerate(cv.experiences, start=1):
    print(f"{i}. {exp.company} | {exp.title} | {exp.period}")

print()

print("=" * 80)
print("CV")
print("=" * 80)

print()

print("Summary      :", len(cv.summary), "caractères")
print("Experiences  :", len(cv.experiences))
print("Education    :", len(cv.education))
print("Languages    :", len(cv.languages))
print("Skills       :", len(cv.skills))
print("Interests    :", len(cv.interests))

print()
assert len(cv.experiences) == 5

assert len(cv.education) == 3

assert len(cv.languages) == 3

assert len(cv.interests) == 6

print("=" * 80)
print("Première expérience")
print("=" * 80)

exp = cv.experiences[0]

print("Company :", exp.company)
print("Title   :", exp.title)
print("Period  :", exp.period)

print()

print("=" * 80)
print("Compétences")
print("=" * 80)

print(cv.skills)
assert len(cv.skills) > 10
assert all(skill.name for skill in cv.skills)
assert isinstance(cv.skills[0], Skill)
assert any(
    "Transformation d'organisations Tech et SI" in skill.name
    for skill in cv.skills
)
assert cv.skills[0].name != ""
assert len(cv.skills) >= 20

assert all(
    isinstance(skill, Skill)
    for skill in cv.skills
)

assert any(
    skill.name.startswith("Mise en place d'une gouvernance dédiée")
    for skill in cv.skills
)

assert any(
    skill.name.startswith("Alignement Dir/DSI COBIT")
    for skill in cv.skills
)
print(type(cv.skills[0]))