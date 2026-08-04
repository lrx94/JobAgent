from __future__ import annotations

from dataclasses import dataclass


EVIDENCE_SOURCES = {
    "cv",
    "job",
    "profile",
    "market",
    "catalog",
    "unknown",
}


@dataclass(
    frozen=True,
    slots=True,
)
class Evidence:
    """
    Élément textuel justifiant une information extraite.

    Une preuve reste indépendante du parser qui l'a produite.
    """

    value: str
    source: str = "unknown"
    excerpt: str = ""
    confidence: float = 1.0
    reference_id: str | None = None

    def __post_init__(self) -> None:
        normalized_value = str(
            self.value or ""
        ).strip()

        if not normalized_value:
            raise ValueError(
                "Evidence.value est obligatoire."
            )

        normalized_source = str(
            self.source or "unknown"
        ).strip().casefold()

        if normalized_source not in EVIDENCE_SOURCES:
            normalized_source = "unknown"

        normalized_excerpt = str(
            self.excerpt or ""
        ).strip()

        normalized_confidence = max(
            0.0,
            min(
                float(
                    self.confidence
                    if self.confidence is not None
                    else 1.0
                ),
                1.0,
            ),
        )

        normalized_reference_id = (
            str(self.reference_id).strip()
            if self.reference_id is not None
            else None
        )

        if not normalized_reference_id:
            normalized_reference_id = None

        object.__setattr__(
            self,
            "value",
            normalized_value,
        )

        object.__setattr__(
            self,
            "source",
            normalized_source,
        )

        object.__setattr__(
            self,
            "excerpt",
            normalized_excerpt,
        )

        object.__setattr__(
            self,
            "confidence",
            normalized_confidence,
        )

        object.__setattr__(
            self,
            "reference_id",
            normalized_reference_id,
        )

    def to_dict(self) -> dict[str, object]:
        return {
            "value": self.value,
            "source": self.source,
            "excerpt": self.excerpt,
            "confidence": self.confidence,
            "reference_id": self.reference_id,
        }