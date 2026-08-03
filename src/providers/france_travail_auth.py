from __future__ import annotations

import json
import time
from dataclasses import dataclass
from typing import Any, Callable
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from src.providers.france_travail_config import (
    FranceTravailConfig,
)


@dataclass(frozen=True, slots=True)
class AccessToken:
    value: str
    expires_at: float

    def is_valid(
        self,
        safety_margin: int = 30,
    ) -> bool:
        return bool(
            self.value
            and time.time()
            < self.expires_at - safety_margin
        )


class FranceTravailAuthClient:
    """
    Client OAuth2 utilisant le flux client_credentials.

    Le jeton est conservé en mémoire jusqu'à son expiration.
    """

    def __init__(
        self,
        config: FranceTravailConfig,
        opener: Callable[..., Any] = urlopen,
    ) -> None:
        self.config = config
        self.opener = opener
        self._token: AccessToken | None = None

    def access_token(
        self,
        force_refresh: bool = False,
    ) -> str:
        if (
            not force_refresh
            and self._token is not None
            and self._token.is_valid()
        ):
            return self._token.value

        self.config.require_credentials()

        payload = urlencode(
            {
                "grant_type": (
                    "client_credentials"
                ),
                "client_id": (
                    self.config.client_id
                ),
                "client_secret": (
                    self.config.client_secret
                ),
                "scope": self.config.scope,
            }
        ).encode("utf-8")

        request = Request(
            self.config.token_url,
            data=payload,
            headers={
                "Accept": "application/json",
                "Content-Type": (
                    "application/"
                    "x-www-form-urlencoded"
                ),
                "User-Agent": (
                    self.config.user_agent
                ),
            },
            method="POST",
        )

        response_data = self._execute(
            request
        )

        token_value = str(
            response_data.get(
                "access_token",
                "",
            )
            or ""
        ).strip()

        if not token_value:
            raise RuntimeError(
                "France Travail n'a pas retourné "
                "de jeton d'accès."
            )

        expires_in = self._positive_integer(
            response_data.get(
                "expires_in",
                300,
            ),
            default=300,
        )

        self._token = AccessToken(
            value=token_value,
            expires_at=(
                time.time()
                + expires_in
            ),
        )

        return token_value

    def invalidate(self) -> None:
        self._token = None

    def _execute(
        self,
        request: Request,
    ) -> dict[str, Any]:
        try:
            with self.opener(
                request,
                timeout=self.config.timeout,
            ) as response:
                status = getattr(
                    response,
                    "status",
                    200,
                )

                body = response.read()

        except HTTPError as error:
            raise RuntimeError(
                "Erreur OAuth France Travail : "
                f"HTTP {error.code}."
            ) from error

        except URLError as error:
            raise RuntimeError(
                "Connexion OAuth France Travail "
                f"impossible : {error.reason}"
            ) from error

        except TimeoutError as error:
            raise RuntimeError(
                "Le délai OAuth France Travail "
                "a été dépassé."
            ) from error

        if not 200 <= status < 300:
            raise RuntimeError(
                "France Travail a retourné le "
                f"statut OAuth HTTP {status}."
            )

        try:
            decoded = body.decode(
                "utf-8"
            )
            data = json.loads(decoded)
        except (
            UnicodeDecodeError,
            json.JSONDecodeError,
        ) as error:
            raise RuntimeError(
                "La réponse OAuth France Travail "
                "n'est pas un JSON valide."
            ) from error

        if not isinstance(data, dict):
            raise RuntimeError(
                "Le format de la réponse OAuth "
                "France Travail est invalide."
            )

        return data

    @staticmethod
    def _positive_integer(
        value: Any,
        default: int,
    ) -> int:
        try:
            normalized = int(
                float(value)
            )
        except (
            TypeError,
            ValueError,
        ):
            return default

        return (
            normalized
            if normalized > 0
            else default
        )