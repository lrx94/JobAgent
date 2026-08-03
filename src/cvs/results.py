from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from src.cvs.models import CVDocument


@dataclass(frozen=True, slots=True)
class CVAnalysisResult:
    """
    Résultat de l’analyse métier d’un CV.
    """

    text: str
    skills: tuple[str, ...] = ()
    character_count: int = 0
    word_count: int = 0

    def __post_init__(self) -> None:
        normalized_text = str(
            self.text or ""
        ).strip()

        object.__setattr__(
            self,
            "text",
            normalized_text,
        )

        normalized_skills: list[str] = []
        seen: set[str] = set()

        for value in self.skills or ():
            skill = str(
                value or ""
            ).strip().casefold()

            if not skill or skill in seen:
                continue

            seen.add(skill)
            normalized_skills.append(skill)

        object.__setattr__(
            self,
            "skills",
            tuple(normalized_skills),
        )

        object.__setattr__(
            self,
            "character_count",
            len(normalized_text),
        )

        object.__setattr__(
            self,
            "word_count",
            len(normalized_text.split()),
        )

    @property
    def has_text(self) -> bool:
        return bool(self.text)

    @property
    def has_skills(self) -> bool:
        return bool(self.skills)

    def to_dict(self) -> dict[str, Any]:
        return {
            "text": self.text,
            "skills": list(self.skills),
            "character_count": (
                self.character_count
            ),
            "word_count": self.word_count,
            "has_text": self.has_text,
            "has_skills": self.has_skills,
        }


@dataclass(frozen=True, slots=True)
class CVImportResult:
    """
    Résultat complet de l’import d’un CV.
    """

    document: CVDocument
    analysis: CVAnalysisResult | None = None
    duplicate_reused: bool = False
    warnings: tuple[str, ...] = field(
        default_factory=tuple
    )

    @property
    def cv_id(self) -> str:
        return self.document.cv_id

    @property
    def title(self) -> str:
        return self.document.title

    @property
    def skills(self) -> tuple[str, ...]:
        if self.analysis is None:
            return ()

        return self.analysis.skills

    @property
    def analyzed(self) -> bool:
        return self.analysis is not None

    def to_dict(self) -> dict[str, Any]:
        return {
            "document": self.document.to_dict(),
            "analysis": (
                self.analysis.to_dict()
                if self.analysis is not None
                else None
            ),
            "duplicate_reused": (
                self.duplicate_reused
            ),
            "warnings": list(self.warnings),
            "analyzed": self.analyzed,
        }