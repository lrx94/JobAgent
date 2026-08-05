from __future__ import annotations

from collections.abc import Callable, Iterable
from typing import Any

import streamlit as st

from src.learning import (
    LearningSuggestion,
    SuggestionStatus,
)
from src.workspace.learning_service import (
    WorkspaceLearningService,
)
import csv
import io

STATUS_DISPLAY = {
    SuggestionStatus.CANDIDATE: {
        "icon": "🟡",
        "label": "À examiner",
        "section": "À examiner",
    },
    SuggestionStatus.ACCEPTED: {
        "icon": "✅",
        "label": "Acceptée",
        "section": "Acceptées",
    },
    SuggestionStatus.REJECTED: {
        "icon": "❌",
        "label": "Rejetée",
        "section": "Rejetées",
    },
    SuggestionStatus.IGNORED: {
        "icon": "⏸️",
        "label": "Ignorée",
        "section": "Ignorées",
    },
}
def build_learning_export_csv(
    suggestions: Iterable[LearningSuggestion],
) -> bytes:
    """
    Produit un export CSV exploitable pour analyser
    les suggestions du Learning Engine.
    """

    output = io.StringIO(
        newline=""
    )

    writer = csv.writer(
        output,
        delimiter=";",
    )

    writer.writerow(
        (
            "suggestion_id",
            "terme_observe",
            "terme_normalise",
            "statut",
            "type",
            "occurrences",
            "nombre_sources",
            "sources",
            "origines",
            "confiance",
            "cible_canonique",
            "contextes",
        )
    )

    for suggestion in suggestions or ():
        if not isinstance(
            suggestion,
            LearningSuggestion,
        ):
            continue

        writer.writerow(
            (
                suggestion.suggestion_id,
                suggestion.observed_term,
                suggestion.normalized_term,
                suggestion.status.value,
                suggestion.suggestion_type.value,
                suggestion.occurrence_count,
                suggestion.source_count,
                " | ".join(
                    suggestion.sources
                ),
                " | ".join(
                    origin.value
                    for origin
                    in suggestion.origins
                ),
                f"{suggestion.confidence:.3f}",
                suggestion.canonical_target or "",
                " | ".join(
                    suggestion.contexts
                ),
            )
        )

    return output.getvalue().encode(
        "utf-8-sig"
    )

def render_learning_panel(
    *,
    learning_service: WorkspaceLearningService,
    suggestions: Iterable[LearningSuggestion],
    key_prefix: str = "learning",
    on_action_success: Callable[[], None] | None = None,
) -> None:
    if not isinstance(
        learning_service,
        WorkspaceLearningService,
    ):
        raise TypeError(
            "learning_service doit être un "
            "WorkspaceLearningService."
        )

    values = tuple(
        suggestion
        for suggestion in suggestions or ()
        if isinstance(
            suggestion,
            LearningSuggestion,
        )
    )

    if not values:
        st.info(
            "Aucune suggestion d'enrichissement."
        )
        return
    export_data = (
    build_learning_export_csv(
            values
        )
    )

    st.download_button(
        "📤 Exporter les suggestions",
        data=export_data,
        file_name=(
            "jobagent_learning_suggestions.csv"
        ),
        mime="text/csv",
        key=f"{key_prefix}_export",
        width="stretch",
    )
    grouped = {
        status: _sort_suggestions(
            suggestion
            for suggestion in values
            if suggestion.status == status
        )
        for status in (
            SuggestionStatus.CANDIDATE,
            SuggestionStatus.ACCEPTED,
            SuggestionStatus.REJECTED,
            SuggestionStatus.IGNORED,
        )
    }

    candidate_count = len(
        grouped[
            SuggestionStatus.CANDIDATE
        ]
    )

    accepted_count = len(
        grouped[
            SuggestionStatus.ACCEPTED
        ]
    )

    rejected_count = len(
        grouped[
            SuggestionStatus.REJECTED
        ]
    )

    ignored_count = len(
        grouped[
            SuggestionStatus.IGNORED
        ]
    )

    metric_columns = st.columns(4)

    metric_columns[0].metric(
        "À examiner",
        candidate_count,
    )

    metric_columns[1].metric(
        "Acceptées",
        accepted_count,
    )

    metric_columns[2].metric(
        "Rejetées",
        rejected_count,
    )

    metric_columns[3].metric(
        "Ignorées",
        ignored_count,
    )

    if candidate_count == 0:
        st.success(
            "Toutes les suggestions ont été examinées."
        )
    else:
        st.caption(
            f"{candidate_count} suggestion(s) "
            "restent à examiner."
        )

    _render_status_section(
        status=SuggestionStatus.CANDIDATE,
        suggestions=grouped[
            SuggestionStatus.CANDIDATE
        ],
        learning_service=learning_service,
        key_prefix=key_prefix,
        on_action_success=on_action_success,
        expanded=True,
    )

    _render_status_section(
        status=SuggestionStatus.ACCEPTED,
        suggestions=grouped[
            SuggestionStatus.ACCEPTED
        ],
        learning_service=learning_service,
        key_prefix=key_prefix,
        on_action_success=on_action_success,
        expanded=False,
    )

    _render_status_section(
        status=SuggestionStatus.REJECTED,
        suggestions=grouped[
            SuggestionStatus.REJECTED
        ],
        learning_service=learning_service,
        key_prefix=key_prefix,
        on_action_success=on_action_success,
        expanded=False,
    )

    _render_status_section(
        status=SuggestionStatus.IGNORED,
        suggestions=grouped[
            SuggestionStatus.IGNORED
        ],
        learning_service=learning_service,
        key_prefix=key_prefix,
        on_action_success=on_action_success,
        expanded=False,
    )


def _sort_suggestions(
    suggestions: Iterable[LearningSuggestion],
) -> tuple[LearningSuggestion, ...]:
    return tuple(
        sorted(
            suggestions,
            key=lambda suggestion: (
                -suggestion.confidence,
                -suggestion.occurrence_count,
                suggestion.normalized_term,
            ),
        )
    )


def _render_status_section(
    *,
    status: SuggestionStatus,
    suggestions: tuple[
        LearningSuggestion,
        ...
    ],
    learning_service: WorkspaceLearningService,
    key_prefix: str,
    on_action_success: Callable[[], None] | None,
    expanded: bool,
) -> None:
    display = STATUS_DISPLAY[status]

    section_title = (
        f"{display['icon']} "
        f"{display['section']} "
        f"({len(suggestions)})"
    )

    with st.expander(
        section_title,
        expanded=(
            expanded
            and bool(suggestions)
        ),
    ):
        if not suggestions:
            st.caption(
                "Aucune suggestion dans cette catégorie."
            )
            return

        for suggestion in suggestions:
            _render_suggestion(
                learning_service=learning_service,
                suggestion=suggestion,
                key_prefix=key_prefix,
                on_action_success=on_action_success,
            )


def _render_suggestion(
    *,
    learning_service: WorkspaceLearningService,
    suggestion: LearningSuggestion,
    key_prefix: str,
    on_action_success: Callable[[], None] | None,
) -> None:
    label = (
        suggestion.observed_term
        or suggestion.normalized_term
    )

    status_display = STATUS_DISPLAY[
        suggestion.status
    ]

    card_title = (
        f"{status_display['icon']} "
        f"{label} — "
        f"{suggestion.occurrence_count} "
        "occurrence(s)"
    )

    with st.container(
        border=True,
    ):
        st.write(
            f"#### {card_title}"
        )

        st.caption(
            "Statut : "
            f"**{status_display['label']}**"
        )

        metric_columns = st.columns(3)

        metric_columns[0].metric(
            "Occurrences",
            suggestion.occurrence_count,
        )

        metric_columns[1].metric(
            "Sources",
            suggestion.source_count,
        )

        metric_columns[2].metric(
            "Confiance",
            (
                f"{suggestion.confidence * 100:.0f} %"
            ),
        )

        if suggestion.sources:
            st.caption(
                "Sources : "
                + ", ".join(
                    suggestion.sources
                )
            )

        if suggestion.contexts:
            with st.expander(
                "Voir les exemples observés",
                expanded=False,
            ):
                for context in (
                    suggestion.contexts[:3]
                ):
                    st.write(
                        f"- {context}"
                    )

        _render_actions(
            learning_service=learning_service,
            suggestion=suggestion,
            label=label,
            key_prefix=key_prefix,
            on_action_success=on_action_success,
        )


def _render_actions(
    *,
    learning_service: WorkspaceLearningService,
    suggestion: LearningSuggestion,
    label: str,
    key_prefix: str,
    on_action_success: Callable[[], None] | None,
) -> None:
    status = suggestion.status

    if status == SuggestionStatus.CANDIDATE:
        columns = st.columns(3)

        if columns[0].button(
            "✅ Accepter",
            key=(
                f"{key_prefix}_accept_"
                f"{suggestion.suggestion_id}"
            ),
            width="stretch",
        ):
            _apply_action(
                action=learning_service.accept,
                suggestion=suggestion,
                success_message=(
                    f"✅ Suggestion « {label} » "
                    "acceptée."
                ),
                on_action_success=(
                    on_action_success
                ),
            )

        if columns[1].button(
            "⏸️ Ignorer",
            key=(
                f"{key_prefix}_ignore_"
                f"{suggestion.suggestion_id}"
            ),
            width="stretch",
        ):
            _apply_action(
                action=learning_service.ignore,
                suggestion=suggestion,
                success_message=(
                    f"⏸️ Suggestion « {label} » "
                    "ignorée."
                ),
                on_action_success=(
                    on_action_success
                ),
            )

        if columns[2].button(
            "❌ Rejeter",
            key=(
                f"{key_prefix}_reject_"
                f"{suggestion.suggestion_id}"
            ),
            width="stretch",
        ):
            _apply_action(
                action=learning_service.reject,
                suggestion=suggestion,
                success_message=(
                    f"❌ Suggestion « {label} » "
                    "rejetée."
                ),
                on_action_success=(
                    on_action_success
                ),
            )

        return

    if status == SuggestionStatus.ACCEPTED:
        if st.button(
            "❌ Rejeter cette suggestion",
            key=(
                f"{key_prefix}_accepted_reject_"
                f"{suggestion.suggestion_id}"
            ),
            width="stretch",
        ):
            _apply_action(
                action=learning_service.reject,
                suggestion=suggestion,
                success_message=(
                    f"❌ Suggestion « {label} » "
                    "désormais rejetée."
                ),
                on_action_success=(
                    on_action_success
                ),
            )

        return

    if status == SuggestionStatus.REJECTED:
        if st.button(
            "✅ Accepter cette suggestion",
            key=(
                f"{key_prefix}_rejected_accept_"
                f"{suggestion.suggestion_id}"
            ),
            width="stretch",
        ):
            _apply_action(
                action=learning_service.accept,
                suggestion=suggestion,
                success_message=(
                    f"✅ Suggestion « {label} » "
                    "désormais acceptée."
                ),
                on_action_success=(
                    on_action_success
                ),
            )

        return

    if status == SuggestionStatus.IGNORED:
        columns = st.columns(2)

        if columns[0].button(
            "✅ Accepter",
            key=(
                f"{key_prefix}_ignored_accept_"
                f"{suggestion.suggestion_id}"
            ),
            width="stretch",
        ):
            _apply_action(
                action=learning_service.accept,
                suggestion=suggestion,
                success_message=(
                    f"✅ Suggestion « {label} » "
                    "acceptée."
                ),
                on_action_success=(
                    on_action_success
                ),
            )

        if columns[1].button(
            "❌ Rejeter",
            key=(
                f"{key_prefix}_ignored_reject_"
                f"{suggestion.suggestion_id}"
            ),
            width="stretch",
        ):
            _apply_action(
                action=learning_service.reject,
                suggestion=suggestion,
                success_message=(
                    f"❌ Suggestion « {label} » "
                    "rejetée."
                ),
                on_action_success=(
                    on_action_success
                ),
            )


def _apply_action(
    *,
    action: Any,
    suggestion: LearningSuggestion,
    success_message: str,
    on_action_success: Callable[[], None] | None,
) -> None:
    try:
        action(
            suggestion.suggestion_id
        )
    except Exception as error:
        st.error(
            "Impossible de mettre à jour "
            f"la suggestion : {error}"
        )
        return

    if on_action_success is not None:
        on_action_success()

    st.session_state[
        "learning_action_success"
    ] = success_message

    st.rerun()