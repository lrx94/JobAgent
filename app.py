import streamlit as st
from src.ui.job_card import display_job
from src.profile import Profile
from src.profile_manager import ProfileManager
from src.services.job_service import JobService
from src.ui.dashboard import display_dashboard
from src.storage.database import init_database
from src.storage.repository import JobRepository

# --------------------------------------------------
# Configuration de la page
# --------------------------------------------------

st.set_page_config(
    page_title="JobAgent",
    page_icon="🤖",
    layout="wide"
)

st.title("🤖 JobAgent")
st.caption("Assistant intelligent de recherche d'emploi")

# --------------------------------------------------
# Chargement des profils
# --------------------------------------------------

pm = ProfileManager()
profiles = pm.list_profiles()

if not profiles:
    st.error("Aucun profil trouvé.")
    st.stop()

profile_names = [p["name"] for p in profiles]

selected_profile = st.sidebar.selectbox(
    "Profil",
    profile_names
)

profile_data = next(
    p for p in profiles
    if p["name"] == selected_profile
)

profile = Profile(
    name=profile_data["name"],
    keywords=profile_data.get("keywords", []),
    locations=profile_data.get("locations", []),
    salary_min=profile_data.get("salary_min", 0),
    remote=profile_data.get("remote", False)
)

# --------------------------------------------------
# Informations du profil
# --------------------------------------------------

st.sidebar.markdown("---")

st.sidebar.write("### Compétences")

for skill in profile.keywords:
    st.sidebar.write("✅", skill)

st.sidebar.markdown("---")

st.sidebar.write("📍 Localisation")

if profile.locations:
    st.sidebar.write(", ".join(profile.locations))
else:
    st.sidebar.write("Toutes")

st.sidebar.markdown("---")

st.sidebar.write("💰 Salaire minimum")

if profile.salary_min:
    st.sidebar.write(f"{profile.salary_min:,} €".replace(",", " "))
else:
    st.sidebar.write("Non défini")

st.sidebar.markdown("---")

st.sidebar.write("🏠 Télétravail")

st.sidebar.write("Oui" if profile.remote else "Non")

# --------------------------------------------------
# Recherche
# --------------------------------------------------

service = JobService()


init_database()

repository = JobRepository()

if st.button("🔍 Rechercher des offres", use_container_width=True):

    with st.spinner("Recherche des offres..."):

        jobs = service.search(profile)
        for job in jobs:
            repository.save(job)
        display_dashboard(jobs)
        

    st.success(f"{len(jobs)} offre(s) trouvée(s)")

    st.divider()

    for job in jobs:

         display_job(job)