from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class ProviderCapability:
    """
    Décrit les caractéristiques fonctionnelles d'un provider.

    Cette structure ne signifie pas nécessairement que le provider
    est déjà implémenté ou configuré dans JobAgent.
    """

    provider_id: str
    label: str

    implemented: bool = False
    requires_configuration: bool = False

    supported_role_ids: tuple[str, ...] = ()
    supported_categories: tuple[str, ...] = ()

    international: bool = False
    executive_roles: bool = False
    remote_jobs: bool = False

    priority: int = 100

    def supports_role(
        self,
        role_id: str | None,
    ) -> bool:
        if not role_id:
            return True

        if not self.supported_role_ids:
            return True

        normalized_role_id = str(
            role_id
        ).strip().casefold()

        return any(
            normalized_role_id
            == supported_role.casefold()
            for supported_role
            in self.supported_role_ids
        )

    def supports_any_category(
        self,
        categories: (
            list[str]
            | tuple[str, ...]
            | None
        ),
    ) -> bool:
        if not categories:
            return True

        if not self.supported_categories:
            return True

        normalized_categories = {
            str(category).strip().casefold()
            for category in categories
            if str(category).strip()
        }

        supported = {
            category.casefold()
            for category
            in self.supported_categories
        }

        return bool(
            normalized_categories
            & supported
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "provider_id": self.provider_id,
            "label": self.label,
            "implemented": self.implemented,
            "requires_configuration": (
                self.requires_configuration
            ),
            "supported_role_ids": list(
                self.supported_role_ids
            ),
            "supported_categories": list(
                self.supported_categories
            ),
            "international": self.international,
            "executive_roles": self.executive_roles,
            "remote_jobs": self.remote_jobs,
            "priority": self.priority,
        }


PROVIDER_CAPABILITIES: tuple[
    ProviderCapability,
    ...,
] = (
    ProviderCapability(
        provider_id="remoteok",
        label="RemoteOK",
        implemented=True,
        requires_configuration=False,
        supported_role_ids=(
            "cto",
            "data_engineer",
            "cloud_architect",
            "it_project_director",
        ),
        supported_categories=(
            "technology",
            "engineering",
            "data",
            "cloud",
            "remote",
        ),
        international=True,
        executive_roles=False,
        remote_jobs=True,
        priority=40,
    ),
    ProviderCapability(
        provider_id="francetravail",
        label="France Travail",
        implemented=True,
        requires_configuration=True,
        supported_categories=(
            "technology",
            "engineering",
            "management",
            "finance",
            "executive",
            "project_management",
            "program_management",
            "transformation",
        ),
        international=False,
        executive_roles=True,
        remote_jobs=True,
        priority=10,
    ),
    ProviderCapability(
        provider_id="apec",
        label="APEC",
        implemented=False,
        requires_configuration=False,
        supported_categories=(
            "technology",
            "management",
            "finance",
            "executive",
            "project_management",
            "program_management",
            "transformation",
            "governance",
        ),
        international=False,
        executive_roles=True,
        remote_jobs=True,
        priority=15,
    ),
    ProviderCapability(
        provider_id="welcometothejungle",
        label="Welcome to the Jungle",
        implemented=False,
        requires_configuration=False,
        supported_categories=(
            "technology",
            "engineering",
            "data",
            "product",
            "finance",
            "management",
            "project_management",
        ),
        international=False,
        executive_roles=False,
        remote_jobs=True,
        priority=20,
    ),
    ProviderCapability(
        provider_id="linkedin",
        label="LinkedIn",
        implemented=False,
        requires_configuration=True,
        supported_categories=(),
        international=True,
        executive_roles=True,
        remote_jobs=True,
        priority=25,
    ),
)