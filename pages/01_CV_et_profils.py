from __future__ import annotations

import tempfile
from pathlib import Path

import streamlit as st

from src.career.user_cv_profile_service import (
    UserCVProfileService,
)
from src.career.search_workflow import (
    CareerSearchWorkflow,
)
from src.auth.adapters.streamlit_bootstrap import (
    require_streamlit_user,
)


st.set_page_config(
    page_title="CV et profils",
    page_icon="📄",
    layout="wide",
)
user_context = require_streamlit_user()
st.title("📄 CV et profils")
st.caption(
    "Analysez un CV, choisissez un métier cible, "
    "créez ou enrichissez un profil puis lancez une recherche."
)
st.caption(
    "Espace utilisateur privé : "
    f"{user_context.display_name}"
)

# ---------------------------------------------------------------------------
# Services
# ---------------------------------------------------------------------------


def create_cv_profile_service(
    user_context,
) -> UserCVProfileService:
    return UserCVProfileService(
        user_context=user_context,
        storage_root=(
            Path("data")
            / "users"
        ),
    )


@st.cache_resource
def create_search_workflow() -> CareerSearchWorkflow:
    return CareerSearchWorkflow()


service = create_cv_profile_service(
    user_context
)
search_workflow = create_search_workflow()


# ---------------------------------------------------------------------------
# État de session
# ---------------------------------------------------------------------------


def initialize_state() -> None:
    defaults = {
        "cv_analysis": None,
        "cv_temporary_path": None,
        "cv_original_name": None,
        "career_generated_profile": None,
        "career_selected_role": None,
        "career_search_result": None,
        "career_saved_profile_id": None,
        "career_search_completed": False,
    }

    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


initialize_state()


# ---------------------------------------------------------------------------
# Fonctions utilitaires
# ---------------------------------------------------------------------------


def save_uploaded_pdf(
    uploaded_file,
) -> Path:
    """
    Copie le PDF envoyé dans un fichier temporaire persistant
    pendant la session Streamlit.
    """

    suffix = (
        Path(uploaded_file.name).suffix
        or ".pdf"
    )

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


def reset_search_state() -> None:
    """
    Supprime les résultats de recherche après modification
    ou nouvel enregistrement du profil.
    """

    st.session_state[
        "career_search_result"
    ] = None

    st.session_state[
        "career_search_completed"
    ] = False


def display_provider_statuses(
    search_result,
) -> None:
    st.write("#### État des providers")

    for provider_status in (
        search_result.provider_statuses
    ):
        if provider_status.operational:
            icon = "✅"

        elif (
            provider_status.status
            == "not_configured"
        ):
            icon = "⚠️"

        else:
            icon = "○"

        recommended_label = (
            " — recommandé"
            if provider_status.recommended
            else " — source secondaire"
        )

        st.write(
            f"{icon} **{provider_status.label}**"
            f"{recommended_label} : "
            f"{provider_status.message}"
        )


def display_job(
    job,
) -> None:
    with st.container(
        border=True
    ):
        st.subheader(
            job.title
        )

        job_col1, job_col2 = (
            st.columns(2)
        )

        job_col1.write(
            f"**Entreprise :** "
            f"{job.company}"
        )

        job_col2.write(
            f"**Score :** "
            f"{job.score:.1f}"
        )

        st.write(
            f"**Localisation :** "
            f"{job.location}"
        )

        st.write(
            f"**Source :** "
            f"{job.source}"
        )

        if job.matched_skills:
            st.write(
                "**Compétences communes :**",
                ", ".join(
                    job.matched_skills
                ),
            )

        if job.missing_skills:
            with st.expander(
                "Compétences absentes",
                expanded=False,
            ):
                st.write(
                    ", ".join(
                        job.missing_skills
                    )
                )

        if job.explanation:
            with st.expander(
                "Explication du score",
                expanded=False,
            ):
                st.write(
                    job.explanation
                )

        if job.url:
            st.link_button(
                "Voir l'offre",
                job.url,
            )


# ---------------------------------------------------------------------------
# Import et analyse du CV
# ---------------------------------------------------------------------------


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
    key="analyze_cv_button",
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

        st.session_state[
            "career_generated_profile"
        ] = None

        st.session_state[
            "career_selected_role"
        ] = None

        st.session_state[
            "career_saved_profile_id"
        ] = None

        reset_search_state()

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


# ---------------------------------------------------------------------------
# Étape 1 — Résultat de l'analyse
# ---------------------------------------------------------------------------


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
        st.warning(
            warning
        )

st.write(
    "#### Compétences extraites"
)

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


# ---------------------------------------------------------------------------
# Étape 2 — Choix du métier
# ---------------------------------------------------------------------------


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
    for suggestion
    in analysis.role_suggestions
}

selected_label = st.selectbox(
    "Métier proposé",
    options=list(
        role_by_label.keys()
    ),
    key="selected_role_label",
)

selected_role = role_by_label[
    selected_label
]

column_score, column_providers = (
    st.columns(
        [
            1,
            2,
        ]
    )
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
            selected_role.missing_core_skills
        )
        or "Aucune",
    )


# ---------------------------------------------------------------------------
# Étape 3 — Personnalisation du profil
# ---------------------------------------------------------------------------


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
    key="career_profile_name",
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
    key="career_keywords",
)

locations_text = st.text_input(
    "Localisations",
    value=comma_separated(
        preview_profile.locations
    ),
    help=(
        "Exemples : Paris, Lyon, Remote"
    ),
    key="career_locations",
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
    key="career_salary_min",
)

remote = st.checkbox(
    "Télétravail accepté",
    value=bool(
        preview_profile.remote
    ),
    key="career_remote",
)


# ---------------------------------------------------------------------------
# Étape 4 — Création ou enrichissement
# ---------------------------------------------------------------------------


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
    key="career_save_action",
)

selected_existing_profile = None

if action == "Enrichir un profil existant":
    if existing_profiles:
        selected_existing_profile = (
            st.selectbox(
                "Profil à enrichir",
                options=existing_profiles,
                key="career_existing_profile",
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
    key="career_save_button",
)

if save_clicked:
    try:
        final_generated = (
            service.build_profile(
                analysis=analysis,
                role_id=selected_role.role_id,
                keywords=keywords_text,
                locations=locations_text,
                salary_min=int(
                    salary_min
                ),
                remote=remote,
                profile_name=profile_name,
            )
        )

        career_metadata = {
            "role_id": selected_role.role_id,
            "role_label": selected_role.label,
            "role_score": selected_role.score,
            "seniority": analysis.seniority,
            "recommended_providers": list(
                selected_role.preferred_providers
            ),
        }

        cv_path = st.session_state.get(
            "cv_temporary_path"
        )

        if (
            action
            == "Créer un nouveau profil"
        ):
            save_result = (
                service.create_profile(
                    profile=(
                        final_generated.profile
                    ),
                    cv_source_path=cv_path,
                    metadata=career_metadata,
                )
            )

        else:
            save_result = (
                service.enrich_profile(
                    profile_id=(
                        selected_existing_profile
                    ),
                    profile=(
                        final_generated.profile
                    ),
                    cv_source_path=cv_path,
                    metadata=career_metadata,
                )
            )

        st.session_state[
            "career_generated_profile"
        ] = final_generated.profile

        st.session_state[
            "career_selected_role"
        ] = selected_role

        st.session_state[
            "career_saved_profile_id"
        ] = save_result.profile_id

        reset_search_state()

        st.cache_resource.clear()

        st.success(
            (
                "Profil créé"
                if save_result.created
                else "Profil enrichi"
            )
            + f" : {save_result.profile_name}"
        )

        st.write(
            "**Identifiant :**",
            save_result.profile_id,
        )

        st.write(
            "**Configuration :**",
            str(
                save_result.config_path
            ),
        )

        if (
            save_result.cv_path
            is not None
        ):
            st.write(
                "**CV enregistré :**",
                str(
                    save_result.cv_path
                ),
            )

    except Exception as error:
        st.error(
            "L'enregistrement du profil a échoué."
        )

        st.exception(error)


# ---------------------------------------------------------------------------
# Étape 5 — Recherche
# ---------------------------------------------------------------------------


st.divider()
st.subheader("5. Rechercher des offres")

search_profile = st.session_state.get(
    "career_generated_profile"
)

search_role = st.session_state.get(
    "career_selected_role"
)

saved_profile_id = st.session_state.get(
    "career_saved_profile_id"
)

if search_profile is None:
    st.info(
        "Enregistrez d'abord le profil pour "
        "pouvoir lancer la recherche."
    )

else:
    st.success(
        "Profil prêt pour la recherche : "
        f"{search_profile.name}"
    )

    if saved_profile_id:
        st.caption(
            "Profil enregistré sous : "
            f"{saved_profile_id}"
        )

    if search_role is not None:
        st.write(
            "**Métier sélectionné :**",
            search_role.label,
        )

        st.write(
            "**Sources recommandées :**",
            ", ".join(
                search_role.preferred_providers
            ),
        )

    st.caption(
        "RemoteOK est actuellement le seul provider "
        "réellement opérationnel. Les autres sources "
        "sont affichées à titre de recommandation."
    )

    search_clicked = st.button(
        "🚀 Rechercher des offres",
        type="primary",
        use_container_width=True,
        key="career_search_button",
    )

    if search_clicked:
        try:
            with st.spinner(
                "Interrogation de RemoteOK et "
                "analyse des offres..."
            ):
                search_result = (
                    search_workflow.search(
                        profile=search_profile,
                        selected_role=search_role,
                    )
                )

            st.session_state[
                "career_search_result"
            ] = search_result

            st.session_state[
                "career_search_completed"
            ] = True

            st.rerun()

        except Exception as error:
            st.session_state[
                "career_search_result"
            ] = None

            st.session_state[
                "career_search_completed"
            ] = False

            st.error(
                "La recherche a échoué."
            )

            st.exception(error)


# ---------------------------------------------------------------------------
# Étape 6 — Résultats
# ---------------------------------------------------------------------------


search_result = st.session_state.get(
    "career_search_result"
)

search_completed = st.session_state.get(
    "career_search_completed",
    False,
)

if search_completed:
    st.divider()
    st.subheader(
        "6. Résultats de la recherche"
    )

    if search_result is None:
        st.error(
            "La recherche n'a produit aucun "
            "résultat exploitable."
        )

    else:
        display_provider_statuses(
            search_result
        )



        # ------------------------------------------------------------------
        # AJOUT V3.12
        # ------------------------------------------------------------------

        provider_selection = getattr(
            search_result,
            "provider_selection",
            None,
        )

        if provider_selection is not None:
            st.write(
                "#### Sélection intelligente"
            )

            for selection_item in (
                provider_selection.items
            ):
                if selection_item.selected:
                    if selection_item.fallback:
                        icon = "🔁"
                        decision = "sélectionné en repli"
                    else:
                        icon = "🎯"
                        decision = "sélectionné"

                elif selection_item.recommended:
                    icon = "💡"
                    decision = "recommandé mais indisponible"

                else:
                    icon = "○"
                    decision = "non sélectionné"

                st.write(
                    f"{icon} **{selection_item.label}** "
                    f"— {decision} "
                    f"(indice {selection_item.score})"
                )

                if selection_item.reasons:
                    with st.expander(
                        f"Pourquoi {selection_item.label} ?",
                        expanded=False,
                    ):
                        for reason in selection_item.reasons:
                            st.write(f"- {reason}")

        # ------------------------------------------------------------------
        # FIN AJOUT V3.12
        # ------------------------------------------------------------------

        if search_result.provider_errors:
            for provider_error in (
                search_result.provider_errors
            ):
                st.warning(provider_error)


        metric_collected, metric_relevant = (
            st.columns(2)
        )

        metric_collected.metric(
            "Offres analysées",
            search_result.total_collected,
        )

        metric_relevant.metric(
            "Offres pertinentes",
            search_result.total_relevant,
        )

        st.write(
            "#### Résultats"
        )

        if not search_result.jobs:
            st.info(
                "Aucune offre suffisamment pertinente "
                "n'a été trouvée avec RemoteOK."
            )

            st.caption(
                "Ce résultat est cohérent lorsque le métier "
                "sélectionné est DSI, CIO, Directeur de projet "
                "ou Directeur de programme. Les sources "
                "prioritaires correspondantes seront intégrées "
                "dans la V3.12."
            )

        else:
            for job in (
                search_result.jobs
            ):
                display_job(
                    job
                )

        if st.button(
            "🔄 Relancer la recherche",
            use_container_width=True,
            key="career_search_again_button",
        ):
            reset_search_state()
            st.rerun()