from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


REMOTE_TYPES = {
    "onsite",
    "hybrid",
    "remote",
    "unknown",
}

SALARY_PERIODS = {
    "hour",
    "day",
    "month",
    "year",
    "unknown",
}


@dataclass
class Job:
    """
    Modèle canonique d'une offre d'emploi.

    Le modèle conserve les anciens champs `salary` et `remote`
    afin de rester compatible avec le matching et l'interface existants.
    """

    title: str
    company: str
    location: str
    description: str
    source: str

    url: str | None = None

    # Identité fournisseur
    external_id: str | None = None

    # Contrat
    contract_type: str | None = None

    # Rémunération canonique
    salary_min: int | None = None
    salary_max: int | None = None
    salary_currency: str = "EUR"
    salary_period: str = "unknown"

    # Organisation du travail
    remote_type: str = "unknown"

    # Dates
    published_at: datetime | None = None
    collected_at: datetime = field(
        default_factory=datetime.now
    )

    # Informations extraites
    skills: list[str] = field(default_factory=list)
    languages: list[str] = field(default_factory=list)
    experience_level: str | None = None
    experience_years: int | None = None

    # Données originales du fournisseur
    raw_data: dict[str, Any] = field(default_factory=dict)

    # Champs historiques conservés pour compatibilité
    salary: int = 0
    remote: bool = False

    # Résultat du matching
    score: float = 0.0
    matched_skills: list[str] = field(default_factory=list)
    missing_skills: list[str] = field(default_factory=list)
    explanation: str = ""
    match_details: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.title = self._clean_required_text(
            self.title,
            "title",
        )

        self.company = self._clean_optional_text(
            self.company,
            "Entreprise inconnue",
        )

        self.location = self._clean_optional_text(
            self.location,
            "Localisation non précisée",
        )

        self.description = self._clean_optional_text(
            self.description,
            "",
        )

        self.source = self._clean_required_text(
            self.source,
            "source",
        )

        self.url = self._clean_optional_value(self.url)
        self.external_id = self._clean_optional_value(
            self.external_id
        )
        self.contract_type = self._clean_optional_value(
            self.contract_type
        )
        self.experience_level = self._clean_optional_value(
            self.experience_level
        )

        self.salary_min = self._normalize_positive_integer(
            self.salary_min
        )

        self.salary_max = self._normalize_positive_integer(
            self.salary_max
        )

        self.salary = (
            self._normalize_positive_integer(self.salary)
            or 0
        )

        if self.salary_min is None and self.salary > 0:
            self.salary_min = self.salary

        if self.salary == 0 and self.salary_min is not None:
            self.salary = self.salary_min

        if (
            self.salary_min is not None
            and self.salary_max is not None
            and self.salary_max < self.salary_min
        ):
            self.salary_min, self.salary_max = (
                self.salary_max,
                self.salary_min,
            )

        normalized_period = str(
            self.salary_period or "unknown"
        ).strip().lower()

        self.salary_period = (
            normalized_period
            if normalized_period in SALARY_PERIODS
            else "unknown"
        )

        normalized_remote_type = str(
            self.remote_type or "unknown"
        ).strip().lower()

        if normalized_remote_type not in REMOTE_TYPES:
            normalized_remote_type = "unknown"

        if self.remote and normalized_remote_type == "unknown":
            normalized_remote_type = "remote"

        self.remote_type = normalized_remote_type

        if self.remote_type == "remote":
            self.remote = True
        elif self.remote_type in {"onsite", "hybrid"}:
            self.remote = False

        self.skills = self._normalize_string_list(
            self.skills
        )
        self.languages = self._normalize_string_list(
            self.languages
        )
        self.matched_skills = self._normalize_string_list(
            self.matched_skills
        )
        self.missing_skills = self._normalize_string_list(
            self.missing_skills
        )

        self.raw_data = dict(self.raw_data or {})
        self.match_details = dict(
            self.match_details or {}
        )

        self.score = float(self.score or 0)

    @property
    def is_remote(self) -> bool:
        return self.remote_type == "remote"

    @property
    def is_hybrid(self) -> bool:
        return self.remote_type == "hybrid"

    @property
    def identity(self) -> str:
        """
        Identité stable utilisable pour la déduplication future.
        """

        if self.external_id:
            return f"{self.source}:{self.external_id}"

        if self.url:
            return self.url

        normalized_parts = [
            self.title.lower().strip(),
            self.company.lower().strip(),
            self.location.lower().strip(),
        ]

        return "|".join(normalized_parts)

    @staticmethod
    def _clean_required_text(
        value: str,
        field_name: str,
    ) -> str:
        cleaned = str(value or "").strip()

        if not cleaned:
            raise ValueError(
                f"Le champ Job.{field_name} est obligatoire."
            )

        return cleaned

    @staticmethod
    def _clean_optional_text(
        value: str | None,
        default: str,
    ) -> str:
        cleaned = str(value or "").strip()

        return cleaned or default

    @staticmethod
    def _clean_optional_value(
        value: str | None,
    ) -> str | None:
        if value is None:
            return None

        cleaned = str(value).strip()

        return cleaned or None

    @staticmethod
    def _normalize_positive_integer(
        value: int | float | str | None,
    ) -> int | None:
        if value in {None, ""}:
            return None

        try:
            normalized = int(float(value))
        except (TypeError, ValueError):
            return None

        return normalized if normalized >= 0 else None

    @staticmethod
    def _normalize_string_list(
        values: list[str] | tuple[str, ...] | None,
    ) -> list[str]:
        normalized: list[str] = []
        seen: set[str] = set()

        for value in values or []:
            cleaned = str(value).strip()

            if not cleaned:
                continue

            key = cleaned.casefold()

            if key in seen:
                continue

            seen.add(key)
            normalized.append(cleaned)

        return normalized