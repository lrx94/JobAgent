from __future__ import annotations

import streamlit as st

from src.profile_manager import ProfileManager
from src.services.job_service import JobService
from src.storage.database import init_database
from src.storage.repository import JobRepository
from src.ui.dashboard import display_dashboard
from src.ui.job_card import display_job


# --------------------------------------------------
# Configuration de la page
# --------------------------------------------------

st.set_page_config(
    page_title="JobAgent",
    page_icon="🤖",
    layout="wide",
)

st.title("🚀 JobAgent")
st.caption(
    "Votre assistant intelligent de recherche d'emploi"
)

st.divider()


# --------------------------------------------------
# Initialisation des services
# --------------------------------------------------

@st.cache_resource
def create_job_service() -> JobService:
    """
    Crée une instance unique du service de recherche.
    """

    return JobService()


@st.cache_resource
def create_repository() -> JobRepository:
    """
    Initialise la base et crée une instance unique du repository.
    """

    init_database()

    return JobRepository()


profile_manager = ProfileManager()
job_service = create_job_service()
job_repository = create_repository()


# --------------------------------------------------
# Chargement des profils
# --------------------------------------------------

profile_names = profile_manager.list_profiles()

if not profile_names:
    st.error(
        "Aucun profil valide n'a été trouvé dans le dossier profiles."
    )
    st.stop()

selected_profile_name = st.sidebar.selectbox(
    "Profil",
    profile_names,
)

try:
    profile = profile_manager.load_profile(
        selected_profile_name
    )

except (FileNotFoundError, ValueError, OSError) as error:
    st.error(
        "Impossible de charger le profil sélectionné."
    )

    st.exception(error)
    st.stop()


# --------------------------------------------------
# Informations du profil
# --------------------------------------------------

st.sidebar.markdown("---")
st.sidebar.write("### 👤 Profil")
st.sidebar.write(profile.name)

st.sidebar.markdown("---")
st.sidebar.write("### 🛠️ Compétences")

if profile.keywords:
    for skill in profile.keywords:
        st.sidebar.write(f"✅ {skill}")
else:
    st.sidebar.write("Aucune compétence définie")

st.sidebar.markdown("---")
st.sidebar.write("### 📍 Localisation")

if profile.locations:
    st.sidebar.write(
        ", ".join(profile.locations)
    )
else:
    st.sidebar.write("Toutes")

st.sidebar.markdown("---")
st.sidebar.write("### 💰 Salaire minimum")

if profile.salary_min:
    formatted_salary = (
        f"{profile.salary_min:,}"
        .replace(",", " ")
    )

    st.sidebar.write(
        f"{formatted_salary} €"
    )
else:
    st.sidebar.write("Non défini")

st.sidebar.markdown("---")
st.sidebar.write("### 🏠 Télétravail")
st.sidebar.write(
    "Oui"
    if profile.remote
    else "Non"
)


# --------------------------------------------------
# Résumé de la recherche
# --------------------------------------------------

st.subheader("🎯 Paramètres de recherche")

column_profile, column_skills, column_location, column_remote = (
    st.columns(4)
)

displayed_keywords = (
    ", ".join(profile.keywords[:3])
    if profile.keywords
    else "-"
)

if len(profile.keywords) > 3:
    displayed_keywords += "…"

displayed_locations = (
    ", ".join(profile.locations)
    if profile.locations
    else "Toutes"
)

column_profile.metric(
    "👤 Profil",
    profile.name,
)

column_skills.metric(
    "🛠️ Compétences",
    displayed_keywords,
)

column_location.metric(
    "📍 Zone",
    displayed_locations,
)

column_remote.metric(
    "🏠 Remote",
    "Oui"
    if profile.remote
    else "Non",
)

st.divider()


# --------------------------------------------------
# Recherche des offres
# --------------------------------------------------

search_clicked = st.button(
    "🔍 Rechercher des offres",
    use_container_width=True,
    type="primary",
)

if search_clicked:
    try:
        with st.spinner(
            "Recherche et analyse des offres en cours..."
        ):
            jobs = job_service.search(profile)

            if jobs is None:
                jobs = []

            for job in jobs:
                try:
                    job_repository.save(job)

                except Exception as repository_error:
                    st.warning(
                        "Une offre n'a pas pu être enregistrée "
                        "dans la base locale."
                    )

                    st.caption(
                        str(repository_error)
                    )

    except Exception as search_error:
        st.error(
            "Une erreur est survenue pendant la recherche."
        )

        st.exception(search_error)
        st.stop()

    if not jobs:
        st.warning(
            "Aucune offre n'a été trouvée pour ce profil."
        )

        st.stop()

    scores = [
        float(getattr(job, "score", 0) or 0)
        for job in jobs
    ]

    best_score = round(
        max(scores)
    )

    average_score = round(
        sum(scores) / len(scores)
    )

    st.success(
        f"{len(jobs)} offre(s) trouvée(s)"
    )

    st.caption(
        f"🔍 {len(jobs)} offres analysées • "
        f"🏆 Meilleur score : {best_score}% • "
        f"⭐ Moyenne : {average_score}%"
    )

    st.divider()

    # Vue synthétique du tableau de bord.
    display_dashboard(jobs)

    st.divider()
    st.subheader("📋 Détail des offres")

    # Vue détaillée de chaque offre.
    for job in jobs:
        display_job(job)