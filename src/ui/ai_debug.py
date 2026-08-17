from __future__ import annotations

from collections.abc import Mapping
from typing import Any

import streamlit as st

from src.domain import Job


DIMENSION_LABELS = {
    "hard_skills": "Compétences techniques",
    "soft_skills": "Compétences comportementales",
    "experience": "Expérience",
    "seniority": "Seniorité",
    "management": "Management",
    "certifications": "Certifications",
    "languages": "Langues",
}


def get_structured_details(
    job: Job,
) -> dict[str, Any] | None:
    """
    Retourne les données du score structuré lorsqu'elles
    sont disponibles et exploitables.
    """

    _validate_job_contract(job)

    match_details = getattr(job, "match_details")
    details = (
        match_details.get("structured")
        if isinstance(match_details, Mapping)
        else None
    )

    if not isinstance(details, Mapping):
        return None

    return dict(details)


def _validate_job_contract(job: object) -> None:
    """Valide la frontière UI, y compris après un hot reload Streamlit."""

    required_attributes = (
        "score",
        "match_details",
    )

    if all(
        hasattr(job, attribute)
        for attribute in required_attributes
    ):
        match_details = getattr(job, "match_details")

        if isinstance(match_details, Mapping):
            return

    raise TypeError(
        "job doit respecter le contrat Job "
        "(score et match_details mapping)."
    )


def render_ai_debug(
    job: Job,
) -> bool:
    """
    Affiche la comparaison entre le score historique
    et le score structuré.

    Aucun calcul n'est effectué ici. La fonction lit
    uniquement Job.match_details["structured"].

    Retourne True lorsque le panneau a été affiché.
    """

    details = get_structured_details(job)

    if details is None:
        return False

    legacy_score = _safe_float(
        details.get(
            "legacy_score",
            getattr(job, "score"),
        )
    )

    structured_score = _safe_float(
        details.get("global_score")
    )

    difference = (
        structured_score
        - legacy_score
    )

    with st.expander(
        "📊 Analyse IA détaillée",
        expanded=False,
    ):
        _render_score_summary(
            legacy_score=legacy_score,
            structured_score=structured_score,
            difference=difference,
        )

        _render_dimensions(
            details.get("dimensions")
        )

        _render_values(
            title="✅ Forces détectées",
            values=details.get("strengths"),
            empty_message=(
                "Aucune force structurée détectée."
            ),
        )

        _render_values(
            title="⚠️ Écarts détectés",
            values=details.get("gaps"),
            empty_message=(
                "Aucun écart structuré détecté."
            ),
        )

        warnings = _normalize_values(
            details.get("warnings")
        )

        for warning in warnings:
            st.warning(warning)

        version = str(
            details.get("version")
            or "inconnue"
        ).strip()

        st.caption(
            f"Version du scoring structuré : {version}"
        )

    return True


def _render_score_summary(
    *,
    legacy_score: float,
    structured_score: float,
    difference: float,
) -> None:
    legacy_column, structured_column, delta_column = (
        st.columns(3)
    )

    legacy_column.metric(
        "Score historique",
        f"{legacy_score:.1f} %",
    )

    structured_column.metric(
        "Score structuré",
        f"{structured_score:.1f} %",
    )

    delta_column.metric(
        "Écart",
        f"{difference:+.1f}",
    )


def _render_dimensions(
    raw_dimensions: Any,
) -> None:
    dimensions = _normalize_dimensions(
        raw_dimensions
    )

    if not dimensions:
        st.info(
            "Aucun sous-score disponible."
        )
        return

    st.write("#### Sous-scores")

    rows = []

    for dimension in dimensions:
        name = str(
            dimension.get("name")
            or "unknown"
        ).strip()

        score = _safe_float(
            dimension.get("score")
        )

        weight = _safe_float(
            dimension.get("weight")
        )

        rows.append(
            {
                "Dimension": (
                    DIMENSION_LABELS.get(
                        name,
                        name.replace(
                            "_",
                            " ",
                        ).title(),
                    )
                ),
                "Score": f"{score:.1f} %",
                "Poids": f"{weight * 100:.1f} %",
                "Explication": str(
                    dimension.get(
                        "explanation"
                    )
                    or ""
                ).strip(),
            }
        )

    st.dataframe(
        rows,
        width="stretch",
        hide_index=True,
    )

    with st.expander(
        "Pourquoi ce score ?",
        expanded=False,
    ):
        for dimension in dimensions:
            _render_dimension_explanation(
                dimension
            )


def _render_dimension_explanation(
    dimension: Mapping[str, Any],
) -> None:
    name = str(
        dimension.get("name")
        or "unknown"
    ).strip()

    label = DIMENSION_LABELS.get(
        name,
        name.replace("_", " ").title(),
    )

    score = _safe_float(
        dimension.get("score")
    )

    st.write(
        f"**{label} — {score:.1f} %**"
    )

    matched = _normalize_values(
        dimension.get("matched")
    )

    missing = _normalize_values(
        dimension.get("missing")
    )

    explanation = str(
        dimension.get("explanation")
        or ""
    ).strip()

    if explanation:
        st.caption(explanation)

    for value in matched:
        st.write(f"🟢 {value}")

    for value in missing:
        st.write(f"🟠 {value}")

    if not matched and not missing:
        st.write(
            "Aucun élément détaillé."
        )


def _render_values(
    *,
    title: str,
    values: Any,
    empty_message: str,
) -> None:
    normalized_values = _normalize_values(
        values
    )

    st.write(f"#### {title}")

    if not normalized_values:
        st.caption(empty_message)
        return

    for value in normalized_values:
        st.write(f"- {value}")


def _normalize_dimensions(
    values: Any,
) -> tuple[dict[str, Any], ...]:
    if not isinstance(
        values,
        (list, tuple),
    ):
        return ()

    result: list[dict[str, Any]] = []

    for value in values:
        if isinstance(value, Mapping):
            result.append(
                dict(value)
            )

    return tuple(result)


def _normalize_values(
    values: Any,
) -> tuple[str, ...]:
    if not isinstance(
        values,
        (list, tuple, set),
    ):
        return ()

    result: list[str] = []
    seen: set[str] = set()

    for value in values:
        cleaned = str(
            value or ""
        ).strip()

        if not cleaned:
            continue

        identity = cleaned.casefold()

        if identity in seen:
            continue

        seen.add(identity)
        result.append(cleaned)

    return tuple(result)


def _safe_float(
    value: Any,
) -> float:
    try:
        return float(
            value or 0.0
        )
    except (
        TypeError,
        ValueError,
    ):
        return 0.0
