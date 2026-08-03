from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Iterable

from src.career.job_role_catalog import (
    JOB_ROLE_CATALOG,
)
from src.career.models import RoleSuggestion
from src.providers.capabilities import (
    PROVIDER_CAPABILITIES,
    ProviderCapability,
)


@dataclass(frozen=True, slots=True)
class ProviderSelectionItem:
    """
    Décision prise pour un provider.
    """

    provider_id: str
    label: str

    recommended: bool
    implemented: bool
    available: bool
    selected: bool
    fallback: bool

    score: int
    reasons: tuple[str, ...] = ()

    @property
    def operational(self) -> bool:
        return (
            self.implemented
            and self.available
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "provider_id": self.provider_id,
            "label": self.label,
            "recommended": self.recommended,
            "implemented": self.implemented,
            "available": self.available,
            "selected": self.selected,
            "fallback": self.fallback,
            "operational": self.operational,
            "score": self.score,
            "reasons": list(self.reasons),
        }


@dataclass(slots=True)
class ProviderSelectionResult:
    """
    Résultat global de la sélection intelligente.
    """

    items: list[ProviderSelectionItem] = field(
        default_factory=list
    )

    @property
    def selected_provider_ids(self) -> list[str]:
        return [
            item.provider_id
            for item in self.items
            if item.selected
        ]

    @property
    def operational_provider_ids(self) -> list[str]:
        return [
            item.provider_id
            for item in self.items
            if item.operational
        ]

    @property
    def missing_recommended_provider_ids(
        self,
    ) -> list[str]:
        return [
            item.provider_id
            for item in self.items
            if item.recommended
            and not item.operational
        ]

    @property
    def has_operational_selection(self) -> bool:
        return any(
            item.selected
            and item.operational
            for item in self.items
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "selected_provider_ids": (
                self.selected_provider_ids
            ),
            "operational_provider_ids": (
                self.operational_provider_ids
            ),
            "missing_recommended_provider_ids": (
                self.missing_recommended_provider_ids
            ),
            "has_operational_selection": (
                self.has_operational_selection
            ),
            "providers": [
                item.to_dict()
                for item in self.items
            ],
        }


class ProviderSelector:
    """
    Sélectionne les providers selon :

    - les recommandations portées par le métier ;
    - les capacités déclarées des providers ;
    - les providers réellement disponibles ;
    - une stratégie de repli lorsque les sources prioritaires
      ne sont pas encore opérationnelles.
    """

    RECOMMENDED_BONUS = 100
    ROLE_SUPPORT_BONUS = 30
    CATEGORY_SUPPORT_BONUS = 20
    AVAILABLE_BONUS = 50
    IMPLEMENTED_BONUS = 20
    EXECUTIVE_BONUS = 10
    REMOTE_BONUS = 5

    def __init__(
        self,
        capabilities: Iterable[
            ProviderCapability
        ] | None = None,
    ) -> None:
        self.capabilities = tuple(
            capabilities
            if capabilities is not None
            else PROVIDER_CAPABILITIES
        )

    def select(
        self,
        selected_role: RoleSuggestion | None,
        available_provider_names: (
            list[str]
            | tuple[str, ...]
            | None
        ),
        remote_requested: bool = False,
    ) -> ProviderSelectionResult:
        role_id = (
            selected_role.role_id
            if selected_role is not None
            else None
        )

        recommended_ids = {
            self.canonical_provider_id(
                provider_name
            )
            for provider_name
            in (
                selected_role
                .preferred_providers
                if selected_role is not None
                else ()
            )
        }

        available_ids = {
            self.canonical_provider_id(
                provider_name
            )
            for provider_name
            in available_provider_names or []
        }

        role_categories = self._role_categories(
            role_id
        )

        executive_role = (
            "executive"
            in {
                category.casefold()
                for category in role_categories
            }
        )

        preliminary: list[
            dict[str, Any]
        ] = []

        known_ids: set[str] = set()

        for capability in self.capabilities:
            provider_id = (
                self.canonical_provider_id(
                    capability.provider_id
                )
            )

            known_ids.add(provider_id)

            recommended = (
                provider_id
                in recommended_ids
            )

            available = (
                provider_id
                in available_ids
            )

            reasons: list[str] = []
            score = max(
                0,
                100 - capability.priority,
            )

            if recommended:
                score += self.RECOMMENDED_BONUS
                reasons.append(
                    "Provider recommandé pour le métier."
                )

            if capability.supports_role(
                role_id
            ):
                score += self.ROLE_SUPPORT_BONUS
                reasons.append(
                    "Le provider couvre ce métier."
                )

            if capability.supports_any_category(
                role_categories
            ):
                score += (
                    self.CATEGORY_SUPPORT_BONUS
                )
                reasons.append(
                    "Les catégories du métier sont couvertes."
                )

            if capability.implemented:
                score += self.IMPLEMENTED_BONUS
                reasons.append(
                    "Provider implémenté dans JobAgent."
                )

            if available:
                score += self.AVAILABLE_BONUS
                reasons.append(
                    "Provider disponible dans le service."
                )

            if (
                executive_role
                and capability.executive_roles
            ):
                score += self.EXECUTIVE_BONUS
                reasons.append(
                    "Provider adapté aux fonctions cadres "
                    "ou dirigeantes."
                )

            if (
                remote_requested
                and capability.remote_jobs
            ):
                score += self.REMOTE_BONUS
                reasons.append(
                    "Le provider propose du télétravail."
                )

            preliminary.append(
                {
                    "capability": capability,
                    "provider_id": provider_id,
                    "recommended": recommended,
                    "available": available,
                    "score": score,
                    "reasons": reasons,
                }
            )

        for provider_id in sorted(
            available_ids - known_ids
        ):
            preliminary.append(
                {
                    "capability": (
                        ProviderCapability(
                            provider_id=provider_id,
                            label=provider_id,
                            implemented=True,
                            priority=100,
                        )
                    ),
                    "provider_id": provider_id,
                    "recommended": (
                        provider_id
                        in recommended_ids
                    ),
                    "available": True,
                    "score": (
                        self.AVAILABLE_BONUS
                        + self.IMPLEMENTED_BONUS
                    ),
                    "reasons": [
                        "Provider disponible mais absent "
                        "du catalogue de capacités."
                    ],
                }
            )

        operational_recommended = [
            item
            for item in preliminary
            if item["recommended"]
            and item["available"]
            and item["capability"].implemented
        ]

        fallback_ids: set[str] = set()

        if operational_recommended:
            selected_ids = {
                item["provider_id"]
                for item
                in operational_recommended
            }

        else:
            operational = [
                item
                for item in preliminary
                if item["available"]
                and item["capability"].implemented
            ]

            operational.sort(
                key=lambda item: (
                    item["score"],
                    -item["capability"].priority,
                ),
                reverse=True,
            )

            selected_ids = {
                item["provider_id"]
                for item in operational
            }

            fallback_ids = set(
                selected_ids
            )

        items = [
            ProviderSelectionItem(
                provider_id=(
                    item["provider_id"]
                ),
                label=(
                    item["capability"].label
                ),
                recommended=(
                    item["recommended"]
                ),
                implemented=(
                    item["capability"]
                    .implemented
                ),
                available=(
                    item["available"]
                ),
                selected=(
                    item["provider_id"]
                    in selected_ids
                ),
                fallback=(
                    item["provider_id"]
                    in fallback_ids
                ),
                score=int(
                    item["score"]
                ),
                reasons=tuple(
                    item["reasons"]
                ),
            )
            for item in preliminary
        ]

        items.sort(
            key=lambda item: (
                not item.selected,
                not item.recommended,
                -item.score,
                item.label.casefold(),
            )
        )

        return ProviderSelectionResult(
            items=items
        )

    @staticmethod
    def canonical_provider_id(
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
            "apec": "apec",
            "welcome": (
                "welcometothejungle"
            ),
            "welcometothejungle": (
                "welcometothejungle"
            ),
            "linkedinprovider": "linkedin",
            "linkedin": "linkedin",
        }

        return aliases.get(
            normalized,
            normalized,
        )

    @staticmethod
    def _role_categories(
        role_id: str | None,
    ) -> tuple[str, ...]:
        if not role_id:
            return ()

        for role in JOB_ROLE_CATALOG:
            if role.role_id == role_id:
                return role.categories

        return ()