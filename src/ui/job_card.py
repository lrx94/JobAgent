from __future__ import annotations

from typing import Any

import streamlit as st

from src.ui.ai_debug import render_ai_debug
from src.ui.presentation import format_score
from src.ui.score_utils import score_progress, score_summary


def display_job(job: Any) -> None:
    with st.container(border=True):
        heading, score_column = st.columns([5, 1], vertical_alignment="center")
        with heading:
            st.subheader(str(getattr(job, "title", "") or "Offre sans titre"))
            company = str(getattr(job, "company", "") or "Entreprise non renseignée")
            location = str(getattr(job, "location", "") or "Localisation non renseignée")
            source = str(getattr(job, "source", "") or "Source non renseignée")
            remote = _remote_label(job)
            st.caption(f"{company} · {location} · {remote} · {source}")
        with score_column:
            st.metric("Adéquation", format_score(getattr(job, "score", None)))

        st.progress(score_progress(getattr(job, "score", 0) or 0))
        st.caption(score_summary(job))

        matched = tuple(getattr(job, "matched_skills", ()) or ())
        if matched:
            st.markdown("**Compétences correspondantes**")
            st.caption(" · ".join(str(skill) for skill in matched[:6]))

        with st.expander("Détails de l’offre", icon=":material/expand_more:"):
            details = getattr(job, "match_details", {}) or {}
            if details:
                st.write("**Pourquoi ce score ?**")
                st.json(details, expanded=False)

            missing = tuple(getattr(job, "missing_skills", ()) or ())
            if missing:
                st.write("**Compétences à développer**")
                st.caption(" · ".join(str(skill) for skill in missing))

            description = str(getattr(job, "description", "") or "")
            if description:
                st.write(description[:1200] + ("…" if len(description) > 1200 else ""))

            render_ai_debug(job)

            url = str(getattr(job, "url", "") or "")
            if url:
                st.link_button(
                    "Consulter l’offre",
                    url,
                    icon=":material/open_in_new:",
                    width="stretch",
                )


def _remote_label(job: Any) -> str:
    remote_type = str(getattr(job, "remote_type", "") or "").strip().casefold()
    if remote_type and remote_type != "unknown":
        return remote_type.capitalize()
    if bool(getattr(job, "remote", False)):
        return "Télétravail"
    return "Mode de travail non renseigné"
