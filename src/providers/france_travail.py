from __future__ import annotations

import json
from typing import Any, Callable
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from src.domain import Job
from src.providers.base import JobProvider
from src.providers.france_travail_auth import (
    FranceTravailAuthClient,
)
from src.providers.france_travail_config import (
    FranceTravailConfig,
)
from src.providers.france_travail_mapper import (
    FranceTravailJobMapper,
)
from src.search_request import SearchRequest


class FranceTravailProvider(JobProvider):
    """
    Provider officiel France Travail.

    Les mots-clés servent uniquement à construire la requête
    distante. Le matching final reste sous la responsabilité
    du MatchingEngine.
    """

    SOURCE_NAME = "France Travail"

    def __init__(
        self,
        config: FranceTravailConfig | None = None,
        auth_client: (
            FranceTravailAuthClient | None
        ) = None,
        mapper: (
            FranceTravailJobMapper | None
        ) = None,
        opener: Callable[..., Any] = urlopen,
    ) -> None:
        self.config = (
            config
            or FranceTravailConfig
            .from_environment()
        )

        self.opener = opener

        self.auth_client = (
            auth_client
            or FranceTravailAuthClient(
                config=self.config,
                opener=opener,
            )
        )

        self.mapper = (
            mapper
            or FranceTravailJobMapper()
        )

    @property
    def name(self) -> str:
        return self.SOURCE_NAME

    @property
    def configured(self) -> bool:
        return self.config.configured

    def search(
        self,
        request: SearchRequest,
    ) -> list[Job]:
        if not isinstance(
            request,
            SearchRequest,
        ):
            raise TypeError(
                "request doit être une instance "
                "de SearchRequest."
            )

        self.config.require_credentials()

        token = (
            self.auth_client.access_token()
        )

        parameters = self._parameters(
            request
        )

        search_url = self.config.search_url

        if parameters:
            search_url += (
                "?"
                + urlencode(parameters)
            )

        start = (
            request.page - 1
        ) * request.page_size

        end = (
            start
            + request.page_size
            - 1
        )

        payload = self._fetch(
            url=search_url,
            token=token,
            start=start,
            end=end,
        )

        results = payload.get(
            "resultats",
            [],
        )

        if not isinstance(results, list):
            return []

        jobs = self.mapper.map_many(
            [
                item
                for item in results
                if isinstance(item, dict)
            ]
        )

        seen: set[str] = set()
        unique_jobs: list[Job] = []

        for job in jobs:
            identity = (
                job.identity.casefold()
            )

            if identity in seen:
                continue

            seen.add(identity)
            unique_jobs.append(job)

        return unique_jobs

    @staticmethod
    def _parameters(
        request: SearchRequest,
    ) -> dict[str, str]:
        parameters: dict[str, str] = {}

        if request.primary_keyword:
            parameters["motsCles"] = (
                request.primary_keyword
            )

        if request.primary_location:
            location = (
                request.primary_location
            )

            if (
                location.casefold()
                not in {
                    "remote",
                    "télétravail",
                }
            ):
                parameters[
                    "commune"
                ] = location

        if request.contract_types:
            parameters[
                "typeContrat"
            ] = ",".join(
                request.contract_types
            )

        return parameters

    def _fetch(
        self,
        url: str,
        token: str,
        start: int,
        end: int,
    ) -> dict[str, Any]:
        request = Request(
            url,
            headers={
                "Accept": (
                    "application/json"
                ),
                "Authorization": (
                    f"Bearer {token}"
                ),
                "Range": (
                    f"offres={start}-{end}"
                ),
                "User-Agent": (
                    self.config.user_agent
                ),
            },
            method="GET",
        )

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
            if error.code == 401:
                self.auth_client.invalidate()

            raise RuntimeError(
                "Erreur API France Travail : "
                f"HTTP {error.code}."
            ) from error

        except URLError as error:
            raise RuntimeError(
                "Connexion France Travail "
                f"impossible : {error.reason}"
            ) from error

        except TimeoutError as error:
            raise RuntimeError(
                "Le délai France Travail "
                "a été dépassé."
            ) from error

        if not 200 <= status < 300:
            raise RuntimeError(
                "France Travail a retourné "
                f"HTTP {status}."
            )

        try:
            data = json.loads(
                body.decode("utf-8")
            )
        except (
            UnicodeDecodeError,
            json.JSONDecodeError,
        ) as error:
            raise RuntimeError(
                "La réponse France Travail "
                "n'est pas un JSON valide."
            ) from error

        if not isinstance(data, dict):
            raise RuntimeError(
                "Le format France Travail "
                "est invalide."
            )

        return data