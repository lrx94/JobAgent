from __future__ import annotations

import re

from src.domain import Experience


class ExperienceParser:
    """
    Parse la section 'Expériences professionnelles'
    et retourne une liste d'objets Experience.
    """

    PERIOD_RE = re.compile(
        r"^(De\s+\d{4}|De\s+[A-Za-zÀ-ÿ]+\s+\d{4}|D'[A-Za-zÀ-ÿ]+\s+\d{4})",
        re.IGNORECASE,
    )

    def parse(self, text: str) -> list[Experience]:

        if not text.strip():
            return []

        blocks = self._split(text)

        experiences: list[Experience] = []

        for block in blocks:
            experience = self._parse_block(block)

            if experience is not None:
                experiences.append(experience)

        return experiences

    def _split(self, text: str) -> list[str]:

        lines = [
            line.strip()
            for line in text.splitlines()
            if line.strip()
        ]

        blocks: list[list[str]] = []
        current: list[str] = []

        for line in lines:

            if self.PERIOD_RE.match(line):

                if current:
                    blocks.append(current)

                current = [line]

            else:
                current.append(line)

        if current:
            blocks.append(current)

        return [
            "\n".join(block)
            for block in blocks
        ]

    def _parse_block(self, block: str) -> Experience | None:

        lines = [
            line.strip()
            for line in block.splitlines()
            if line.strip()
        ]

        if len(lines) < 5:
            return None

        if lines[0].startswith("D'"):

            period = f"{lines[0]} {lines[1]}"

            company = lines[2]
            location = lines[3]
            title = lines[4]
            description = "\n".join(lines[5:])

        else:

            period = lines[0]

            company = lines[1]
            location = lines[2]
            title = lines[3]
            description = "\n".join(lines[4:])

        return Experience(
            company=company,
            title=title,
            location=location,
            period=period,
            description=description,
        )