import streamlit as st

from src.ui.score_utils import (
    score_badge,
    score_summary,
    score_progress,
)


def display_job(job):

    with st.container(border=True):

        col1, col2 = st.columns([4, 1])

        with col1:

            st.subheader(job.title)

            st.write(f"🏢 {job.company}")

            st.write(f"📍 {job.location}")

            st.caption(job.source)

        with col2:

            st.metric(
                "Matching",
                f"{job.score}%"
            )

        # Barre de progression
        st.progress(score_progress(job.score))

        # Badge
        st.markdown(f"### {score_badge(job.score)}")

        # Résumé
        st.info(score_summary(job))

        # Détails du score
        if job.match_details:

            with st.expander("📊 Pourquoi ce score ?"):

                st.write(
                    f"🧠 Compétences : {job.match_details.get('skills', 0)} pts"
                )

                st.write(
                    f"📍 Localisation : {job.match_details.get('location', 0)} pts"
                )

                st.write(
                    f"🏠 Télétravail : {job.match_details.get('remote', 0)} pts"
                )

                st.write(
                    f"💰 Salaire : {job.match_details.get('salary', 0)} pts"
                )

        # Compétences trouvées
        if job.matched_skills:

            st.success(
                "✔ " + " • ".join(job.matched_skills)
            )

        # Compétences manquantes
        if job.missing_skills:

            st.warning(
                "❌ " + " • ".join(job.missing_skills)
            )

        # Description
        if job.description:

            with st.expander("📄 Description"):

                st.write(job.description)

        # Lien
        if job.url:

            st.link_button(
                "Voir l'offre",
                job.url,
                use_container_width=True,
            )