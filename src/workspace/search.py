from __future__ import annotations

from dataclasses import dataclass
from typing import Any, MutableMapping

from src.career.search_workflow import (
    CareerSearchResult,
    CareerSearchWorkflow,
)
from src.career.user_cv_profile_service import (
    UserCVProfileService,
)
from src.profile import Profile
from src.workspace.exceptions import (
    WorkspaceError,
)
from src.workspace.analysis_service import (
    WorkspaceAnalysisService,
)

class WorkspaceSearchError(
    WorkspaceError
):
    """
    Une recherche depuis le Career Workspace
    n'a pas pu être exécutée.
    """


@dataclass(frozen=True, slots=True)
class WorkspaceSearchContext:
    """
    Profil métier prêt à être transmis au workflow
    de recherche existant.
    """

    profile_id: str
    profile: Profile


class WorkspaceSearchService:
    """
    Adapte un profil utilisateur enregistré au
    CareerSearchWorkflow déjà présent dans JobAgent.

    Ce service ne contient ni provider, ni matching,
    ni logique de collecte supplémentaire.
    """

    def __init__(
        self,
        profile_service: UserCVProfileService,
        workflow: CareerSearchWorkflow | None = None,
        analysis_service: (
            WorkspaceAnalysisService | None
        ) = None,
    ) -> None:
        if not isinstance(
            profile_service,
            UserCVProfileService,
        ):
            raise TypeError(
                "profile_service doit être un "
                "UserCVProfileService."
            )

        if workflow is not None:
            search_method = getattr(
                workflow,
                "search",
                None,
            )

            if not callable(search_method):
                raise TypeError(
                    "workflow doit exposer "
                    "une méthode search()."
                )

        self.profile_service = profile_service
        self.workflow = (
            workflow
            or CareerSearchWorkflow()
        )
        
        if (
            analysis_service is not None
            and not isinstance(
                analysis_service,
                WorkspaceAnalysisService,
            )
        ):
            raise TypeError(
                "analysis_service doit être un "
                "WorkspaceAnalysisService."
            )
        
        self.analysis_service = (
            analysis_service
        )
    @property
    def user_id(self) -> str:
        return self.profile_service.user_id

    def build_context(
        self,
        profile_id: str,
    ) -> WorkspaceSearchContext:
        normalized_profile_id = str(
            profile_id or ""
        ).strip()

        if not normalized_profile_id:
            raise WorkspaceSearchError(
                "Le profile_id est obligatoire."
            )

        available_profiles = set(
            self.profile_service.list_profiles()
        )

        if (
            normalized_profile_id
            not in available_profiles
        ):
            raise WorkspaceSearchError(
                "Le profil demandé n'existe pas "
                "dans l'espace utilisateur."
            )

        try:
            config = (
                self.profile_service
                .load_profile_config(
                    normalized_profile_id
                )
            )
        except Exception as error:
            raise WorkspaceSearchError(
                "Impossible de charger la "
                "configuration du profil."
            ) from error

        if not isinstance(config, dict):
            raise WorkspaceSearchError(
                "La configuration du profil "
                "est invalide."
            )

        profile = self._build_profile(
            profile_id=normalized_profile_id,
            config=config,
        )

        return WorkspaceSearchContext(
            profile_id=normalized_profile_id,
            profile=profile,
        )

    def search(
        self,
        profile_id: str,
    ) -> CareerSearchResult:
        context = self.build_context(
            profile_id
        )

        try:
            result = self.workflow.search(
                profile=context.profile,
                selected_role=None,
            )
        except Exception as error:
            raise WorkspaceSearchError(
                "La recherche d'offres a échoué."
            ) from error

        if self.analysis_service is None:
            return result

        jobs_to_enrich = self._result_jobs(
            result
        )

        try:
            (
                self.analysis_service
                .enrich_profile_jobs(
                    profile_id=(
                        context.profile_id
                    ),
                    jobs=jobs_to_enrich,
                )
            )
        except Exception:
            # L'observabilité structurée ne doit jamais
            # empêcher la recherche historique.
            pass

        return result

    @staticmethod
    def _result_jobs(
        result: CareerSearchResult,
    ) -> tuple:
        """
        Récupère l'échantillon le plus large disponible.

        `all_jobs` est prioritaire afin que les offres
        filtrées restent également observables.
        """

        all_jobs = getattr(
            result,
            "all_jobs",
            None,
        )

        if all_jobs:
            return tuple(all_jobs)

        jobs = getattr(
            result,
            "jobs",
            None,
        )

        return tuple(
            jobs or ()
        )

    @staticmethod
    def _build_profile(
        profile_id: str,
        config: dict[str, Any],
    ) -> Profile:
        name = str(
            config.get("name")
            or config.get("title")
            or profile_id
        ).strip()

        keywords = (
            WorkspaceSearchService
            ._normalize_string_list(
                config.get(
                    "keywords",
                    [],
                )
            )
        )

        locations = (
            WorkspaceSearchService
            ._normalize_string_list(
                config.get(
                    "locations",
                    [],
                )
            )
        )

        try:
            salary_min = int(
                config.get(
                    "salary_min",
                    0,
                )
                or 0
            )
        except (
            TypeError,
            ValueError,
        ):
            salary_min = 0

        remote = bool(
            config.get(
                "remote",
                False,
            )
        )

        return Profile(
            name=name,
            keywords=keywords,
            locations=locations,
            salary_min=max(
                0,
                salary_min,
            ),
            remote=remote,
        )

    @staticmethod
    def _normalize_string_list(
        values: Any,
    ) -> list[str]:
        if isinstance(values, str):
            source = values.split(",")
        elif isinstance(
            values,
            (
                list,
                tuple,
                set,
            ),
        ):
            source = values
        else:
            source = []

        result: list[str] = []
        seen: set[str] = set()

        for value in source:
            cleaned = str(
                value or ""
            ).strip()

            if not cleaned:
                continue

            identity = cleaned.casefold()

            if identity in seen:
                continue

            seen.add(identity)
            result.append(cleaned)

        return result


class WorkspaceSearchCache:
    """
    Cache de résultats par profil.

    Le stockage concret peut être st.session_state
    ou un simple dictionnaire pendant les tests.
    """

    STATE_KEY = (
        "career_workspace_search_results"
    )

    @classmethod
    def get_store(
        cls,
        session_state: MutableMapping[
            str,
            Any,
        ],
    ) -> dict[str, CareerSearchResult]:
        current = session_state.get(
            cls.STATE_KEY
        )

        if not isinstance(
            current,
            dict,
        ):
            current = {}

            session_state[
                cls.STATE_KEY
            ] = current

        return current

    @classmethod
    def get(
        cls,
        session_state: MutableMapping[
            str,
            Any,
        ],
        profile_id: str,
    ) -> CareerSearchResult | None:
        return cls.get_store(
            session_state
        ).get(
            str(profile_id)
        )

    @classmethod
    def set(
        cls,
        session_state: MutableMapping[
            str,
            Any,
        ],
        profile_id: str,
        result: CareerSearchResult,
    ) -> None:
        if not isinstance(
            result,
            CareerSearchResult,
        ):
            raise TypeError(
                "result doit être un "
                "CareerSearchResult."
            )

        cls.get_store(
            session_state
        )[
            str(profile_id)
        ] = result

    @classmethod
    def clear(
        cls,
        session_state: MutableMapping[
            str,
            Any,
        ],
        profile_id: str,
    ) -> None:
        cls.get_store(
            session_state
        ).pop(
            str(profile_id),
            None,
        )

    @classmethod
    def clear_all(
        cls,
        session_state: MutableMapping[
            str,
            Any,
        ],
    ) -> None:
        session_state[
            cls.STATE_KEY
        ] = {}