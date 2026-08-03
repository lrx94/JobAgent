from __future__ import annotations
from src.ui.dashboard import (
    display_dashboard,
)
from src.ui.job_card import (
    display_job,
)
from src.workspace.search import (
    WorkspaceSearchCache,
    WorkspaceSearchError,
    WorkspaceSearchService,
)
from pathlib import Path

import streamlit as st

from src.auth.adapters.streamlit_bootstrap import (
    require_streamlit_user,
)
from src.cvs.exceptions import (
    CVAnalysisError,
    CVError,
    CVStillInUseError,
)
from src.cvs.service import CVService
from src.profile import Profile
from src.workspace import build_workspace
from src.workspace.ui import (
    WorkspaceProfileItem,
    build_workspace_snapshot,
    format_file_size,
)
from src.workspace.ui.actions import (
    WorkspaceCVActions,
)
import hashlib


STORAGE_ROOT = (
    Path("data")
    / "users"
)

SELECTED_PROFILE_KEY = (
    "career_workspace_selected_profile"
)

ONBOARDING_FILE_DIGEST_KEY = (
    "workspace_onboarding_file_digest"
)

ONBOARDING_PREVIEW_KEY = (
    "workspace_onboarding_preview"
)

ONBOARDING_PROFILE_NAME_KEY = (
    "workspace_onboarding_profile_name"
)

ONBOARDING_CV_TITLE_KEY = (
    "workspace_onboarding_cv_title"
)

ONBOARDING_KEYWORDS_KEY = (
    "workspace_onboarding_keywords"
)

st.set_page_config(
    page_title="Career Workspace",
    page_icon="🧭",
    layout="wide",
)

user_context = require_streamlit_user()

workspace = build_workspace(
    user_context=user_context,
    storage_root=STORAGE_ROOT,
)

search_service = WorkspaceSearchService(
    profile_service=(
        workspace.profile_service
    )
)

cv_actions = WorkspaceCVActions(
    cv_service=workspace.cv_service,
    association_service=(
        workspace.association_service
    ),
    association_repository=(
        workspace.association_repository
    ),
    profile_service=(
        workspace.profile_service
    ),
)

def rerun() -> None:
    st.rerun()


def normalize_csv_values(
    value: str,
) -> list[str]:
    """
    Transforme une saisie séparée par des virgules
    en liste dédupliquée.
    """

    result: list[str] = []
    seen: set[str] = set()

    for item in str(
        value or ""
    ).split(","):
        cleaned = item.strip()

        if not cleaned:
            continue

        identity = cleaned.casefold()

        if identity in seen:
            continue

        seen.add(identity)
        result.append(cleaned)

    return result


def ensure_selected_profile(
    profile_ids: list[str],
) -> str | None:
    current = st.session_state.get(
        SELECTED_PROFILE_KEY
    )

    if current in profile_ids:
        return current

    selected = (
        profile_ids[0]
        if profile_ids
        else None
    )

    st.session_state[
        SELECTED_PROFILE_KEY
    ] = selected

    return selected


def render_quick_profile_creation() -> None:
    with st.expander(
        "➕ Créer un nouveau profil",
        expanded=False,
    ):
        with st.form(
            "career_workspace_profile_form",
            clear_on_submit=True,
        ):
            name = st.text_input(
                "Nom du profil",
                placeholder=(
                    "Ex. DSI Groupe, Data Engineer"
                ),
            )

            keywords_text = st.text_area(
                "Compétences et mots-clés",
                placeholder=(
                    "Python, Azure, SQL, gouvernance SI"
                ),
            )

            locations_text = st.text_input(
                "Localisations",
                placeholder="Paris, Remote",
            )

            salary_min = st.number_input(
                "Salaire minimum annuel",
                min_value=0,
                step=1000,
                value=0,
            )

            remote = st.checkbox(
                "Télétravail accepté",
                value=True,
            )

            submitted = st.form_submit_button(
                "Créer le profil",
                type="primary",
                use_container_width=True,
            )

        if not submitted:
            return

        if not name.strip():
            st.error(
                "Le nom du profil est obligatoire."
            )
            return

        try:
            result = (
                workspace
                .profile_service
                .create_profile(
                    profile=Profile(
                        name=name.strip(),
                        keywords=normalize_csv_values(
                            keywords_text
                        ),
                        locations=normalize_csv_values(
                            locations_text
                        ),
                        salary_min=int(salary_min),
                        remote=remote,
                    )
                )
            )
        except Exception as error:
            st.error(
                "Impossible de créer le profil : "
                f"{error}"
            )
            return

        st.session_state[
            SELECTED_PROFILE_KEY
        ] = result.profile_id

        st.success(
            f"Profil « {name.strip()} » créé."
        )

        rerun()

def render_profile_from_cv_creation() -> None:
    with st.expander(
        "📄 Créer un profil depuis mon CV",
        expanded=False,
    ):
        st.caption(
            "Le CV est analysé avec les dictionnaires "
            "de compétences et synonymes déjà utilisés "
            "par JobAgent."
        )

        uploaded_file = st.file_uploader(
            "CV au format PDF",
            type=["pdf"],
            key="workspace_onboarding_cv",
        )

        if uploaded_file is None:
            st.info(
                "Ajoute un PDF pour préremplir "
                "automatiquement le profil."
            )
            return

        content = uploaded_file.getvalue()

        file_digest = hashlib.sha256(
            content
        ).hexdigest()

        previous_digest = (
            st.session_state.get(
                ONBOARDING_FILE_DIGEST_KEY
            )
        )

        if file_digest != previous_digest:
            try:
                with st.spinner(
                    "Analyse du CV et préparation "
                    "du profil..."
                ):
                    preview = (
                        workspace
                        .onboarding_service
                        .preview_from_bytes(
                            content=content,
                            original_filename=(
                                uploaded_file.name
                            ),
                        )
                    )

            except Exception as error:
                st.session_state[
                    ONBOARDING_PREVIEW_KEY
                ] = None

                st.session_state[
                    ONBOARDING_PROFILE_NAME_KEY
                ] = Path(
                    uploaded_file.name
                ).stem

                st.session_state[
                    ONBOARDING_CV_TITLE_KEY
                ] = Path(
                    uploaded_file.name
                ).stem

                st.session_state[
                    ONBOARDING_KEYWORDS_KEY
                ] = ""

                st.warning(
                    "Le CV n'a pas pu être utilisé "
                    "pour préremplir le formulaire : "
                    f"{error}"
                )

            else:
                st.session_state[
                    ONBOARDING_PREVIEW_KEY
                ] = preview

                st.session_state[
                    ONBOARDING_PROFILE_NAME_KEY
                ] = (
                    preview
                    .suggested_profile_name
                )

                st.session_state[
                    ONBOARDING_CV_TITLE_KEY
                ] = (
                    preview
                    .suggested_cv_title
                )

                st.session_state[
                    ONBOARDING_KEYWORDS_KEY
                ] = ", ".join(
                    preview.suggested_keywords
                )

            st.session_state[
                ONBOARDING_FILE_DIGEST_KEY
            ] = file_digest

        preview = st.session_state.get(
            ONBOARDING_PREVIEW_KEY
        )

        if preview is not None:
            st.success(
                "Le CV a été analysé. "
                "Les champs ont été préremplis."
            )

            summary_columns = st.columns(2)

            with summary_columns[0]:
                st.write(
                    "**Métier détecté**"
                )

                st.write(
                    preview.detected_role
                    or "Non déterminé"
                )

                if (
                    preview.detected_role_score
                    is not None
                ):
                    st.caption(
                        "Confiance : "
                        f"{preview.detected_role_score:.0f} %"
                    )

            with summary_columns[1]:
                st.write(
                    "**Compétences reconnues**"
                )

                st.write(
                    len(
                        preview.detected_skills
                    )
                )

            if preview.detected_skills:
                with st.expander(
                    "Voir les compétences détectées",
                    expanded=False,
                ):
                    st.write(
                        ", ".join(
                            preview.detected_skills
                        )
                    )

            for warning in (
                preview.warnings
            ):
                st.warning(warning)

        with st.form(
            "career_workspace_onboarding_form",
            clear_on_submit=False,
        ):
            profile_name = st.text_input(
                "Nom du profil de recherche",
                key=(
                    ONBOARDING_PROFILE_NAME_KEY
                ),
                placeholder=(
                    "Ex. DSI / CIO, Data Engineer"
                ),
            )

            cv_title = st.text_input(
                "Titre du CV",
                key=(
                    ONBOARDING_CV_TITLE_KEY
                ),
                placeholder="Ex. CV DSI 2026",
            )

            keywords_text = st.text_area(
                "Mots-clés initiaux",
                key=(
                    ONBOARDING_KEYWORDS_KEY
                ),
                placeholder=(
                    "Transformation SI, COBIT, "
                    "gouvernance, cloud"
                ),
            )

            locations_text = st.text_input(
                "Localisations recherchées",
                placeholder="Paris, Remote",
                key=(
                    "workspace_onboarding_locations"
                ),
            )

            salary_min = st.number_input(
                "Salaire minimum annuel",
                min_value=0,
                step=1000,
                value=0,
                key="onboarding_salary_min",
            )

            remote = st.checkbox(
                "Télétravail accepté",
                value=True,
                key="onboarding_remote",
            )

            submitted = st.form_submit_button(
                "Créer le profil depuis ce CV",
                type="primary",
                use_container_width=True,
            )

        if not submitted:
            return

        if not profile_name.strip():
            st.error(
                "Le nom du profil est obligatoire."
            )
            return

        profile = Profile(
            name=profile_name.strip(),
            keywords=normalize_csv_values(
                keywords_text
            ),
            locations=normalize_csv_values(
                locations_text
            ),
            salary_min=int(salary_min),
            remote=remote,
        )

        try:
            result = (
                workspace
                .onboarding_service
                .create_from_bytes(
                    content=content,
                    original_filename=(
                        uploaded_file.name
                    ),
                    profile=profile,
                    cv_title=(
                        cv_title.strip()
                        or Path(
                            uploaded_file.name
                        ).stem
                    ),
                    duplicate_policy=(
                        CVService.DUPLICATE_REUSE
                    ),
                    analyze=True,
                )
            )

        except Exception as error:
            st.error(
                "Impossible de créer le profil "
                f"depuis le CV : {error}"
            )
            return

        st.session_state[
            SELECTED_PROFILE_KEY
        ] = result.profile_id

        for state_key in (
            ONBOARDING_FILE_DIGEST_KEY,
            ONBOARDING_PREVIEW_KEY,
            ONBOARDING_PROFILE_NAME_KEY,
            ONBOARDING_CV_TITLE_KEY,
            ONBOARDING_KEYWORDS_KEY,
        ):
            st.session_state.pop(
                state_key,
                None,
            )

        st.success(
            "Le profil a été créé avec les données "
            "issues de l'analyse du CV."
        )

        rerun()


def render_navigation(
    snapshot,
    selected_profile_id: str | None,
) -> None:
    st.subheader("🌳 Mes Profils")

    render_quick_profile_creation()
    render_profile_from_cv_creation()

    st.divider()

    if not snapshot.profiles:
        st.info(
            "Aucun profil utilisateur enregistré."
        )
        return

    profiles_by_id = {
        profile.profile_id: profile
        for profile in snapshot.profiles
    }

    profile_ids = list(
        profiles_by_id
    )

    if (
        st.session_state.get(
            SELECTED_PROFILE_KEY
        )
        not in profile_ids
    ):
        st.session_state[
            SELECTED_PROFILE_KEY
        ] = profile_ids[0]

    selected_id = st.radio(
        "Profils existants",
        options=profile_ids,
        key=SELECTED_PROFILE_KEY,
        format_func=lambda profile_id: (
            profiles_by_id[
                profile_id
            ].display_name
        ),
        label_visibility="visible",
    )

    selected_profile = profiles_by_id[
        selected_id
    ]

    if not selected_profile.cvs:
        st.caption(
            "Aucun CV associé à ce profil."
        )
    else:
        st.write("**CV associés**")

        for cv in selected_profile.cvs:
            marker = (
                "⭐"
                if cv.is_primary
                else "📄"
            )

            st.caption(
                f"{marker} {cv.title}"
            )

    if snapshot.unassigned_cvs:
        st.divider()
        st.write(
            "**CV non associés**"
        )

        for cv in snapshot.unassigned_cvs:
            st.caption(
                f"📄 {cv.title}"
            )



def render_cv_library(
    snapshot,
    selected_profile: WorkspaceProfileItem | None,
) -> None:
    documents = list(
        workspace.cv_service.list_cvs()
    )

    if selected_profile is None:
        st.info(
            "Sélectionne un profil."
        )
        return

    associated_cv_ids = {
        cv.cv_id
        for cv in selected_profile.cvs
    }

    available_documents = [
        document
        for document in documents
        if document.cv_id
        not in associated_cv_ids
    ]



    if not documents:
        st.info(
            "La bibliothèque ne contient encore aucun CV."
        )
        return

    profile_labels = {
        profile.profile_id: profile.display_name
        for profile in snapshot.profiles
    }

    st.caption(
        f"{len(documents)} CV dans la bibliothèque."
    )
    st.subheader(
        "➕ Ajouter un CV existant"
    )

    if available_documents:

        cv_by_id = {
            document.cv_id: document
            for document
            in available_documents
        }

        selected_cv_id = st.selectbox(
            "CV de la bibliothèque",
            options=list(cv_by_id),
            format_func=lambda cv_id:
                cv_by_id[cv_id].title,
            key=(
                "workspace_add_existing_cv_"
                f"{selected_profile.profile_id}"
            ),
        )

        make_primary = st.checkbox(
            "Définir comme principal",
            value=(
                selected_profile.primary_cv
                is None
            ),
        )

        if st.button(
            "Associer au profil",
            type="primary",
            use_container_width=True,
            key=(
                "workspace_attach_existing_"
                f"{selected_profile.profile_id}"
            ),
        ):

            cv_actions.attach_cv(
                profile_id=(
                    selected_profile.profile_id
                ),
                cv_id=selected_cv_id,
                is_primary=make_primary,
            )

            rerun()

    else:

        st.success(
            "Tous les CV de la bibliothèque "
            "sont déjà associés à ce profil."
        )

    st.divider()
    for document in documents:
        associations = (
            cv_actions.associations_for_cv(
                document.cv_id
            )
        )

        associated_profile_ids = [
            association.profile_id
            for association in associations
        ]

        associated_labels = [
            profile_labels.get(
                profile_id,
                profile_id,
            )
            for profile_id
            in associated_profile_ids
        ]

        with st.expander(
            f"📄 {document.title}",
            expanded=False,
        ):
            st.caption(
                f"{document.original_filename} • "
                f"{format_file_size(document.size_bytes)}"
            )

            if associated_labels:
                st.write(
                    "**Profils associés :** "
                    + ", ".join(
                        sorted(associated_labels)
                    )
                )
            else:
                st.warning(
                    "Ce CV n'est associé à aucun profil."
                )

            action_tabs = st.tabs(
                [
                    "Visualiser",
                    "Associer",
                    "Renommer",
                    "Supprimer",
                ]
            )

            with action_tabs[0]:
                try:
                    pdf_content = (
                        workspace.cv_service.read_cv(
                            document.cv_id
                        )
                    )

                    st.pdf(
                        pdf_content,
                        height=700,
                        key=(
                            "workspace_library_pdf_"
                            f"{document.cv_id}"
                        ),
                    )

                    st.download_button(
                        "⬇️ Télécharger",
                        data=pdf_content,
                        file_name=(
                            document.original_filename
                        ),
                        mime="application/pdf",
                        key=(
                            "workspace_library_download_"
                            f"{document.cv_id}"
                        ),
                        use_container_width=True,
                    )

                except Exception as error:
                    st.error(
                        "Impossible d'afficher le CV : "
                        f"{error}"
                    )

            with action_tabs[1]:
                available_profile_ids = (
                    cv_actions.available_profile_ids(
                        associated_profile_ids
                    )
                )

                if available_profile_ids:
                    target_profile_id = st.selectbox(
                        "Associer à un profil",
                        options=available_profile_ids,
                        format_func=lambda profile_id: (
                            profile_labels.get(
                                profile_id,
                                profile_id,
                            )
                        ),
                        key=(
                            "workspace_library_attach_profile_"
                            f"{document.cv_id}"
                        ),
                    )

                    make_primary = st.checkbox(
                        "Définir comme CV principal",
                        value=False,
                        key=(
                            "workspace_library_attach_primary_"
                            f"{document.cv_id}"
                        ),
                    )

                    if st.button(
                        "Associer ce CV",
                        key=(
                            "workspace_library_attach_"
                            f"{document.cv_id}"
                        ),
                        use_container_width=True,
                    ):
                        try:
                            cv_actions.attach_cv(
                                profile_id=target_profile_id,
                                cv_id=document.cv_id,
                                is_primary=make_primary,
                            )
                        except CVError as error:
                            st.error(str(error))
                        else:
                            st.success(
                                "CV associé au profil."
                            )
                            rerun()
                else:
                    st.info(
                        "Ce CV est déjà associé à tous "
                        "les profils disponibles."
                    )

                if associations:
                    st.divider()
                    st.write(
                        "**Associations existantes**"
                    )

                    for association in associations:
                        columns = st.columns(
                            [3, 1, 1]
                        )

                        label = profile_labels.get(
                            association.profile_id,
                            association.profile_id,
                        )

                        if association.is_primary:
                            label += " ⭐"

                        columns[0].write(label)

                        if columns[1].button(
                            "Principal",
                            disabled=(
                                association.is_primary
                            ),
                            key=(
                                "workspace_library_primary_"
                                f"{association.profile_id}_"
                                f"{association.cv_id}"
                            ),
                        ):
                            try:
                                cv_actions.set_primary_cv(
                                    profile_id=(
                                        association.profile_id
                                    ),
                                    cv_id=association.cv_id,
                                )
                            except CVError as error:
                                st.error(str(error))
                            else:
                                rerun()

                        if columns[2].button(
                            "Détacher",
                            key=(
                                "workspace_library_detach_"
                                f"{association.profile_id}_"
                                f"{association.cv_id}"
                            ),
                        ):
                            try:
                                cv_actions.detach_cv(
                                    profile_id=(
                                        association.profile_id
                                    ),
                                    cv_id=association.cv_id,
                                )
                            except CVError as error:
                                st.error(str(error))
                            else:
                                rerun()

            with action_tabs[2]:
                with st.form(
                    "workspace_library_rename_"
                    f"{document.cv_id}"
                ):
                    new_title = st.text_input(
                        "Nouveau titre",
                        value=document.title,
                        key=(
                            "workspace_library_title_"
                            f"{document.cv_id}"
                        ),
                    )

                    rename_submitted = (
                        st.form_submit_button(
                            "Renommer",
                            use_container_width=True,
                        )
                    )

                if rename_submitted:
                    try:
                        cv_actions.rename_cv(
                            document.cv_id,
                            new_title,
                        )
                    except CVError as error:
                        st.error(str(error))
                    else:
                        st.success(
                            "CV renommé."
                        )
                        rerun()

            with action_tabs[3]:
                if associated_profile_ids:
                    st.warning(
                        "Ce CV est encore associé à "
                        "un ou plusieurs profils."
                    )

                force_delete = st.checkbox(
                    "Détacher de tous les profils",
                    value=False,
                    key=(
                        "workspace_library_force_delete_"
                        f"{document.cv_id}"
                    ),
                )

                confirm_delete = st.checkbox(
                    "Je confirme la suppression définitive",
                    value=False,
                    key=(
                        "workspace_library_confirm_delete_"
                        f"{document.cv_id}"
                    ),
                )

                if st.button(
                    "🗑 Supprimer le CV",
                    type="secondary",
                    disabled=not confirm_delete,
                    key=(
                        "workspace_library_delete_"
                        f"{document.cv_id}"
                    ),
                    use_container_width=True,
                ):
                    try:
                        cv_actions.delete_cv(
                            document.cv_id,
                            force=force_delete,
                        )
                    except CVStillInUseError as error:
                        st.error(str(error))
                    except CVError as error:
                        st.error(str(error))
                    else:
                        st.success(
                            "CV supprimé."
                        )
                        rerun()


def render_profile_dashboard(
    profile: WorkspaceProfileItem | None,
) -> None:
    st.subheader("👤 Profil")

    if profile is None:
        st.info(
            "Crée ou sélectionne un profil "
            "pour afficher son tableau de bord."
        )
        return

    st.title(
        profile.display_name
    )

    metric1, metric2, metric3 = (
        st.columns(3)
    )

    metric1.metric(
        "CV associés",
        profile.cv_count,
    )

    metric2.metric(
        "Mots-clés",
        len(
            profile.config.get(
                "keywords",
                [],
            )
            or []
        ),
    )

    metric3.metric(
        "CV principal",
        (
            "Oui"
            if profile.primary_cv
            else "Non"
        ),
    )

    tabs = st.tabs(
        [
            "Vue d’ensemble",
            "Compétences",
            "CV associés",
            "Bibliothèque",
            "Offres",
        ]
    )

    with tabs[0]:
        keywords = (
            profile.config.get(
                "keywords",
                [],
            )
            or []
        )

        locations = (
            profile.config.get(
                "locations",
                [],
            )
            or []
        )

        primary_cv = profile.primary_cv

        if primary_cv is None:
            st.warning(
                "Aucun CV principal associé."
            )
        else:
            st.write("### ⭐ CV principal")

            st.caption(
                f"{primary_cv.title} • "
                f"{primary_cv.original_filename} • "
                f"{format_file_size(primary_cv.size_bytes)}"
            )

            try:
                pdf_content = (
                    workspace
                    .cv_service
                    .read_cv(
                        primary_cv.cv_id
                    )
                )

                st.pdf(
                    pdf_content,
                    height=760,
                    key=(
                        "workspace_overview_primary_pdf_"
                        f"{profile.profile_id}_"
                        f"{primary_cv.cv_id}"
                    ),
                )

                st.download_button(
                    "⬇️ Télécharger le CV principal",
                    data=pdf_content,
                    file_name=(
                        primary_cv.original_filename
                    ),
                    mime="application/pdf",
                    key=(
                        "workspace_overview_download_"
                        f"{profile.profile_id}_"
                        f"{primary_cv.cv_id}"
                    ),
                    use_container_width=True,
                )

            except Exception as error:
                st.error(
                    "Impossible d’afficher le CV principal : "
                    f"{error}"
                )

        st.divider()

        overview_col1, overview_col2 = (
            st.columns(2)
        )

        with overview_col1:
            st.write("**Localisations**")

            st.write(
                ", ".join(locations)
                if locations
                else "Non renseignées"
            )

            st.write("**Télétravail**")

            st.write(
                "Accepté"
                if profile.config.get(
                    "remote",
                    False,
                )
                else "Non renseigné"
            )

        with overview_col2:
            st.write("**Salaire minimum**")

            salary = int(
                profile.config.get(
                    "salary_min",
                    0,
                )
                or 0
            )

            st.write(
                f"{salary:,} €".replace(
                    ",",
                    " ",
                )
                if salary
                else "Non renseigné"
            )

            st.write("**Nombre de CV associés**")

            st.write(
                str(profile.cv_count)
            )

        if keywords:
            st.divider()

            st.write(
                "**Mots-clés de recherche**"
            )

            st.write(
                ", ".join(keywords)
            )

    with tabs[1]:
        primary_cv = profile.primary_cv

        if primary_cv is None:
            st.info(
                "Associe un CV principal pour "
                "analyser ses compétences."
            )
        else:
            try:
                analysis = (
                    workspace
                    .cv_service
                    .analyze(
                        primary_cv.cv_id
                    )
                )
            except CVAnalysisError as error:
                st.warning(str(error))
            else:
                col1, col2 = st.columns(2)

                col1.metric(
                    "Caractères extraits",
                    analysis.character_count,
                )

                col2.metric(
                    "Compétences détectées",
                    len(analysis.skills),
                )

                if analysis.skills:
                    st.write(
                        ", ".join(
                            analysis.skills
                        )
                    )
                else:
                    st.info(
                        "Aucune compétence détectée."
                    )

    with tabs[2]:
        if not profile.cvs:
            st.info(
                "Aucun CV associé à ce profil."
            )
        else:
            for cv in profile.cvs:
                with st.container(
                    border=True
                ):
                    marker = (
                        "⭐ CV principal"
                        if cv.is_primary
                        else "CV secondaire"
                    )

                    st.write(
                        f"**{cv.title}**"
                    )

                    st.caption(
                        f"{marker} • "
                        f"{cv.original_filename} • "
                        f"{format_file_size(cv.size_bytes)}"
                    )
                    with st.expander(
                        "👁️ Visualiser le CV",
                        expanded=False,
                    ):
                        try:
                            pdf_content = (
                                workspace
                                .cv_service
                                .read_cv(
                                    cv.cv_id
                                )
                            )

                            st.pdf(
                                pdf_content,
                                height=700,
                                key=(
                                    "workspace_pdf_preview_"
                                    f"{profile.profile_id}_"
                                    f"{cv.cv_id}"
                                ),
                            )
                            st.download_button(
                                "⬇️ Télécharger le CV",
                                data=pdf_content,
                                file_name=cv.original_filename,
                                mime="application/pdf",
                                key=(
                                    "workspace_download_cv_"
                                    f"{profile.profile_id}_"
                                    f"{cv.cv_id}"
                                ),
                                use_container_width=True,
                            )
                        except Exception as error:
                            st.error(
                                "Impossible d’afficher le CV : "
                                f"{error}"
                            )
                    if (
                        not cv.is_primary
                        and st.button(
                            "Définir comme principal",
                            key=(
                                "primary_cv_"
                                f"{profile.profile_id}_"
                                f"{cv.cv_id}"
                            ),
                        )
                    ):
                        try:
                            (
                                workspace
                                .association_service
                                .set_primary_cv(
                                    profile_id=(
                                        profile.profile_id
                                    ),
                                    cv_id=cv.cv_id,
                                )
                            )
                        except CVError as error:
                            st.error(str(error))
                        else:
                            rerun()

                    if st.button(
                        "Détacher",
                        key=(
                            "detach_cv_"
                            f"{profile.profile_id}_"
                            f"{cv.cv_id}"
                        ),
                    ):
                        try:
                            (
                                workspace
                                .association_service
                                .detach_cv(
                                    profile_id=(
                                        profile.profile_id
                                    ),
                                    cv_id=cv.cv_id,
                                )
                            )
                        except CVError as error:
                            st.error(str(error))
                        else:
                            rerun()

    with tabs[3]:
        render_cv_library(
            snapshot=build_workspace_snapshot(
                workspace
            ),
            selected_profile=profile,
        )

    with tabs[4]:
        st.info(
            "Les résultats de recherche sont affichés "
            "dans la colonne « Recherche et offres »."
        )

def render_provider_information(
    search_result,
) -> None:
    provider_selection = getattr(
        search_result,
        "provider_selection",
        None,
    )

    if provider_selection is not None:
        with st.expander(
            "Sources interrogées",
            expanded=False,
        ):
            for item in provider_selection.items:
                if item.selected:
                    icon = (
                        "🔁"
                        if item.fallback
                        else "🎯"
                    )

                    decision = (
                        "sélectionné en repli"
                        if item.fallback
                        else "sélectionné"
                    )

                elif item.recommended:
                    icon = "💡"
                    decision = (
                        "recommandé mais indisponible"
                    )

                else:
                    icon = "○"
                    decision = "non sélectionné"

                st.write(
                    f"{icon} **{item.label}** "
                    f"— {decision}"
                )

                for reason in (
                    item.reasons or []
                ):
                    st.caption(
                        f"• {reason}"
                    )

    for provider_error in (
        getattr(
            search_result,
            "provider_errors",
            [],
        )
        or []
    ):
        st.warning(
            provider_error
        )
       
def render_search_panel(
    profile: WorkspaceProfileItem | None,
) -> None:
    st.subheader("💼 Recherche et offres")

    if profile is None:
        st.info(
            "Sélectionne un profil pour "
            "lancer une recherche."
        )
        return

    profile_id = profile.profile_id

    st.write(
        "Profil actif : "
        f"**{profile.display_name}**"
    )

    keywords = (
        profile.config.get(
            "keywords",
            [],
        )
        or []
    )

    if keywords:
        st.caption(
            "Mots-clés : "
            + ", ".join(
                str(value)
                for value in keywords
            )
        )

    search_result = (
        WorkspaceSearchCache.get(
            st.session_state,
            profile_id,
        )
    )

    if search_result is None:
        try:
            with st.spinner(
                "Recherche des offres..."
            ):
                search_result = (
                    search_service.search(
                        profile_id
                    )
                )

            WorkspaceSearchCache.set(
                st.session_state,
                profile_id,
                search_result,
            )

            rerun()

        except WorkspaceSearchError as error:
            st.error(str(error))
            return

        except Exception as error:
            st.error(
                "La recherche a échoué : "
                f"{error}"
            )
            return

    if st.button(
        "🔄 Actualiser",
        key=(
            "workspace_refresh_search_"
            f"{profile_id}"
        ),
        use_container_width=True,
    ):
        WorkspaceSearchCache.clear(
            st.session_state,
            profile_id,
        )

        try:
            with st.spinner(
                "Actualisation des offres..."
            ):
                search_result = (
                    search_service.search(
                        profile_id
                    )
                )

            WorkspaceSearchCache.set(
                st.session_state,
                profile_id,
                search_result,
            )

            rerun()

        except WorkspaceSearchError as error:
            st.error(str(error))
            return

        except Exception as error:
            st.error(
                "La recherche a échoué : "
                f"{error}"
            )
            return

    search_result = (
        WorkspaceSearchCache.get(
            st.session_state,
            profile_id,
        )
    )

    if search_result is None:
        st.info(
            "Aucune recherche enregistrée."
        )
        return

    render_provider_information(
        search_result
    )

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

    jobs = list(
        search_result.jobs
    )

    if not jobs:
        st.info(
            "Aucune offre suffisamment pertinente "
            "n'a été trouvée."
        )
        return

    display_dashboard(
        jobs
    )

    st.write("### Résultats")

    for job in jobs:
        display_job(
            job
        )

snapshot = build_workspace_snapshot(
    workspace
)

profile_ids = [
    profile.profile_id
    for profile in snapshot.profiles
]

selected_profile_id = (
    ensure_selected_profile(
        profile_ids
    )
)

selected_profile = (
    snapshot.get_profile(
        selected_profile_id
    )
    if selected_profile_id
    else None
)

st.title("🧭 Career Workspace")

display_name = str(
    getattr(
        user_context,
        "display_name",
        "",
    )
    or ""
).strip()

st.caption(
    "Espace carrière privé"
    + (
        f" de {display_name}"
        if display_name
        else ""
    )
)

navigation_column, dashboard_column, cv_column = (
    st.columns(
        [1.15, 2.2, 1.55],
        gap="large",
    )
)

with navigation_column:
    render_navigation(
        snapshot=snapshot,
        selected_profile_id=(
            selected_profile_id
        ),
    )

with dashboard_column:
    render_profile_dashboard(
        selected_profile
    )

with cv_column:
    render_search_panel(
        selected_profile
    )