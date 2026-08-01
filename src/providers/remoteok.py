from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from html import unescape
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from src.domain import Job
from src.providers.base import JobProvider
from src.search_request import SearchRequest


class RemoteOKProvider(JobProvider):
    """
    Provider d'offres d'emploi provenant du flux JSON RemoteOK.

    Responsabilités du provider :
    - télécharger les offres RemoteOK ;
    - convertir les données en objets Job ;
    - supprimer les doublons ;
    - appliquer les filtres techniques compatibles avec RemoteOK ;
    - appliquer la pagination.

    Le provider ne filtre pas les offres selon les compétences du profil.
    Le matching des compétences est effectué ensuite par le moteur
    de matching de JobAgent.
    """

    API_URL = "https://remoteok.com/api"
    SOURCE_NAME = "RemoteOK"

    def __init__(
        self,
        timeout: float = 20.0,
        user_agent: str = "JobAgent/3.10",
    ) -> None:
        self.timeout = max(float(timeout), 1.0)
        self.user_agent = str(user_agent).strip() or "JobAgent/3.10"

    @property
    def name(self) -> str:
        return self.SOURCE_NAME

    def search(
        self,
        request: SearchRequest,
    ) -> list[Job]:
        """
        Télécharge les offres RemoteOK, les normalise et applique
        les critères techniques compatibles avec le fournisseur.
        """

        if not isinstance(request, SearchRequest):
            raise TypeError(
                "request doit être une instance de SearchRequest."
            )

        payload = self._fetch_payload()

        jobs: list[Job] = []
        seen_identities: set[str] = set()

        for item in payload:
            job = self._build_job(item)

            if job is None:
                continue

            if not self._matches_request(job, request):
                continue

            identity = job.identity.casefold()

            if identity in seen_identities:
                continue

            seen_identities.add(identity)
            jobs.append(job)

        jobs.sort(
            key=lambda job: (
                job.published_at is not None,
                job.published_at or datetime.min,
            ),
            reverse=True,
        )

        return self._paginate(jobs, request)

    def _fetch_payload(self) -> list[dict[str, Any]]:
        """
        Télécharge et valide le flux JSON RemoteOK.
        """

        request = Request(
            self.API_URL,
            headers={
                "User-Agent": self.user_agent,
                "Accept": "application/json",
            },
            method="GET",
        )

        try:
            with urlopen(
                request,
                timeout=self.timeout,
            ) as response:
                status = getattr(response, "status", 200)

                if status != 200:
                    raise RuntimeError(
                        "RemoteOK a retourné le statut HTTP "
                        f"{status}."
                    )

                body = response.read()

        except HTTPError as error:
            raise RuntimeError(
                "Erreur HTTP RemoteOK : "
                f"{error.code} {error.reason}"
            ) from error

        except URLError as error:
            raise RuntimeError(
                "Impossible de joindre RemoteOK : "
                f"{error.reason}"
            ) from error

        except TimeoutError as error:
            raise RuntimeError(
                "Le délai d'attente RemoteOK a été dépassé."
            ) from error

        try:
            decoded = body.decode("utf-8")
            payload = json.loads(decoded)

        except (UnicodeDecodeError, json.JSONDecodeError) as error:
            raise RuntimeError(
                "La réponse RemoteOK n'est pas un JSON valide."
            ) from error

        if not isinstance(payload, list):
            raise RuntimeError(
                "Le format de réponse RemoteOK est inattendu."
            )

        return [
            item
            for item in payload
            if isinstance(item, dict)
        ]

    def _build_job(
        self,
        item: dict[str, Any],
    ) -> Job | None:
        """
        Transforme une entrée JSON RemoteOK en objet Job.
        """

        external_id = self._clean_text(
            item.get("id")
        )

        title = self._clean_text(
            item.get("position")
            or item.get("title")
        )

        if not external_id or not title:
            return None

        company = self._clean_text(
            item.get("company")
        ) or "Entreprise inconnue"

        location = self._clean_text(
            item.get("location")
        ) or "Remote"

        description = self._clean_html(
            item.get("description")
        )

        url = self._clean_text(
            item.get("url")
            or item.get("apply_url")
        )

        if url and url.startswith("/"):
            url = f"https://remoteok.com{url}"

        if not url:
            url = (
                "https://remoteok.com/remote-jobs/"
                f"{external_id}"
            )

        skills = self._normalize_tags(
            item.get("tags")
        )

        salary_min = self._parse_integer(
            item.get("salary_min")
        )

        salary_max = self._parse_integer(
            item.get("salary_max")
        )

        published_at = self._parse_datetime(
            item
        )

        return Job(
            title=title,
            company=company,
            location=location,
            description=description,
            source=self.SOURCE_NAME,
            url=url,
            external_id=external_id,
            salary_min=salary_min,
            salary_max=salary_max,
            salary_currency="USD",
            salary_period=(
                "year"
                if salary_min is not None
                or salary_max is not None
                else "unknown"
            ),
            remote_type="remote",
            published_at=published_at,
            skills=skills,
            raw_data=dict(item),
            remote=True,
        )

    def _matches_request(
        self,
        job: Job,
        request: SearchRequest,
    ) -> bool:
        """
        Applique uniquement les filtres techniques.

        Les mots-clés et compétences ne sont pas utilisés ici.
        Leur évaluation est déléguée au moteur de matching.
        """

        if request.locations:
            location_text = job.location.casefold()

            location_matches = any(
                location.casefold() in location_text
                or location_text in location.casefold()
                for location in request.locations
            )

            worldwide_terms = {
                "remote",
                "worldwide",
                "anywhere",
                "global",
            }

            is_worldwide = any(
                term in location_text
                for term in worldwide_terms
            )

            if not location_matches and not is_worldwide:
                return False

        if request.salary_min is not None:
            available_salary = (
                job.salary_max
                if job.salary_max is not None
                else job.salary_min
            )

            if (
                available_salary is not None
                and available_salary < request.salary_min
            ):
                return False

        if (
            request.published_within_days is not None
            and job.published_at is not None
        ):
            cutoff = datetime.now(
                timezone.utc
            ) - timedelta(
                days=request.published_within_days
            )

            published_at = job.published_at

            if published_at.tzinfo is None:
                published_at = published_at.replace(
                    tzinfo=timezone.utc
                )

            if published_at < cutoff:
                return False

        return True

    @staticmethod
    def _paginate(
        jobs: list[Job],
        request: SearchRequest,
    ) -> list[Job]:
        """
        Applique la pagination demandée.
        """

        start = (request.page - 1) * request.page_size
        end = start + request.page_size

        return jobs[start:end]

    @classmethod
    def _parse_datetime(
        cls,
        item: dict[str, Any],
    ) -> datetime | None:
        """
        Convertit la date RemoteOK en datetime.
        """

        epoch = item.get("epoch")

        if epoch not in {None, ""}:
            try:
                return datetime.fromtimestamp(
                    float(epoch),
                    tz=timezone.utc,
                )

            except (TypeError, ValueError, OSError):
                pass

        date_value = cls._clean_text(
            item.get("date")
        )

        if not date_value:
            return None

        normalized = date_value.replace(
            "Z",
            "+00:00",
        )

        try:
            parsed = datetime.fromisoformat(
                normalized
            )

        except ValueError:
            return None

        if parsed.tzinfo is None:
            parsed = parsed.replace(
                tzinfo=timezone.utc
            )

        return parsed

    @staticmethod
    def _normalize_tags(
        value: Any,
    ) -> list[str]:
        """
        Nettoie et déduplique les tags RemoteOK.
        """

        if not isinstance(value, (list, tuple)):
            return []

        normalized: list[str] = []
        seen: set[str] = set()

        for item in value:
            tag = str(item or "").strip()

            if not tag:
                continue

            key = tag.casefold()

            if key in seen:
                continue

            seen.add(key)
            normalized.append(tag)

        return normalized

    @staticmethod
    def _parse_integer(
        value: Any,
    ) -> int | None:
        """
        Convertit une valeur numérique en entier positif.
        """

        if value in {None, ""}:
            return None

        try:
            parsed = int(float(value))

        except (TypeError, ValueError):
            return None

        return parsed if parsed >= 0 else None

    @staticmethod
    def _clean_text(
        value: Any,
    ) -> str:
        """
        Convertit une valeur en texte nettoyé.
        """

        return str(value or "").strip()

    @classmethod
    def _clean_html(
        cls,
        value: Any,
    ) -> str:
        """
        Supprime les balises HTML principales d'une description.
        """

        text = cls._clean_text(
            value
        )

        if not text:
            return ""

        replacements = {
            "<br>": "\n",
            "<br/>": "\n",
            "<br />": "\n",
            "</p>": "\n",
            "</li>": "\n",
        }

        for source, replacement in replacements.items():
            text = text.replace(
                source,
                replacement,
            )

        inside_tag = False
        result: list[str] = []

        for character in text:
            if character == "<":
                inside_tag = True
                continue

            if character == ">":
                inside_tag = False
                continue

            if not inside_tag:
                result.append(character)

        cleaned = unescape(
            "".join(result)
        )

        return "\n".join(
            line.strip()
            for line in cleaned.splitlines()
            if line.strip()
        )