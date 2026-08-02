from __future__ import annotations

import json
from collections.abc import Iterable
from pathlib import Path
from typing import Any

from src.auth.exceptions import (
    AuthorizationConfigurationError,
)


class AllowListRepository:
    """
    Repository local des adresses autorisées.

    La source peut être :

    - un fichier JSON ;
    - une collection d'adresses fournie en mémoire.

    Le chargement est effectué une seule fois puis mis en cache.
    La méthode reload() permet de forcer une nouvelle lecture.
    """

    JSON_KEY = "allowed_emails"

    def __init__(
        self,
        path: str | Path | None = None,
        emails: Iterable[str] | None = None,
    ) -> None:
        if path is not None and emails is not None:
            raise ValueError(
                "Fournir soit path, soit emails, "
                "mais pas les deux."
            )

        self.path = (
            Path(path)
            if path is not None
            else None
        )

        self._initial_emails = (
            tuple(emails)
            if emails is not None
            else None
        )

        self._cache: set[str] | None = None

    def allowed_emails(
        self,
    ) -> set[str]:
        """
        Retourne une copie défensive des adresses autorisées.
        """

        if self._cache is None:
            self._cache = self._load()

        return set(self._cache)

    def is_allowed_email(
        self,
        email: str,
    ) -> bool:
        """
        Vérifie une adresse après normalisation.
        """

        normalized = self.normalize_email(
            email,
            required=False,
        )

        if not normalized:
            return False

        return normalized in self.allowed_emails()

    def reload(self) -> set[str]:
        """
        Invalide le cache et relit la source.
        """

        self._cache = None
        return self.allowed_emails()

    def _load(self) -> set[str]:
        if self._initial_emails is not None:
            return self._normalize_collection(
                self._initial_emails
            )

        if self.path is None:
            return set()

        if not self.path.exists():
            return set()

        if not self.path.is_file():
            raise AuthorizationConfigurationError(
                "Le chemin de la liste blanche "
                f"n'est pas un fichier : {self.path}"
            )

        try:
            raw_content = self.path.read_text(
                encoding="utf-8"
            )
        except OSError as error:
            raise AuthorizationConfigurationError(
                "Impossible de lire la liste blanche : "
                f"{self.path}"
            ) from error

        if not raw_content.strip():
            return set()

        try:
            data = json.loads(
                raw_content
            )
        except json.JSONDecodeError as error:
            raise AuthorizationConfigurationError(
                "Le fichier de liste blanche "
                "contient un JSON invalide."
            ) from error

        values = self._extract_email_values(
            data
        )

        return self._normalize_collection(
            values
        )

    @classmethod
    def _extract_email_values(
        cls,
        data: Any,
    ) -> Iterable[str]:
        if isinstance(data, list):
            return data

        if isinstance(data, dict):
            values = data.get(
                cls.JSON_KEY,
                [],
            )

            if not isinstance(values, list):
                raise AuthorizationConfigurationError(
                    f"Le champ {cls.JSON_KEY!r} "
                    "doit être une liste."
                )

            return values

        raise AuthorizationConfigurationError(
            "La liste blanche doit être un objet JSON "
            "ou une liste JSON."
        )

    @classmethod
    def _normalize_collection(
        cls,
        values: Iterable[Any],
    ) -> set[str]:
        normalized: set[str] = set()

        for value in values:
            if value is None:
                continue

            if not isinstance(value, str):
                raise AuthorizationConfigurationError(
                    "Chaque adresse autorisée doit "
                    "être une chaîne de caractères."
                )

            cleaned = cls.normalize_email(
                value,
                required=False,
            )

            if cleaned:
                normalized.add(cleaned)

        return normalized

    @staticmethod
    def normalize_email(
        value: str,
        required: bool = True,
    ) -> str:
        cleaned = str(
            value or ""
        ).strip().casefold()

        if not cleaned:
            if required:
                raise ValueError(
                    "L'adresse e-mail est obligatoire."
                )

            return ""

        local_part, separator, domain = (
            cleaned.partition("@")
        )

        if (
            separator != "@"
            or not local_part
            or not domain
            or "." not in domain
        ):
            raise AuthorizationConfigurationError(
                f"Adresse e-mail invalide : {value!r}"
            )

        return cleaned