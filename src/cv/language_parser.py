from __future__ import annotations

from src.domain import Language

from .normalizers import (
    LanguageNormalizer,
    TextNormalizer,
)


class LanguageParser:
    """Parse la section Langues."""

    def parse(self, text: str) -> list[Language]:
        languages = []

        for line in text.splitlines():
            line = line.strip()

            if not line:
                continue

            languages.append(
                Language(
                    name=LanguageNormalizer.normalize(
                        TextNormalizer.normalize(line)
                    )
                )
            )

        return languages