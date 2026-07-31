import streamlit as st


def display_dashboard(jobs):

    if not jobs:
        return

    nb_jobs = len(jobs)

    scores = [
        float(job.score or 0)
        for job in jobs
    ]

    average = round(
        sum(scores) / nb_jobs
    )

    best_score = round(
        max(scores)
    )

    excellent = len(
        [
            job
            for job in jobs
            if float(job.score or 0) >= 80
        ]
    )

    remote = len(
        [
            job
            for job in jobs
            if getattr(
                job,
                "remote_type",
                "unknown",
            ) == "remote"
            or getattr(job, "remote", False)
        ]
    )

    c1, c2, c3, c4, c5 = st.columns(5)

    c1.metric(
        "📄 Offres",
        nb_jobs,
    )

    c2.metric(
        "🏆 Meilleur",
        f"{best_score}%",
    )

    c3.metric(
        "⭐ Moyenne",
        f"{average}%",
    )

    c4.metric(
        "🟢 Excellents",
        excellent,
    )

    c5.metric(
        "🏠 Remote",
        remote,
    )

    st.divider()