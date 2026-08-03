from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import fields, is_dataclass
from datetime import date, datetime, time
from enum import Enum
from pathlib import Path
from typing import Any


JSON_PRIMITIVES = (
    str,
    int,
    float,
    bool,
    type(None),
)


def to_json_compatible(
    value: Any,
) -> Any:
    """
    Convertit récursivement une valeur Python en structure
    compatible avec json.dumps().

    Types pris en charge :
    - primitives JSON ;
    - dataclasses, dont SemanticMatch ;
    - dictionnaires ;
    - listes, tuples et ensembles ;
    - dates et heures ;
    - Enum ;
    - Path ;
    - objets exposant to_dict() ;
    - objets simples exposant __dict__.

    En dernier recours, la valeur est convertie en chaîne.
    """

    if isinstance(value, JSON_PRIMITIVES):
        return value

    if isinstance(
        value,
        (
            datetime,
            date,
            time,
        ),
    ):
        return value.isoformat()

    if isinstance(value, Enum):
        return to_json_compatible(
            value.value
        )

    if isinstance(value, Path):
        return str(value)

    if is_dataclass(value):
        return {
            field.name: to_json_compatible(
                getattr(
                    value,
                    field.name,
                )
            )
            for field in fields(value)
        }

    if isinstance(value, Mapping):
        return {
            str(key): to_json_compatible(
                item
            )
            for key, item in value.items()
        }

    if isinstance(
        value,
        (
            list,
            tuple,
            set,
            frozenset,
        ),
    ):
        return [
            to_json_compatible(item)
            for item in value
        ]

    to_dict = getattr(
        value,
        "to_dict",
        None,
    )

    if callable(to_dict):
        return to_json_compatible(
            to_dict()
        )

    object_dictionary = getattr(
        value,
        "__dict__",
        None,
    )

    if isinstance(
        object_dictionary,
        dict,
    ):
        return {
            str(key): to_json_compatible(
                item
            )
            for key, item
            in object_dictionary.items()
            if not str(key).startswith("_")
        }

    return str(value)


def json_dumps(
    value: Any,
) -> str:
    """
    Sérialise une valeur après conversion vers un format JSON sûr.
    """

    return json.dumps(
        to_json_compatible(value),
        ensure_ascii=False,
    )