from __future__ import annotations

from collections.abc import Iterable
from typing import Any

import streamlit as st

from src.ui.presentation import build_dashboard_kpis


def display_dashboard(
    jobs: Iterable[Any],
    *,
    market_skills: Iterable[Any] | None = None,
    gaps: Iterable[Any] | None = None,
) -> None:
    values = tuple(jobs or ())
    kpis = build_dashboard_kpis(
        jobs=values,
        market_skills=market_skills,
        gaps=gaps,
    )

    st.html('<div class="ja-eyebrow">Vue synthétique</div>')
    st.subheader("Tableau de bord")

    with st.container(horizontal=True):
        st.metric("Offres pertinentes", kpis.relevant_jobs, border=True)
        st.metric("Compétences marché", kpis.market_skills, border=True)
        st.metric("Gaps identifiés", kpis.identified_gaps, border=True)
        st.metric("Adéquation profil", kpis.profile_fit, border=True)

    if not values:
        st.caption("Les indicateurs seront complétés après une recherche.")
        return

    left, right = st.columns([1.6, 1], gap="large")
    with left:
        with st.container(border=True):
            st.subheader("Dernières offres pertinentes")
            for job in values[:5]:
                title = str(getattr(job, "title", "") or "Offre sans titre")
                company = str(getattr(job, "company", "") or "Entreprise non renseignée")
                location = str(getattr(job, "location", "") or "Localisation non renseignée")
                score = getattr(job, "score", None)
                st.markdown(f"**{title}** · {score if score is not None else '—'} %")
                st.caption(f"{company} · {location}")
    with right:
        with st.container(border=True):
            st.subheader("Suggestions d’apprentissage")
            st.caption(
                "Les compétences manquantes prioritaires apparaissent dans le panneau Learning."
                if gaps is None
                else f"{len(tuple(gaps))} gap(s) identifié(s)."
            )
            st.button("Voir Learning", icon=":material/school:", key="dashboard_learning_shortcut")

    market_col, actions_col = st.columns([1.6, 1], gap="large")
    with market_col:
        with st.container(border=True):
            st.subheader("Aperçu de votre marché")
            st.caption("Analyse basée uniquement sur les résultats déjà collectés.")
            st.write(f"**Volume analysé :** {len(values)} offre(s)")
    with actions_col:
        with st.container(border=True):
            st.subheader("Raccourcis rapides")
            st.caption("Recherche, CV, profils et rapport restent accessibles dans cet espace.")
