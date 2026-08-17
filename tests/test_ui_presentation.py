from __future__ import annotations

from types import SimpleNamespace

from src.ui.presentation import (
    NOT_AVAILABLE,
    build_dashboard_kpis,
    format_score,
)


def test_format_score_clamps_and_formats_values() -> None:
    assert format_score(82.4) == "82 %"
    assert format_score(150) == "100 %"
    assert format_score(-5) == "0 %"


def test_format_score_falls_back_when_missing() -> None:
    assert format_score(None) == NOT_AVAILABLE
    assert format_score("invalid") == NOT_AVAILABLE


def test_dashboard_kpis_use_existing_data_only() -> None:
    result = build_dashboard_kpis(
        jobs=(
            SimpleNamespace(score=80),
            SimpleNamespace(score=60),
        ),
        market_skills=("Python", "SQL"),
        gaps=("Cloud",),
    )

    assert result.relevant_jobs == "2"
    assert result.market_skills == "2"
    assert result.identified_gaps == "1"
    assert result.profile_fit == "70 %"


def test_dashboard_kpis_do_not_invent_missing_data() -> None:
    result = build_dashboard_kpis(jobs=())

    assert result.market_skills == NOT_AVAILABLE
    assert result.identified_gaps == NOT_AVAILABLE
    assert result.profile_fit == NOT_AVAILABLE
