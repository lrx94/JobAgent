from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from src.workspace.models import Workspace
from src.workspace.ui.models import (
    WorkspaceCVItem,
    WorkspaceProfileItem,
    WorkspaceSnapshot,
)


def format_file_size(
    size_bytes: int,
) -> str:
    """
    Convertit une taille en libellé lisible.
    """

    size = max(
        0,
        int(size_bytes),
    )

    if size < 1024:
        return f"{size} o"

    if size < 1024 * 1024:
        return f"{size / 1024:.1f} Ko"

    if size < 1024 * 1024 * 1024:
        return (
            f"{size / (1024 * 1024):.1f} Mo"
        )

    return (
        f"{size / (1024 * 1024 * 1024):.1f} Go"
    )


def profile_display_name(
    profile_id: str,
    config: dict[str, Any],
) -> str:
    """
    Retourne le nom fonctionnel du profil.
    """

    candidates = (
        config.get("name"),
        config.get("title"),
        config.get("profile_name"),
    )

    for candidate in candidates:
        value = str(
            candidate or ""
        ).strip()

        if value:
            return value

    return (
        str(profile_id)
        .replace("_", " ")
        .replace("-", " ")
        .title()
    )


def load_profile_config(
    config_path: str | Path,
) -> dict[str, Any]:
    """
    Charge sans erreur bloquante la configuration
    JSON d'un profil.
    """

    path = Path(config_path)

    if not path.is_file():
        return {}

    try:
        data = json.loads(
            path.read_text(
                encoding="utf-8"
            )
        )
    except (
        OSError,
        json.JSONDecodeError,
    ):
        return {}

    if not isinstance(data, dict):
        return {}

    return data


def build_workspace_snapshot(
    workspace: Workspace,
) -> WorkspaceSnapshot:
    """
    Assemble les profils, CV et associations pour l'UI.

    Aucune donnée n'est persistée par cette fonction.
    """

    if not isinstance(
        workspace,
        Workspace,
    ):
        raise TypeError(
            "workspace doit être une instance "
            "de Workspace."
        )

    documents = (
        workspace
        .cv_service
        .list_cvs()
    )

    documents_by_id = {
        document.cv_id: document
        for document in documents
    }

    associated_cv_ids: set[str] = set()
    profiles: list[WorkspaceProfileItem] = []

    profile_ids = sorted(
        workspace
        .profile_service
        .list_profiles(),
        key=str.casefold,
    )

    for profile_id in profile_ids:
        config_path = (
            workspace
            .services
            .paths
            .profile_config_file(
                profile_id
            )
        )

        config = load_profile_config(
            config_path
        )

        associations = (
            workspace
            .association_repository
            .list_for_profile(
                profile_id
            )
        )

        cv_items: list[WorkspaceCVItem] = []

        for association in associations:
            document = documents_by_id.get(
                association.cv_id
            )

            if document is None:
                continue

            associated_cv_ids.add(
                document.cv_id
            )

            cv_items.append(
                WorkspaceCVItem(
                    cv_id=document.cv_id,
                    title=document.title,
                    original_filename=(
                        document.original_filename
                    ),
                    size_bytes=(
                        document.size_bytes
                    ),
                    is_primary=(
                        association.is_primary
                    ),
                )
            )

        cv_items.sort(
            key=lambda item: (
                not item.is_primary,
                item.title.casefold(),
            )
        )

        profiles.append(
            WorkspaceProfileItem(
                profile_id=profile_id,
                display_name=(
                    profile_display_name(
                        profile_id,
                        config,
                    )
                ),
                config=config,
                cvs=tuple(cv_items),
            )
        )

    unassigned_cvs = [
        WorkspaceCVItem(
            cv_id=document.cv_id,
            title=document.title,
            original_filename=(
                document.original_filename
            ),
            size_bytes=document.size_bytes,
            is_primary=False,
        )
        for document in documents
        if document.cv_id
        not in associated_cv_ids
    ]

    unassigned_cvs.sort(
        key=lambda item: (
            item.title.casefold()
        )
    )

    profiles.sort(
        key=lambda item: (
            item.display_name.casefold()
        )
    )

    return WorkspaceSnapshot(
        profiles=tuple(profiles),
        unassigned_cvs=tuple(
            unassigned_cvs
        ),
    )