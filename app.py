import streamlit as st

from src.search import search_jobs
from src.database import init_database
from src.profile_manager import ProfileManager

# ----------------------------------------------------
# Initialisation
# ----------------------------------------------------

init_database()

st.set_page_config(
    page_title="JobAgent IA",
    page_icon="🤖",
    layout="wide"
)

st.title("🤖 JobAgent IA")
st.caption("Assistant intelligent de recherche d'emploi")

# ----------------------------------------------------
# Chargement des profils
# ----------------------------------------------------

pm = ProfileManager()
profiles = pm.list_profiles()

if not profiles:
    st.error("Aucun profil trouvé dans le dossier profiles/")
    st.stop()

profile_names = [p["name"] for p in profiles]

selected_profile = st.sidebar.selectbox(
    "Choisir un profil",
    profile_names
)

profile = next(
    p for p in profiles
    if p["name"] == selected_profile
)

# ----------------------------------------------------
# Valeurs par défaut
# ----------------------------------------------------

default_keywords = ", ".join(
    profile.get("keywords", [])
)

locations = profile.get("locations", [])

default_location = ""

if locations:
    default_location = locations[0]

salary = profile.get("salary_min", "")
remote = profile.get("remote", False)

# ----------------------------------------------------
# Interface
# ----------------------------------------------------

st.subheader(f"👤 Profil : {selected_profile}")

col1, col2 = st.columns(2)

with col1:

    keyword = st.text_input(
        "Mot-clé",
        value=default_keywords
    )

with col2:

    location = st.text_input(
        "Localisation",
        value=default_location
    )

col3, col4 = st.columns(2)

with col3:

    st.text_input(
        "Salaire minimum",
        value=str(salary),
        disabled=True
    )

with col4:

    st.checkbox(
        "Télétravail",
        value=remote,
        disabled=True
    )

# ----------------------------------------------------
# Recherche
# ----------------------------------------------------

if st.button("🔍 Rechercher", type="primary"):

    with st.spinner("Recherche en cours..."):

        jobs = search_jobs(keyword, location)

    st.success(f"{len(jobs)} offre(s) trouvée(s)")

    if jobs:

        rows = []

        for job in jobs:

            rows.append({
                "Poste": job.title,
                "Entreprise": job.company,
                "Ville": job.location,
                "Source": job.source
            })

        st.dataframe(
            rows,
            use_container_width=True
        )

    else:

        st.warning("Aucune offre trouvée.")