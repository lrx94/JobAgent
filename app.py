from __future__ import annotations

from pathlib import Path

import streamlit as st

from src.services.job_service import JobService
from src.ui.dashboard import display_dashboard
from src.ui.job_card import display_job
from src.auth.adapters.streamlit_bootstrap import (
    require_streamlit_user,
)
from src.workspace import build_workspace
from src.workspace.search import (
    WorkspaceSearchError,
    WorkspaceSearchService,
)


STORAGE_ROOT = Path("data") / "users"


# --------------------------------------------------
# Configuration de la page
# --------------------------------------------------

st.set_page_config(
    page_title="JobAgent",
    page_icon="🤖",
    layout="wide",
)
user_context = require_streamlit_user()

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

    JobService gère désormais lui-même :
    - la collecte ;
    - le matching ;
    - la persistance SQLite ;
    - l'historisation des offres.
    """

    return JobService()


workspace = build_workspace(
    user_context=user_context,
    storage_root=STORAGE_ROOT,
)
profile_reader = WorkspaceSearchService(
    profile_service=workspace.profile_service,
)
job_service = create_job_service()


# --------------------------------------------------
# Chargement des profils
# --------------------------------------------------

profile_ids = profile_reader.list_profile_ids()

if not profile_ids:
    st.error(
        "Aucun profil n'a été trouvé dans votre espace. "
        "Créez-en un depuis Career Workspace."
    )
    st.stop()

selected_profile_id = st.sidebar.selectbox(
    "Profil",
    profile_ids,
)

try:
    profile = profile_reader.build_context(
        selected_profile_id
    ).profile

except WorkspaceSearchError as error:
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
    st.sidebar.write(
        "Aucune compétence définie"
    )

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

with st.sidebar.expander("✏️ Modifier les contraintes", expanded=False):
    with st.form(f"profile_constraints_{selected_profile_id}"):
        edited_locations = st.text_input(
            "Localisations / mobilité",
            value=", ".join(profile.locations),
        )
        edited_salary = st.number_input(
            "Salaire minimum annuel",
            min_value=0,
            step=1000,
            value=int(profile.salary_min or 0),
        )
        edited_remote = st.checkbox(
            "Télétravail accepté",
            value=bool(profile.remote),
        )
        save_constraints = st.form_submit_button(
            "Enregistrer les contraintes",
            use_container_width=True,
        )

    if save_constraints:
        try:
            updated_context = profile_reader.update_profile_constraints(
                profile_id=selected_profile_id,
                locations=edited_locations.split(","),
                salary_min=int(edited_salary),
                remote=edited_remote,
            )
        except WorkspaceSearchError as error:
            st.error(str(error))
        else:
            st.session_state["profile_constraints_success"] = (
                f"Contraintes du profil {updated_context.profile.name} enregistrées."
            )
            st.rerun()

constraints_success = st.session_state.pop(
    "profile_constraints_success",
    None,
)
if constraints_success:
    st.sidebar.success(constraints_success)


# --------------------------------------------------
# Résumé de la recherche
# --------------------------------------------------

st.subheader("🎯 Paramètres de recherche")

(
    column_profile,
    column_skills,
    column_location,
    column_remote,
) = st.columns(4)

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

    except Exception as search_error:
        st.error(
            "Une erreur est survenue pendant la recherche."
        )

        st.exception(search_error)
        st.stop()

    if job_service.provider_errors:
        for provider_error in job_service.provider_errors:
            st.warning(
                f"Erreur de collecte : {provider_error}"
            )

    if job_service.persistence_errors:
        st.warning(
            "Certaines offres n'ont pas pu être "
            "enregistrées dans la base locale."
        )

        for persistence_error in (
            job_service.persistence_errors
        ):
            st.caption(persistence_error)

    if not jobs:
        st.warning(
            "Aucune offre n'a été trouvée "
            "pour ce profil."
        )

        st.stop()

    scores = [
        float(
            getattr(job, "score", 0)
            or 0
        )
        for job in jobs
    ]

    best_score = round(
        max(scores)
    )

    average_score = round(
        sum(scores) / len(scores)
    )

    persistence_stats = (
        job_service.persistence_stats
    )

    persistence_actions = (
        job_service.persistence_actions
    )

    st.success(
        f"{len(jobs)} offre(s) trouvée(s)"
    )

    st.caption(
        f"🔍 {len(jobs)} offres analysées • "
        f"🏆 Meilleur score : {best_score}% • "
        f"⭐ Moyenne : {average_score}%"
    )

    if persistence_stats["enabled"]:
        st.caption(
            "💾 Persistance : "
            f"{persistence_stats['saved']} enregistrée(s) • "
            f"{persistence_stats['failed']} échec(s)"
        )

        st.caption(
            "🟢 "
            f"{persistence_actions['inserted']} nouvelle(s) • "
            "🟡 "
            f"{persistence_actions['updated']} mise(s) à jour • "
            "⚪ "
            f"{persistence_actions['unchanged']} inchangée(s)"
        )

    st.divider()

    display_dashboard(jobs)

    st.divider()
    st.subheader("📋 Détail des offres")

    for job in jobs:
        display_job(job)
