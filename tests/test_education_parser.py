from src.cv import PdfReader
from src.cv.section_parser import SectionParser
from src.cv.education_parser import EducationParser

reader = PdfReader()
section_parser = SectionParser()
parser = EducationParser()

text = reader.extract_text("data/cv/test_cv.pdf")

sections = section_parser.parse(text)

result = parser.parse(sections["education"])

print(f"{len(result.education)} formation(s)")
print(f"{len(result.certifications)} certification(s)\n")

print("=" * 80)
print("FORMATIONS")
print("=" * 80)

for education in result.education:

    print(f"Year   : {education.year}")
    print(f"School : {education.school}")
    print(f"Degree : {education.degree}")

    if education.description:
        print("Description :")
        print(education.description)

    print()
    print("=" * 80)

print()
print("=" * 80)
print("CERTIFICATIONS")
print("=" * 80)

for certification in result.certifications:

    print(f"Year         : {certification.year}")
    print(f"Organisation : {certification.organization}")
    print(f"Nom          : {certification.name}")

    if certification.description:
        print("Description :")
        print(certification.description)

    print()
    print("=" * 80)