import fitz
from pathlib import Path


class CVParser:

    def extract_text(self, pdf_path: str) -> str:

        pdf = fitz.open(pdf_path)

        text = ""

        for page in pdf:
            text += page.get_text()

        pdf.close()

        return text