import streamlit as st


def display_dashboard(jobs):

    if not jobs:
        return

    nb_jobs = len(jobs)

    average = round(
        sum(job.score for job in jobs) / nb_jobs
    )

    best_score = max(job.score for job in jobs)

    excellent = len(
        [
            job
            for job in jobs
            if job.score >= 80
        ]
    )

    remote = len(
        [
            job
            for job in jobs
            if "remote" in job.location.lower()
        ]
    )

    c1, c2, c3, c4, c5 = st.columns(5)

    c1.metric(
        "📄 Offres",
        nb_jobs
    )

    c2.metric(
        "🏆 Meilleur",
        f"{best_score}%"
    )

    c3.metric(
        "⭐ Moyenne",
        f"{average}%"
    )

    c4.metric(
        "🟢 Excellents",
        excellent
    )

    c5.metric(
        "🏠 Remote",
        remote
    )

    st.divider()