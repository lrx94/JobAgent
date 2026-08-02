from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class ProviderStatus:
    """
    État d'un provider recommandé pour un métier.
    """

    provider_id: str
    label: str
    status: str
    recommended: bool
    available: bool
    message: str

    @property
    def operational(self) -> bool:
        return (
            self.available
            and self.status == "available"
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "provider_id": self.provider_id,
            "label": self.label,
            "status": self.status,
            "recommended": self.recommended,
            "available": self.available,
            "operational": self.operational,
            "message": self.message,
        }


class ProviderAdvisor:
    """
    Compare les providers recommandés par le métier
    avec ceux réellement disponibles dans JobAgent.
    """

    PROVIDER_LABELS = {
        "remoteok": "RemoteOK",
        "francetravail": "France Travail",
        "apec": "APEC",
        "welcometothejungle": "Welcome to the Jungle",
        "linkedin": "LinkedIn",
    }

    IMPLEMENTED_PROVIDERS = {
        "remoteok",
    }

    def evaluate(
        self,
        recommended_providers: (
            list[str]
            | tuple[str, ...]
            | None
        ),
        available_provider_names: (
            list[str]
            | tuple[str, ...]
            | None
        ),
    ) -> list[ProviderStatus]:
        recommended = self._normalize_names(
            recommended_providers
        )

        available = self._normalize_names(
            available_provider_names
        )

        provider_ids: list[str] = []
        seen: set[str] = set()

        for provider_id in [
            *recommended,
            *available,
        ]:
            if provider_id in seen:
                continue

            seen.add(provider_id)
            provider_ids.append(provider_id)

        statuses = [
            self._create_status(
                provider_id=provider_id,
                recommended=(
                    provider_id in recommended
                ),
                available=(
                    provider_id in available
                ),
            )
            for provider_id in provider_ids
        ]

        statuses.sort(
            key=lambda item: (
                not item.recommended,
                not item.operational,
                item.label.casefold(),
            )
        )

        return statuses

    def _create_status(
        self,
        provider_id: str,
        recommended: bool,
        available: bool,
    ) -> ProviderStatus:
        label = self.PROVIDER_LABELS.get(
            provider_id,
            provider_id,
        )

        implemented = (
            provider_id
            in self.IMPLEMENTED_PROVIDERS
        )

        if available:
            status = "available"
            message = (
                "Provider disponible et opérationnel."
            )

        elif implemented:
            status = "not_configured"
            message = (
                "Provider implémenté mais non disponible "
                "dans le service courant."
            )

        else:
            status = "not_implemented"
            message = (
                "Provider recommandé mais pas encore "
                "implémenté dans JobAgent."
            )

        return ProviderStatus(
            provider_id=provider_id,
            label=label,
            status=status,
            recommended=recommended,
            available=available,
            message=message,
        )

    @classmethod
    def canonical_provider_id(
        cls,
        value: str,
    ) -> str:
        normalized = "".join(
            character
            for character in str(
                value or ""
            ).casefold()
            if character.isalnum()
        )

        aliases = {
            "remoteokprovider": "remoteok",
            "remoteok": "remoteok",
            "francetravailprovider": (
                "francetravail"
            ),
            "francetravail": (
                "francetravail"
            ),
            "welcome": (
                "welcometothejungle"
            ),
            "welcometothejungle": (
                "welcometothejungle"
            ),
            "linkedinprovider": "linkedin",
            "linkedin": "linkedin",
            "apec": "apec",
        }

        return aliases.get(
            normalized,
            normalized,
        )

    @classmethod
    def _normalize_names(
        cls,
        values: (
            list[str]
            | tuple[str, ...]
            | None
        ),
    ) -> list[str]:
        normalized: list[str] = []
        seen: set[str] = set()

        for value in values or []:
            provider_id = (
                cls.canonical_provider_id(
                    value
                )
            )

            if not provider_id:
                continue

            if provider_id in seen:
                continue

            seen.add(provider_id)
            normalized.append(
                provider_id
            )

        return normalized