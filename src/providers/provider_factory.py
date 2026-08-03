from __future__ import annotations

from src.providers.base import JobProvider
from src.providers.france_travail import (
    FranceTravailProvider,
)
from src.providers.france_travail_config import (
    FranceTravailConfig,
)
from src.providers.remoteok import RemoteOKProvider


def build_default_providers(
    include_unconfigured: bool = False,
) -> list[JobProvider]:
    """
    Construit les providers réellement exécutables.

    RemoteOK est toujours disponible.

    France Travail est ajouté uniquement lorsque ses identifiants
    sont configurés, sauf demande explicite de l'inclure.
    """

    providers: list[JobProvider] = [
        RemoteOKProvider(),
    ]

    config = (
        FranceTravailConfig
        .from_environment()
    )

    if (
        config.configured
        or include_unconfigured
    ):
        providers.append(
            FranceTravailProvider(
                config=config
            )
        )

    return providers