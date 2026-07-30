import streamlit as st


def display_dashboard(jobs):

    if not jobs:
        return

    nb_jobs = len(jobs)

    average = round(
        sum(job.score for job in jobs) / nb_jobs
    )

    excellent = len(
        [j for j in jobs if j.score >= 80]
    )

    remote = len(
        [
            j
            for j in jobs
            if "remote" in j.location.lower()
        ]
    )

    c1, c2, c3, c4 = st.columns(4)

    c1.metric(
        "📄 Offres",
        nb_jobs
    )

    c2.metric(
        "⭐ Score moyen",
        f"{average}%"
    )

    c3.metric(
        "🟢 >80 %",
        excellent
    )

    c4.metric(
        "🏠 Remote",
        remote
    )

    st.divider()