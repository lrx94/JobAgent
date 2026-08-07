"""Adaptateur compatible vers la connaissance partagée des compétences."""

from __future__ import annotations

from src.ai.skill_dictionary import SKILL_SYNONYMS

_LEGACY_SKILL_ALIASES = {

    "python": [
        "python",
        "python3",
        "python 3",
        "cpython"
    ],

    "sql": [
        "sql",
        "postgresql",
        "postgres",
        "mysql",
        "mariadb",
        "sqlite",
        "sql server",
        "tsql",
        "t-sql",
        "oracle sql"
    ],

    "azure": [
        "azure",
        "microsoft azure",
        "azure data factory",
        "azure synapse",
        "azure databricks",
        "azure ml",
        "azure cloud"
    ],

    "spark": [
        "spark",
        "apache spark",
        "spark sql",
        "spark streaming",
        "pyspark"
    ],

    "etl": [
        "etl",
        "elt",
        "data pipeline",
        "data integration",
        "pipeline"
    ]
}


def _merge_aliases() -> dict[str, list[str]]:
    """Fusionne la source partagée et les alias historiques sans doublon."""

    merged: dict[str, list[str]] = {}

    for source in (SKILL_SYNONYMS, _LEGACY_SKILL_ALIASES):
        for canonical, aliases in source.items():
            values = merged.setdefault(canonical, [])
            seen = {value.casefold() for value in values}

            for alias in aliases:
                normalized = str(alias).strip()

                if not normalized or normalized.casefold() in seen:
                    continue

                seen.add(normalized.casefold())
                values.append(normalized)

    return merged


# Nom historique conservé pour les imports existants.
SKILL_ALIASES = _merge_aliases()
