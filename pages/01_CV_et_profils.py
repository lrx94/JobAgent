from __future__ import annotations

import tempfile
from pathlib import Path

import streamlit as st

from src.career import (
    CVProfileService,
)


st.set_page_config(
    page_title="CV et profils",
    page_icon="📄",
    layout="wide",
)

st.title("📄 CV et profils")
st.caption(
    "Analysez un CV, choisissez un métier cible "
    "et créez ou enrichissez un profil JobAgent."
)


@st.cache_resource
def create_cv_profile_service() -> CVProfileService:
    return CVProfileService(
        profiles_directory="profiles"
    )


service = create_cv_profile_service()


def initialize_state() -> None:
    defaults = {
        "cv_analysis": None,
        "cv_temporary_path": None,
        "cv_original_name": None,
    }

    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def save_uploaded_pdf(
    uploaded_file,
) -> Path:
    """
    Copie le PDF envoyé dans un fichier temporaire persistant
    pendant la session Streamlit.
    """

    suffix = Path(
        uploaded_file.name
    ).suffix or ".pdf"

    temporary_file = tempfile.NamedTemporaryFile(
        prefix="jobagent_cv_",
        suffix=suffix,
        delete=False,
    )

    temporary_file.write(
        uploaded_file.getvalue()
    )

    temporary_file.flush()
    temporary_file.close()

    return Path(
        temporary_file.name
    )


def comma_separated(
    values,
) -> str:
    return ", ".join(
        str(value)
        for value in values or []
    )


initialize_state()

uploaded_cv = st.file_uploader(
    "Déposer un CV au format PDF",
    type=["pdf"],
    accept_multiple_files=False,
)

analyze_clicked = st.button(
    "🔎 Analyser le CV",
    type="primary",
    use_container_width=True,
    disabled=uploaded_cv is None,
)

if analyze_clicked and uploaded_cv is not None:
    try:
        temporary_path = save_uploaded_pdf(
            uploaded_cv
        )

        with st.spinner(
            "Extraction du texte, des compétences "
            "et des métiers probables..."
        ):
            analysis = service.analyze_pdf(
                temporary_path,
                limit=5,
            )

        st.session_state[
            "cv_analysis"
        ] = analysis

        st.session_state[
            "cv_temporary_path"
        ] = str(
            temporary_path
        )

        st.session_state[
            "cv_original_name"
        ] = uploaded_cv.name

        st.success(
            "Le CV a été analysé."
        )

    except Exception as error:
        st.error(
            "L'analyse du CV a échoué."
        )

        st.exception(error)

analysis = st.session_state.get(
    "cv_analysis"
)

if analysis is None:
    st.info(
        "Déposez un CV puis lancez l'analyse."
    )

    st.stop()


st.divider()
st.subheader("1. Résultat de l'analyse")

column_title, column_seniority, column_skills = (
    st.columns(3)
)

column_title.metric(
    "Métier principal",
    analysis.suggested_title,
)

column_seniority.metric(
    "Séniorité",
    analysis.seniority,
)

column_skills.metric(
    "Compétences détectées",
    len(
        analysis.extracted_skills
    ),
)

if analysis.warnings:
    for warning in analysis.warnings:
        st.warning(warning)

st.write("#### Compétences extraites")

if analysis.extracted_skills:
    st.write(
        ", ".join(
            analysis.extracted_skills
        )
    )
else:
    st.write(
        "Aucune compétence normalisée détectée."
    )


st.divider()
st.subheader("2. Choisir le métier cible")

if not analysis.role_suggestions:
    st.error(
        "Aucun métier exploitable n'a été proposé."
    )

    st.stop()

role_by_label = {
    (
        f"{suggestion.label} "
        f"— {suggestion.score:.2f}%"
    ): suggestion
    for suggestion in analysis.role_suggestions
}

selected_label = st.selectbox(
    "Métier proposé",
    options=list(
        role_by_label.keys()
    ),
)

selected_role = role_by_label[
    selected_label
]

column_score, column_providers = st.columns(
    [
        1,
        2,
    ]
)

column_score.metric(
    "Indice de correspondance",
    f"{selected_role.score:.2f}%",
)

column_providers.write(
    "**Sources recommandées**"
)

column_providers.write(
    ", ".join(
        selected_role.preferred_providers
    )
    or "Aucune source recommandée"
)

with st.expander(
    "Voir le détail de la proposition",
    expanded=False,
):
    st.write(
        "**Intitulés trouvés :**",
        list(
            selected_role.matched_aliases
        )
        or "Aucun",
    )

    st.write(
        "**Compétences associées :**",
        list(
            selected_role.matched_skills
        )
        or "Aucune",
    )

    st.write(
        "**Compétences cœur absentes :**",
        list(
            selected_role
            .missing_core_skills
        )
        or "Aucune",
    )


generated_preview = service.build_profile(
    analysis=analysis,
    role_id=selected_role.role_id,
    locations=["Remote"],
    remote=True,
)

preview_profile = (
    generated_preview.profile
)


st.divider()
st.subheader("3. Personnaliser le profil")

profile_name = st.text_input(
    "Nom du profil",
    value=preview_profile.name,
)

keywords_text = st.text_area(
    "Compétences et mots-clés",
    value=comma_separated(
        preview_profile.keywords
    ),
    height=150,
    help=(
        "Séparez les valeurs par des virgules, "
        "des points-virgules ou des retours à la ligne."
    ),
)

locations_text = st.text_input(
    "Localisations",
    value=comma_separated(
        preview_profile.locations
    ),
    help=(
        "Exemples : Paris, Lyon, Remote"
    ),
)

salary_min = st.number_input(
    "Salaire minimum annuel",
    min_value=0,
    max_value=500000,
    value=int(
        preview_profile.salary_min
        or 0
    ),
    step=1000,
)

remote = st.checkbox(
    "Télétravail accepté",
    value=bool(
        preview_profile.remote
    ),
)


st.divider()
st.subheader("4. Créer ou enrichir un profil")

existing_profiles = (
    service.list_profiles()
)

action = st.radio(
    "Action",
    options=[
        "Créer un nouveau profil",
        "Enrichir un profil existant",
    ],
    horizontal=True,
)

selected_existing_profile = None

if action == "Enrichir un profil existant":
    if existing_profiles:
        selected_existing_profile = (
            st.selectbox(
                "Profil à enrichir",
                options=existing_profiles,
            )
        )

        try:
            existing_config = (
                service.load_profile_config(
                    selected_existing_profile
                )
            )

            with st.expander(
                "Configuration actuelle",
                expanded=False,
            ):
                st.json(
                    existing_config
                )

        except Exception as error:
            st.warning(
                "Impossible de prévisualiser "
                "la configuration actuelle."
            )

            st.caption(
                str(error)
            )

    else:
        st.warning(
            "Aucun profil existant n'est disponible."
        )


save_clicked = st.button(
    "💾 Enregistrer le profil",
    type="primary",
    use_container_width=True,
    disabled=(
        action
        == "Enrichir un profil existant"
        and not selected_existing_profile
    ),
)

if save_clicked:
    try:
        final_generated = (
            service.build_profile(
                analysis=analysis,
                role_id=(
                    selected_role.role_id
                ),
                keywords=keywords_text,
                locations=locations_text,
                salary_min=int(
                    salary_min
                ),
                remote=remote,
                profile_name=profile_name,
            )
        )

        cv_path = st.session_state.get(
            "cv_temporary_path"
        )

        if action == "Créer un nouveau profil":
            result = service.create_profile(
                profile=(
                    final_generated.profile
                ),
                cv_source_path=cv_path,
            )
        else:
            result = service.enrich_profile(
                profile_id=(
                    selected_existing_profile
                ),
                profile=(
                    final_generated.profile
                ),
                cv_source_path=cv_path,
            )

        st.success(
            (
                "Profil créé"
                if result.created
                else "Profil enrichi"
            )
            + f" : {result.profile_name}"
        )

        st.write(
            "**Identifiant :**",
            result.profile_id,
        )

        st.write(
            "**Configuration :**",
            str(
                result.config_path
            ),
        )

        if result.cv_path is not None:
            st.write(
                "**CV enregistré :**",
                str(
                    result.cv_path
                ),
            )

        st.cache_resource.clear()

    except Exception as error:
        st.error(
            "L'enregistrement du profil a échoué."
        )

        st.exception(error)