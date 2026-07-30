import streamlit as st


def score_color(score):

    if score >= 80:
        return "🟢"

    if score >= 60:
        return "🟠"

    return "🔴"


def display_job(job):

    color = score_color(job.score)

    with st.container(border=True):

        col1, col2 = st.columns([4, 1])

        with col1:

            st.subheader(job.title)

            st.write(f"🏢 {job.company}")

            st.write(f"📍 {job.location}")

            st.caption(job.source)

        with col2:

            st.metric(
                "",
                f"{color} {job.score}%"
            )

        if job.matched_skills:

            st.success(
                "✔ " + " • ".join(job.matched_skills)
            )

        if job.missing_skills:

            st.warning(
                "❌ " + " • ".join(job.missing_skills)
            )

        if job.description:

            with st.expander("Description"):

                st.write(job.description)

        if job.url:

            st.link_button(
                "Voir l'offre",
                job.url,
                use_container_width=True
            )