from __future__ import annotations

from collections.abc import Iterable
from typing import Any

import streamlit as st

from src.learning import (
    LearningSuggestion,
    SuggestionStatus,
)
from src.workspace.learning_service import (
    WorkspaceLearningService,
)
from collections.abc import (
    Callable,
    Iterable,
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

    candidates = tuple(
        sorted(
            (
                suggestion
                for suggestion in suggestions or ()
                if suggestion.status
                == SuggestionStatus.CANDIDATE
            ),
            key=lambda suggestion: (
                -suggestion.confidence,
                -suggestion.occurrence_count,
                suggestion.normalized_term,
            ),
        )
    )

    if not candidates:
        st.info(
            "Aucune nouvelle suggestion "
            "d'enrichissement."
        )
        return

    st.caption(
        f"{len(candidates)} suggestion(s) à examiner."
    )

    for suggestion in candidates:
        _render_suggestion(
            learning_service=learning_service,
            suggestion=suggestion,
            key_prefix=key_prefix,
        )


def _render_suggestion(
    *,
    learning_service: WorkspaceLearningService,
    suggestion: LearningSuggestion,
    key_prefix: str,
    on_action_success: Callable[[], None] | None = None,
) -> None:
    label = (
        suggestion.observed_term
        or suggestion.normalized_term
    )

    with st.expander(
        (
            f"⭐ {label} — "
            f"{suggestion.occurrence_count} occurrence(s)"
        ),
        expanded=False,
    ):
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
            f"{suggestion.confidence * 100:.0f} %",
        )

        if suggestion.sources:
            st.caption(
                "Sources : "
                + ", ".join(suggestion.sources)
            )

        if suggestion.contexts:
            st.write("**Exemples observés**")

            for context in suggestion.contexts[:2]:
                st.write(f"- {context}")

        action_columns = st.columns(3)

        accepted = action_columns[0].button(
            "Accepter",
            key=(
                f"{key_prefix}_accept_"
                f"{suggestion.suggestion_id}"
            ),
            use_container_width=True,
        )

        ignored = action_columns[1].button(
            "Ignorer",
            key=(
                f"{key_prefix}_ignore_"
                f"{suggestion.suggestion_id}"
            ),
            use_container_width=True,
        )

        rejected = action_columns[2].button(
            "Rejeter",
            key=(
                f"{key_prefix}_reject_"
                f"{suggestion.suggestion_id}"
            ),
            use_container_width=True,
        )

        if accepted:
            _apply_action(
                learning_service.accept,
                suggestion.suggestion_id,
                "Suggestion acceptée.",
                on_action_success=on_action_success,
            )

        if ignored:
            _apply_action(
                learning_service.ignore,
                suggestion.suggestion_id,
                "Suggestion ignorée.",
                on_action_success=on_action_success,
            )

        if rejected:
            _apply_action(
                learning_service.reject,
                suggestion.suggestion_id,
                "Suggestion rejetée.",
                on_action_success=on_action_success,
            )


def _apply_action(
    action: Any,
    suggestion_id: str,
    success_message: str,
    on_action_success: Callable[[], None] | None = None,
) -> None:
    try:
        action(suggestion_id)
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