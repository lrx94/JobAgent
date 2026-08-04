from __future__ import annotations

from .semantic_matcher import SemanticMatcher
from .skill_extractor import SkillExtractor
from .skill_normalizer import SkillNormalizer


__all__ = [
    "SemanticMatcher",
    "SkillExtractor",
    "SkillNormalizer",
    "OpenAIClient",
]


def __getattr__(
    name: str,
):
    """
    Charge OpenAIClient uniquement lorsqu'il est
    explicitement demandé.

    Le cœur déterministe de JobAgent reste ainsi
    utilisable sans dépendance OpenAI installée.
    """

    if name == "OpenAIClient":
        from .openai_client import (
            OpenAIClient,
        )

        return OpenAIClient

    raise AttributeError(
        f"module {__name__!r} "
        f"has no attribute {name!r}"
    )