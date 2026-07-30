"""
Extraction du premier intitulé de poste du CV.
"""

import re


class JobTitleExtractor:

    def extract(self, text: str) -> str | None:

        lines = [
            line.strip()
            for line in text.splitlines()
            if line.strip()
        ]

        # Recherche de la section Expériences
        start = None

        for i, line in enumerate(lines):

            if "expérience" in line.lower():
                start = i
                break

        if start is None:
            return None

        # Analyse des lignes suivantes
      # Analyse des lignes suivantes

        keywords = (
            "responsable",
            "chef",
            "ingénieur",
            "ingenieur",
            "consultant",
            "architecte",
            "développeur",
            "developpeur",
            "developer",
            "engineer",
            "manager",
            "lead",
            "cto",
            "cio",
            "dsi",
            "directeur",
            "analyste",
            "analyst",
            "product owner",
            "scrum",
            "pmo",
        )

        for line in lines[start:]:

            lower = line.lower().strip()

            if any(word in lower for word in keywords):
                return line

        return None