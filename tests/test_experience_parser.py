from src.cv import PdfReader
from src.cv.section_parser import SectionParser
from src.cv.experience_parser import ExperienceParser

reader = PdfReader()
section_parser = SectionParser()
experience_parser = ExperienceParser()

text = reader.extract_text("data/cv/test_cv.pdf")

sections = section_parser.parse(text)

experiences = experience_parser.parse(
    sections["experiences"]
)

print()

print(f"{len(experiences)} expérience(s)\n")

for i, exp in enumerate(experiences, start=1):

    print("=" * 80)

    print(f"Experience {i}")

    print("=" * 80)

    print("Company :", exp.company)
    print("Title   :", exp.title)
    print("Location:", exp.location)
    print("Period  :", exp.period)

    print()

    print(exp.description[:250])

    print()