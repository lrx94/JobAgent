from __future__ import annotations


class SkillExtractor:
    """
    Extrait les lignes de compétences d'une section 'Compétences'.

    Cette première version est volontairement simple.
    Elle ne fait qu'éliminer les lignes vides.
    """

    def extract(self, text: str) -> list[str]:
        if not text:
            return []

        skills: list[str] = []

        for line in text.splitlines():
            line = line.strip()

            if not line:
                continue

            skills.append(line)

        return skills