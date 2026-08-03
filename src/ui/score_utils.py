"""
Utilitaires d'affichage des scores de matching.
"""

from typing import Tuple


def score_badge(score: int) -> str:
    """Retourne un badge en fonction du score."""

    if score >= 80:
        return "🟢 Excellent Match"

    if score >= 60:
        return "🔵 Très bon Match"

    if score >= 40:
        return "🟠 Bon Match"

    if score >= 20:
        return "🟡 Match Moyen"

    return "🔴 Faible Match"


def score_color(score: int) -> str:
    """Retourne une couleur compatible avec st.metric."""

    if score >= 80:
        return "normal"

    if score >= 60:
        return "normal"

    if score >= 40:
        return "off"

    return "inverse"


def score_summary(job) -> str:
    """
    Génère un résumé simple à partir du score et des compétences.
    """

    details = getattr(job, "match_details", {})

    found = details.get("matched_skills", [])

    if job.score >= 80:
        intro = "Excellente adéquation avec votre profil."

    elif job.score >= 60:
        intro = "Très bonne adéquation avec votre profil."

    elif job.score >= 40:
        intro = "Bonne adéquation avec votre profil."

    elif job.score >= 20:
        intro = "Adéquation partielle."

    else:
        intro = "Cette offre correspond peu à votre profil."

    if found:
        skills = ", ".join(found[:4])
        return f"{intro}\n\nCompétences détectées : {skills}."

    return intro


def score_progress(score: int) -> float:
    """Valeur comprise entre 0 et 1 pour st.progress()."""

    return max(0.0, min(score / 100, 1.0))


def score_icon(score: int) -> str:
    """Icône associée au niveau de matching."""

    if score >= 80:
        return "🏆"

    if score >= 60:
        return "⭐"

    if score >= 40:
        return "👍"

    if score >= 20:
        return "👌"

    return "🔎"