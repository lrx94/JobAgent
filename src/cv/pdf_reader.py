"""
Lecture des fichiers PDF.

Responsabilité :
- ouvrir un PDF
- extraire le texte
- renvoyer une chaîne unique
"""

from pathlib import Path

import fitz


class PdfReader:

    def extract_text(self, pdf_path):

        pdf_path = Path(pdf_path)

        if not pdf_path.exists():
            raise FileNotFoundError(pdf_path)

        document = fitz.open(pdf_path)

        pages = []

        for page in document:
            pages.append(page.get_text())

        document.close()

        return "\n".join(pages)