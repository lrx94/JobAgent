
from src.cv import PdfReader
from src.cv import CVBuilder

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