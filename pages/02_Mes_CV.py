from __future__ import annotations

from pathlib import Path

import streamlit as st

from src.auth.adapters.streamlit_bootstrap import (
    require_streamlit_user,
)
from src.career.user_cv_profile_service import (
    UserCVProfileService,
)
from src.cvs.exceptions import (
    CVAnalysisError,
    CVError,
    CVStillInUseError,
    DuplicateCVError,
)
from src.cvs.profile_cv_repository import (
    ProfileCVRepository,
)
from src.cvs.profile_cv_service import (
    ProfileCVService,
)
from src.cvs.repository import (
    CVRepository,
)
from src.cvs.service import (
    CVService,
)
from src.cvs.ui_helpers import (
    document_by_id,
    document_label,
    format_size,
)


STORAGE_ROOT = (
    Path("data")
    / "users"
)


st.set_page_config(
    page_title="Mes CV",
    page_icon="📚",
    layout="wide",
)

user_context = require_streamlit_user()


def create_services():
    """
    Crée des services liés uniquement à l'utilisateur courant.

    Ne pas placer cette fonction dans st.cache_resource :
    elle contient un contexte utilisateur.
    """

    cv_repository = CVRepository(
        user_context=user_context,
        storage_root=STORAGE_ROOT,
    )

    cv_service = CVService(
        repository=cv_repository
    )

    profile_service = (
        UserCVProfileService(
            user_context=user_context,
            storage_root=STORAGE_ROOT,
        )
    )

    association_repository = (
        ProfileCVRepository(
            user_context=user_context,
            cv_repository=cv_repository,
            storage_root=STORAGE_ROOT,
        )
    )

    association_service = (
        ProfileCVService(
            association_repository=(
                association_repository
            ),
            cv_repository=cv_repository,
        )
    )

    return (
        cv_service,
        profile_service,
        association_repository,
        association_service,
    )


(
    cv_service,
    profile_service,
    association_repository,
    association_service,
) = create_services()


def rerun() -> None:
    st.rerun()


def render_import_section() -> None:
    st.subheader(
        "➕ Ajouter un CV"
    )

    with st.form(
        "cv_import_form",
        clear_on_submit=True,
    ):
        uploaded_file = st.file_uploader(
            "Fichier PDF",
            type=["pdf"],
            accept_multiple_files=False,
            key="cv_library_upload",
        )

        title = st.text_input(
            "Titre du CV",
            placeholder=(
                "Ex. CV DSI / CIO"
            ),
        )

        duplicate_policy = st.selectbox(
            "En cas de CV identique",
            options=[
                CVService.DUPLICATE_REUSE,
                CVService.DUPLICATE_REJECT,
                CVService.DUPLICATE_ALLOW,
            ],
            format_func={
                CVService.DUPLICATE_REUSE:
                    "Réutiliser le CV existant",
                CVService.DUPLICATE_REJECT:
                    "Refuser le doublon",
                CVService.DUPLICATE_ALLOW:
                    "Créer une nouvelle copie",
            }.get,
        )

        analyze = st.checkbox(
            "Analyser automatiquement le CV",
            value=True,
        )

        submitted = st.form_submit_button(
            "Importer le CV",
            type="primary",
            use_container_width=True,
        )

    if not submitted:
        return

    if uploaded_file is None:
        st.error(
            "Sélectionne un fichier PDF."
        )
        return

    fallback_title = (
        Path(uploaded_file.name).stem
    )

    try:
        result = cv_service.import_bytes(
            content=uploaded_file.getvalue(),
            title=(
                title.strip()
                or fallback_title
            ),
            original_filename=(
                uploaded_file.name
            ),
            content_type=(
                uploaded_file.type
                or "application/pdf"
            ),
            duplicate_policy=(
                duplicate_policy
            ),
            analyze=analyze,
        )

    except DuplicateCVError as error:
        st.warning(str(error))
        return

    except CVError as error:
        st.error(str(error))
        return

    st.session_state[
        "cv_last_import_result"
    ] = result

    if result.duplicate_reused:
        st.info(
            "Le CV existant a été réutilisé."
        )
    else:
        st.success(
            "Le CV a été ajouté à ta bibliothèque."
        )

    rerun()


def render_last_import_result() -> None:
    result = st.session_state.get(
        "cv_last_import_result"
    )

    if result is None:
        return

    with st.expander(
        "Résultat du dernier import",
        expanded=True,
    ):
        st.write(
            f"**{result.document.title}**"
        )

        st.caption(
            result.document.original_filename
        )

        if result.analysis is not None:
            col1, col2 = st.columns(2)

            col1.metric(
                "Caractères extraits",
                result.analysis.character_count,
            )

            col2.metric(
                "Compétences détectées",
                len(result.skills),
            )

            if result.skills:
                st.write(
                    "**Compétences détectées**"
                )

                st.write(
                    ", ".join(result.skills)
                )

        for warning in result.warnings:
            st.warning(warning)

        if st.button(
            "Fermer ce résultat",
            key="close_cv_import_result",
        ):
            st.session_state.pop(
                "cv_last_import_result",
                None,
            )
            rerun()


def render_document_card(
    document,
) -> None:
    associations = (
        association_repository
        .list_for_cv(document.cv_id)
    )

    profile_ids = [
        association.profile_id
        for association in associations
    ]

    with st.container(
        border=True
    ):
        title_column, action_column = (
            st.columns(
                [4, 1]
            )
        )

        title_column.subheader(
            document.title
        )

        title_column.caption(
            f"{document.original_filename} "
            f"• {format_size(document.size_bytes)}"
        )

        if profile_ids:
            title_column.write(
                "**Profils associés :** "
                + ", ".join(
                    sorted(profile_ids)
                )
            )
        else:
            title_column.caption(
                "Aucun profil associé"
            )

        action_column.download_button(
            "Télécharger",
            data=cv_service.read_cv(
                document.cv_id
            ),
            file_name=(
                document.original_filename
            ),
            mime="application/pdf",
            key=(
                "download_cv_"
                f"{document.cv_id}"
            ),
            use_container_width=True,
        )

        tabs = st.tabs(
            [
                "Analyse",
                "Profils",
                "Renommer",
                "Supprimer",
            ]
        )

        with tabs[0]:
            try:
                analysis = cv_service.analyze(
                    document.cv_id
                )

            except CVAnalysisError as error:
                st.warning(str(error))

            else:
                metric1, metric2 = (
                    st.columns(2)
                )

                metric1.metric(
                    "Caractères",
                    analysis.character_count,
                )

                metric2.metric(
                    "Compétences",
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

        with tabs[1]:
            render_profile_associations(
                document=document,
                associated_profile_ids=(
                    profile_ids
                ),
            )

        with tabs[2]:
            with st.form(
                f"rename_cv_{document.cv_id}"
            ):
                new_title = st.text_input(
                    "Nouveau titre",
                    value=document.title,
                    key=(
                        "rename_title_"
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
                    cv_service.rename_cv(
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

        with tabs[3]:
            if profile_ids:
                st.warning(
                    "Ce CV est encore associé à "
                    "un ou plusieurs profils."
                )

            force_delete = st.checkbox(
                "Détacher le CV de tous les profils",
                key=(
                    "force_delete_cv_"
                    f"{document.cv_id}"
                ),
            )

            confirm_delete = st.checkbox(
                "Je confirme la suppression définitive",
                key=(
                    "confirm_delete_cv_"
                    f"{document.cv_id}"
                ),
            )

            if st.button(
                "Supprimer le CV",
                type="secondary",
                disabled=not confirm_delete,
                key=(
                    "delete_cv_"
                    f"{document.cv_id}"
                ),
                use_container_width=True,
            ):
                try:
                    association_service.delete_cv(
                        document.cv_id,
                        force=force_delete,
                    )

                except CVStillInUseError as error:
                    st.error(str(error))

                except CVError as error:
                    st.error(str(error))

                else:
                    st.session_state.pop(
                        "cv_last_import_result",
                        None,
                    )

                    st.success(
                        "CV supprimé."
                    )
                    rerun()


def render_profile_associations(
    document,
    associated_profile_ids: list[str],
) -> None:
    profile_ids = list(
        profile_service.list_profiles()
    )

    if not profile_ids:
        st.info(
            "Crée d'abord un profil dans "
            "la page « CV et profils »."
        )
        return

    available_profile_ids = [
        profile_id
        for profile_id in profile_ids
        if profile_id
        not in associated_profile_ids
    ]

    if available_profile_ids:
        selected_profile = st.selectbox(
            "Associer à un profil",
            options=available_profile_ids,
            key=(
                "attach_profile_"
                f"{document.cv_id}"
            ),
        )

        make_primary = st.checkbox(
            "Définir comme CV principal",
            value=False,
            key=(
                "attach_primary_"
                f"{document.cv_id}"
            ),
        )

        if st.button(
            "Associer",
            key=(
                "attach_cv_"
                f"{document.cv_id}"
            ),
            use_container_width=True,
        ):
            try:
                association_service.attach_cv(
                    profile_id=selected_profile,
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

    associations = (
        association_repository
        .list_for_cv(document.cv_id)
    )

    if not associations:
        return

    st.divider()
    st.write(
        "**Associations existantes**"
    )

    for association in associations:
        columns = st.columns(
            [3, 1, 1]
        )

        label = association.profile_id

        if association.is_primary:
            label += " ⭐"

        columns[0].write(label)

        if columns[1].button(
            "Principal",
            disabled=association.is_primary,
            key=(
                "set_primary_"
                f"{association.profile_id}_"
                f"{association.cv_id}"
            ),
        ):
            try:
                association_service.set_primary_cv(
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
                "detach_"
                f"{association.profile_id}_"
                f"{association.cv_id}"
            ),
        ):
            try:
                association_service.detach_cv(
                    profile_id=(
                        association.profile_id
                    ),
                    cv_id=association.cv_id,
                )
            except CVError as error:
                st.error(str(error))
            else:
                rerun()


def render_library() -> None:
    documents = cv_service.list_cvs()

    st.subheader(
        f"📚 Ma bibliothèque ({len(documents)})"
    )

    if not documents:
        st.info(
            "Ta bibliothèque ne contient encore "
            "aucun CV."
        )
        return

    documents_by_id = document_by_id(
        documents
    )

    selected_cv_id = st.selectbox(
        "CV à afficher",
        options=list(
            documents_by_id
        ),
        format_func=lambda cv_id: (
            document_label(
                documents_by_id[cv_id]
            )
        ),
    )

    render_document_card(
        documents_by_id[
            selected_cv_id
        ]
    )


st.title(
    "📚 Mes CV"
)

st.caption(
    "Bibliothèque privée de "
    f"{user_context.display_name}"
)

st.warning(
    "Le stockage utilisé par cette version de "
    "Streamlit Cloud est encore local et peut être "
    "réinitialisé lors d'un redéploiement. "
    "La persistance PostgreSQL et objet arrivera "
    "en V3.12.4."
)

left_column, right_column = st.columns(
    [2, 3],
)

with left_column:
    render_import_section()

with right_column:
    render_last_import_result()

st.divider()

render_library()