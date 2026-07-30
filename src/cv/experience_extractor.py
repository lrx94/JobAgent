"""
Extraction des expériences professionnelles depuis un CV.
"""

from __future__ import annotations

import re

from src.domain.experience import Experience


class ExperienceExtractor:

    def extract(self, text: str) -> list[Experience]:

        lines = [
            line.strip()
            for line in text.splitlines()
            if line.strip()
        ]

        # Recherche de la section Expériences professionnelles
        start = None

        for i, line in enumerate(lines):

            if "expérience" in line.lower():

                start = i + 1
                break

        if start is None:
            return []

        experiences = []

        i = start

        while i < len(lines):

            line = lines[i]

            # Début d'une nouvelle expérience
            if self._is_period(line):

                period = line

                company = ""
                location = ""
                title = ""
                description = []

                # société
                if i + 1 < len(lines):
                    company = lines[i + 1]

                # localisation
                if i + 2 < len(lines):
                    location = lines[i + 2]

                # intitulé
                if i + 3 < len(lines):
                    title = lines[i + 3]

                # description
                j = i + 4

                while j < len(lines):

                    if self._is_period(lines[j]):
                        break

                    description.append(lines[j])
                    j += 1

                experiences.append(
                    Experience(
                        company=company,
                        title=title,
                        location=location,
                        period=period,
                        description="\n".join(description),
                    )
                )

                i = j
                continue

            i += 1

        return experiences

    @staticmethod
    def _is_period(line: str) -> bool:

        lower = line.lower()

        months = (
            "jan",
            "fév",
            "fev",
            "mars",
            "avr",
            "mai",
            "juin",
            "juil",
            "août",
            "aout",
            "sept",
            "oct",
            "nov",
            "déc",
            "dec",
        )

        if any(month in lower for month in months):
            return True

        if re.search(r"\b20\d{2}\b", lower):
            return True

        return False