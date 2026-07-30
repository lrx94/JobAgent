from __future__ import annotations

import re

from src.domain import (
    Certification,
    Education,
    EducationResult,
)


class EducationParser:
    """
    Parse la section 'Diplômes et Formations' d'un CV.

    Retourne :
        - les formations académiques
        - les certifications professionnelles
    """

    YEAR_RE = re.compile(r"^\d{4}$")

    CERTIFICATION_KEYWORDS = (
        "COBIT",
        "ITIL",
        "PRINCE",
        "PMP",
        "SCRUM",
        "SAFE",
        "TOGAF",
        "AWS",
        "AZURE",
        "GCP",
    )

    def parse(self, text: str) -> EducationResult:

        lines = [
            line.strip()
            for line in text.splitlines()
            if line.strip()
        ]

        educations: list[Education] = []

        current: Education | None = None

        for line in lines:

            #
            # Début d'un diplôme / certification
            #

            if re.match(r"^\d{4}\b", line):

                if current:
                    educations.append(current)

                current = Education()

                year = re.match(r"^(\d{4})", line)

                current.year = year.group(1)

                rest = line[4:].strip()

                if rest:
                    current.school = rest

                continue

            if current is None:
                continue

            #
            # Etablissement
            #

            if not current.school:

                current.school = line
                continue

            #
            # Diplôme
            #

            if not current.degree:

                current.degree = line
                continue

            #
            # Description
            #

            if current.description:
                current.description += "\n"

            current.description += line

        if current:
            educations.append(current)

        result = EducationResult()

        for education in educations:

            if self._is_certification(education):

                result.certifications.append(
                    Certification(
                        year=education.year,
                        organization=education.school,
                        name=education.degree or education.school,
                        description=education.description,
                    )
                )

            else:

                result.education.append(education)

        return result

    def _is_certification(self, education: Education) -> bool:

        text = f"{education.school} {education.degree}".upper()

        return any(
            keyword in text
            for keyword in self.CERTIFICATION_KEYWORDS
        )