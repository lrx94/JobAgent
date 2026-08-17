from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable


NOT_AVAILABLE = "Non disponible"


@dataclass(frozen=True, slots=True)
class DashboardKPI:
    relevant_jobs: str
    market_skills: str
    identified_gaps: str
    profile_fit: str


def format_score(value: Any) -> str:
    try:
        score = max(0.0, min(100.0, float(value)))
    except (TypeError, ValueError):
        return NOT_AVAILABLE
    return f"{score:.0f} %"


def build_dashboard_kpis(
    *,
    jobs: Iterable[Any] = (),
    market_skills: Iterable[Any] | None = None,
    gaps: Iterable[Any] | None = None,
) -> DashboardKPI:
    values = tuple(jobs or ())
    scored = [getattr(job, "score", None) for job in values]
    valid_scores = []
    for value in scored:
        try:
            valid_scores.append(float(value))
        except (TypeError, ValueError):
            continue
    return DashboardKPI(
        relevant_jobs=str(len(values)),
        market_skills=(str(len(tuple(market_skills))) if market_skills is not None else NOT_AVAILABLE),
        identified_gaps=(str(len(tuple(gaps))) if gaps is not None else NOT_AVAILABLE),
        profile_fit=(format_score(sum(valid_scores) / len(valid_scores)) if valid_scores else NOT_AVAILABLE),
    )
