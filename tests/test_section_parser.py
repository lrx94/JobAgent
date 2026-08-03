from src.cv import PdfReader
from src.cv.section_parser import SectionParser

reader = PdfReader()
parser = SectionParser()

text = reader.extract_text("data/cv/test_cv.pdf")
sections = parser.parse(text)

for name, content in sections.items():
    print("=" * 80)
    print(name.upper())
    print("=" * 80)
    print(content[:500])
    print()