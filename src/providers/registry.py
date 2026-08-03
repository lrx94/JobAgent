from __future__ import annotations

from collections.abc import Iterable, Iterator
from typing import Any


class ProviderRegistry:
    """Registre des fournisseurs d'offres d'emploi."""

    def __init__(
        self,
        providers: Iterable[Any] | None = None,
    ) -> None:
        self._providers: list[Any] = []

        for provider in providers or []:
            self.register(provider)

    def register(self, provider: Any) -> None:
        """Enregistre un provider valide sans doublon."""

        if provider is None:
            raise ValueError(
                "Le provider ne peut pas être None."
            )

        if not callable(getattr(provider, "search", None)):
            raise TypeError(
                "Le provider doit exposer une méthode search()."
            )

        provider_key = self._provider_key(provider)

        if any(
            self._provider_key(existing) == provider_key
            for existing in self._providers
        ):
            return

        self._providers.append(provider)

    def unregister(self, provider: Any) -> bool:
        """Supprime un provider du registre."""

        provider_key = self._provider_key(provider)

        for index, existing in enumerate(self._providers):
            if self._provider_key(existing) == provider_key:
                del self._providers[index]
                return True

        return False

    def clear(self) -> None:
        """Supprime tous les providers enregistrés."""

        self._providers.clear()

    def all(self) -> list[Any]:
        """Retourne une copie de la liste des providers."""

        return list(self._providers)

    def names(self) -> list[str]:
        """Retourne les noms des providers enregistrés."""

        return [
            self.provider_name(provider)
            for provider in self._providers
        ]

    def get(self, provider_name: str) -> Any | None:
        """Recherche un provider par son nom."""

        normalized_name = str(
            provider_name or ""
        ).strip().casefold()

        for provider in self._providers:
            if (
                self.provider_name(provider).casefold()
                == normalized_name
            ):
                return provider

        return None

    def __len__(self) -> int:
        return len(self._providers)

    def __iter__(self) -> Iterator[Any]:
        return iter(self._providers)

    @staticmethod
    def provider_name(provider: Any) -> str:
        """Retourne un nom lisible pour un provider."""

        explicit_name = getattr(provider, "name", None)

        if explicit_name:
            cleaned_name = str(explicit_name).strip()

            if cleaned_name:
                return cleaned_name

        return provider.__class__.__name__

    @classmethod
    def _provider_key(
        cls,
        provider: Any,
    ) -> tuple[type, str]:
        return (
            provider.__class__,
            cls.provider_name(provider).casefold(),
        )