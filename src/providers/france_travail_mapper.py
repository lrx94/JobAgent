from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from src.domain import Job


class FranceTravailJobMapper:
    """
    Convertit une annonce France Travail en modèle Job canonique.
    """

    SOURCE_NAME = "France Travail"

    def map(
        self,
        item: dict[str, Any],
    ) -> Job | None:
        if not isinstance(item, dict):
            return None

        external_id = self._text(
            item.get("id")
        )

        title = self._text(
            item.get("intitule")
            or item.get("title")
        )

        if not external_id or not title:
            return None

        company_data = item.get(
            "entreprise",
            {},
        )

        if not isinstance(
            company_data,
            dict,
        ):
            company_data = {}

        company = self._text(
            company_data.get("nom")
        ) or "Entreprise inconnue"

        location = self._location(
            item.get("lieuTravail")
        )

        description = self._text(
            item.get("description")
        )

        url = self._extract_url(
            item
        )

        contract_type = self._text(
            item.get("typeContratLibelle")
            or item.get("typeContrat")
        ) or None

        salary_min, salary_max = (
            self._salary_range(
                item.get("salaire")
            )
        )

        remote_type = self._remote_type(
            item
        )

        published_at = (
            self._datetime(
                item.get("dateCreation")
            )
        )

        skills = self._skills(
            item.get("competences")
        )

        languages = self._languages(
            item.get("langues")
        )

        return Job(
            title=title,
            company=company,
            location=location,
            description=description,
            source=self.SOURCE_NAME,
            url=url,
            external_id=external_id,
            contract_type=contract_type,
            salary_min=salary_min,
            salary_max=salary_max,
            salary_currency="EUR",
            salary_period=(
                "year"
                if salary_min is not None
                or salary_max is not None
                else "unknown"
            ),
            remote_type=remote_type,
            published_at=published_at,
            skills=skills,
            languages=languages,
            raw_data=dict(item),
            remote=(
                remote_type == "remote"
            ),
        )

    def map_many(
        self,
        items: list[dict[str, Any]],
    ) -> list[Job]:
        jobs: list[Job] = []

        for item in items:
            job = self.map(item)

            if job is not None:
                jobs.append(job)

        return jobs

    @classmethod
    def _location(
        cls,
        value: Any,
    ) -> str:
        if isinstance(value, dict):
            label = cls._text(
                value.get("libelle")
            )

            if label:
                return label

            city = cls._text(
                value.get("commune")
            )

            if city:
                return city

        return (
            "Localisation non précisée"
        )

    @classmethod
    def _extract_url(
        cls,
        item: dict[str, Any],
    ) -> str | None:
        origin = item.get(
            "origineOffre",
            {},
        )

        if isinstance(origin, dict):
            for key in (
                "urlOrigine",
                "url",
            ):
                value = cls._text(
                    origin.get(key)
                )

                if value:
                    return value

        external_id = cls._text(
            item.get("id")
        )

        if not external_id:
            return None

        return (
            "https://candidat.francetravail.fr/"
            "offres/recherche/detail/"
            f"{external_id}"
        )

    @classmethod
    def _salary_range(
        cls,
        value: Any,
    ) -> tuple[int | None, int | None]:
        if not isinstance(value, dict):
            return None, None

        minimum = cls._integer(
            value.get("min")
            or value.get("salaireMin")
        )

        maximum = cls._integer(
            value.get("max")
            or value.get("salaireMax")
        )

        if minimum is None:
            minimum = cls._first_number(
                value.get("libelle")
            )

        if (
            minimum is not None
            and maximum is not None
            and maximum < minimum
        ):
            minimum, maximum = (
                maximum,
                minimum,
            )

        return minimum, maximum

    @classmethod
    def _remote_type(
        cls,
        item: dict[str, Any],
    ) -> str:
        text = " ".join(
            [
                cls._text(
                    item.get("description")
                ),
                cls._text(
                    item.get(
                        "complementExercice"
                    )
                ),
            ]
        ).casefold()

        if any(
            term in text
            for term in (
                "100% télétravail",
                "100 % télétravail",
                "full remote",
                "entièrement à distance",
            )
        ):
            return "remote"

        if any(
            term in text
            for term in (
                "télétravail",
                "hybride",
                "hybrid",
            )
        ):
            return "hybrid"

        return "unknown"

    @classmethod
    def _skills(
        cls,
        value: Any,
    ) -> list[str]:
        if not isinstance(value, list):
            return []

        skills: list[str] = []

        for item in value:
            if isinstance(item, dict):
                skill = cls._text(
                    item.get("libelle")
                    or item.get("code")
                )
            else:
                skill = cls._text(item)

            if skill:
                skills.append(skill)

        return cls._deduplicate(skills)

    @classmethod
    def _languages(
        cls,
        value: Any,
    ) -> list[str]:
        if not isinstance(value, list):
            return []

        languages: list[str] = []

        for item in value:
            if isinstance(item, dict):
                language = cls._text(
                    item.get("libelle")
                )
            else:
                language = cls._text(
                    item
                )

            if language:
                languages.append(
                    language
                )

        return cls._deduplicate(
            languages
        )

    @staticmethod
    def _datetime(
        value: Any,
    ) -> datetime | None:
        text = str(
            value or ""
        ).strip()

        if not text:
            return None

        try:
            parsed = datetime.fromisoformat(
                text.replace(
                    "Z",
                    "+00:00",
                )
            )
        except ValueError:
            return None

        if parsed.tzinfo is None:
            parsed = parsed.replace(
                tzinfo=timezone.utc
            )

        return parsed

    @staticmethod
    def _first_number(
        value: Any,
    ) -> int | None:
        text = str(
            value or ""
        )

        number = ""
        started = False

        for character in text:
            if character.isdigit():
                number += character
                started = True
            elif started:
                break

        if not number:
            return None

        return int(number)

    @staticmethod
    def _integer(
        value: Any,
    ) -> int | None:
        if value in {
            None,
            "",
        }:
            return None

        try:
            normalized = int(
                float(value)
            )
        except (
            TypeError,
            ValueError,
        ):
            return None

        return (
            normalized
            if normalized >= 0
            else None
        )

    @staticmethod
    def _text(
        value: Any,
    ) -> str:
        return str(
            value or ""
        ).strip()

    @staticmethod
    def _deduplicate(
        values: list[str],
    ) -> list[str]:
        result: list[str] = []
        seen: set[str] = set()

        for value in values:
            key = value.casefold()

            if key in seen:
                continue

            seen.add(key)
            result.append(value)

        return result