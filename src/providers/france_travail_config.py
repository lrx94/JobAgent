from __future__ import annotations

import os
from dataclasses import dataclass
from dotenv import load_dotenv


load_dotenv()

DEFAULT_TOKEN_URL = (
    "https://entreprise.francetravail.fr/"
    "connexion/oauth2/access_token"
    "?realm=%2Fpartenaire"
)

DEFAULT_SEARCH_URL = (
    "https://api.francetravail.io/"
    "partenaire/offresdemploi/v2/offres/search"
)

DEFAULT_SCOPE = (
    "api_offresdemploiv2 o2dsoffre"
)

DEFAULT_TIMEOUT = 20.0
DEFAULT_USER_AGENT = "JobAgent/3.12.1"


@dataclass(frozen=True, slots=True)
class FranceTravailConfig:
    """
    Configuration réseau et OAuth du provider France Travail.

    Les valeurs sensibles sont exclusivement chargées depuis
    les variables d'environnement.
    """

    client_id: str = ""
    client_secret: str = ""

    token_url: str = DEFAULT_TOKEN_URL
    search_url: str = DEFAULT_SEARCH_URL
    scope: str = DEFAULT_SCOPE

    timeout: float = DEFAULT_TIMEOUT
    user_agent: str = DEFAULT_USER_AGENT

    @property
    def configured(self) -> bool:
        return bool(
            self.client_id.strip()
            and self.client_secret.strip()
        )

    @classmethod
    def from_environment(
        cls,
    ) -> FranceTravailConfig:
        return cls(
            client_id=os.getenv(
                "FRANCE_TRAVAIL_CLIENT_ID",
                "",
            ).strip(),
            client_secret=os.getenv(
                "FRANCE_TRAVAIL_CLIENT_SECRET",
                "",
            ).strip(),
            token_url=os.getenv(
                "FRANCE_TRAVAIL_TOKEN_URL",
                DEFAULT_TOKEN_URL,
            ).strip()
            or DEFAULT_TOKEN_URL,
            search_url=os.getenv(
                "FRANCE_TRAVAIL_SEARCH_URL",
                DEFAULT_SEARCH_URL,
            ).strip()
            or DEFAULT_SEARCH_URL,
            scope=os.getenv(
                "FRANCE_TRAVAIL_SCOPE",
                DEFAULT_SCOPE,
            ).strip()
            or DEFAULT_SCOPE,
            timeout=cls._environment_float(
                "FRANCE_TRAVAIL_TIMEOUT",
                DEFAULT_TIMEOUT,
            ),
            user_agent=os.getenv(
                "FRANCE_TRAVAIL_USER_AGENT",
                DEFAULT_USER_AGENT,
            ).strip()
            or DEFAULT_USER_AGENT,
        )

    def require_credentials(self) -> None:
        if self.configured:
            return

        raise RuntimeError(
            "France Travail n'est pas configuré. "
            "Définissez FRANCE_TRAVAIL_CLIENT_ID et "
            "FRANCE_TRAVAIL_CLIENT_SECRET."
        )

    @staticmethod
    def _environment_float(
        variable_name: str,
        default: float,
    ) -> float:
        raw_value = os.getenv(
            variable_name,
            "",
        ).strip()

        if not raw_value:
            return default

        try:
            value = float(raw_value)
        except ValueError:
            return default

        return max(
            value,
            1.0,
        )