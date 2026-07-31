from __future__ import annotations

from dataclasses import dataclass, field

from src.profile import Profile


@dataclass
class SearchRequest:
    """
    Critères indépendants du profil et des fournisseurs.

    Un Profile décrit une personne.
    Un SearchRequest décrit une recherche d'emploi.
    """

    keywords: list[str] = field(default_factory=list)
    locations: list[str] = field(default_factory=list)

    salary_min: int | None = None
    remote: bool = False

    contract_types: list[str] = field(
        default_factory=list
    )

    published_within_days: int | None = None

    page: int = 1
    page_size: int = 20

    def __post_init__(self) -> None:
        self.keywords = self._normalize_list(
            self.keywords
        )

        self.locations = self._normalize_list(
            self.locations
        )

        self.contract_types = self._normalize_list(
            self.contract_types
        )

        self.salary_min = self._normalize_positive_integer(
            self.salary_min
        )

        self.published_within_days = (
            self._normalize_positive_integer(
                self.published_within_days
            )
        )

        self.page = max(
            1,
            self._normalize_positive_integer(self.page)
            or 1,
        )

        normalized_page_size = (
            self._normalize_positive_integer(
                self.page_size
            )
            or 20
        )

        self.page_size = min(
            max(normalized_page_size, 1),
            100,
        )

        self.remote = bool(self.remote)

    @classmethod
    def from_profile(
        cls,
        profile: Profile,
    ) -> SearchRequest:
        return cls(
            keywords=list(profile.keywords or []),
            locations=list(profile.locations or []),
            salary_min=profile.salary_min or None,
            remote=profile.remote,
        )

    @property
    def primary_keyword(self) -> str:
        return self.keywords[0] if self.keywords else ""

    @property
    def primary_location(self) -> str:
        return self.locations[0] if self.locations else ""

    @staticmethod
    def _normalize_list(
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