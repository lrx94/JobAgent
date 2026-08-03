"""
Découpe un CV en sections à partir de leurs titres.

Le parser ne comprend pas le contenu.
Il identifie uniquement les bornes des sections.
"""

from __future__ import annotations
from src.utils import normalize_text

class SectionParser:

    HEADERS = {
        "education": [
            "diplômes et formations",
            "diplômes",
            "formations",
            "formation",
        ],

        "languages": [
            "langues",
        ],

        "interests": [
            "centres d'intérêt",
            "centres d'interet",
            "loisirs",
            "hobbies",
        ],

        "skills": [
            "domaines d'expertise",
            "compétences",
            "competences",
            "expertise",
            "technologies",
        ],

        "experiences": [
            "expériences professionnelles",
            "expérience professionnelle",
            "experiences professionnelles",
            "experience professionnelle",
        ],
    }

    ORDER = [
        "summary",
        "education",
        "languages",
        "interests",
        "skills",
        "experiences",
    ]

    def parse(self, text: str) -> dict[str, str]:

        lines = [
            line.strip()
            for line in text.splitlines()
            if line.strip()
        ]

        positions = {}

        # Localisation des titres
        for index, line in enumerate(lines):

            lower = normalize_text(line)

            for section, headers in self.HEADERS.items():

                if section in positions:
                    continue

                if lower in (
                    normalize_text(header)
                    for header in headers
                ):
                    positions[section] = index
                    break
        
        sections = {}

        # Summary = début du document jusqu'à la première section
        first = min(positions.values())

        sections["summary"] = "\n".join(lines[:first])

        # Découpage entre les sections
        for i, section in enumerate(self.ORDER[1:]):

            if section not in positions:
                sections[section] = ""
                continue

            start = positions[section] + 1

            end = len(lines)

            for next_section in self.ORDER[i + 2:]:

                if next_section in positions:
                    end = positions[next_section]
                    break

            sections[section] = "\n".join(
                lines[start:end]
            )

        return sections