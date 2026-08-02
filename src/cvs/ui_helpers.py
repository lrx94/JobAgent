from __future__ import annotations

from collections.abc import Iterable

from src.cvs.models import CVDocument
from src.cvs.profile_cv_models import (
    ProfileCVAssociation,
)


def format_size(
    size_bytes: int,
) -> str:
    """
    Retourne une taille lisible pour l'interface.
    """

    size = max(
        0,
        int(size_bytes),
    )

    units = (
        "o",
        "Ko",
        "Mo",
        "Go",
    )

    value = float(size)

    for unit in units:
        if value < 1024 or unit == units[-1]:
            if unit == "o":
                return f"{int(value)} {unit}"

            return f"{value:.1f} {unit}"

        value /= 1024

    return f"{size} o"


def document_label(
    document: CVDocument,
) -> str:
    """
    Libellé compact utilisable dans un selectbox.
    """

    return (
        f"{document.title} "
        f"— {document.original_filename}"
    )


def document_by_id(
    documents: Iterable[CVDocument],
) -> dict[str, CVDocument]:
    return {
        document.cv_id: document
        for document in documents
    }


def association_by_cv_id(
    associations: Iterable[
        ProfileCVAssociation
    ],
) -> dict[str, ProfileCVAssociation]:
    return {
        association.cv_id: association
        for association in associations
    }


def primary_cv_id(
    associations: Iterable[
        ProfileCVAssociation
    ],
) -> str | None:
    for association in associations:
        if association.is_primary:
            return association.cv_id

    return None


def profile_ids_for_cv(
    associations: Iterable[
        ProfileCVAssociation
    ],
    cv_id: str,
) -> tuple[str, ...]:
    normalized_cv_id = str(
        cv_id or ""
    ).strip()

    result = sorted(
        {
            association.profile_id
            for association in associations
            if association.cv_id
            == normalized_cv_id
        }
    )

    return tuple(result)