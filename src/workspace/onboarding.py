from __future__ import annotations

from dataclasses import dataclass
from typing import BinaryIO

from src.profile import Profile
from src.career.user_cv_profile_service import (
    UserCVProfileService,
)
from src.cvs.exceptions import CVError
from src.cvs.models import CVDocument
from src.cvs.profile_cv_models import (
    ProfileCVAssociation,
)
from src.cvs.profile_cv_service import (
    ProfileCVService,
)
from src.cvs.results import (
    CVAnalysisResult,
)
from src.cvs.service import (
    CVService,
)
from src.workspace.exceptions import (
    WorkspaceError,
)


class WorkspaceOnboardingError(
    WorkspaceError
):
    """
    Le parcours de création profil/CV n'a pas pu
    être terminé.
    """


@dataclass(
    frozen=True,
    slots=True,
)
class WorkspaceOnboardingResult:
    """
    Résultat du parcours d'onboarding.

    Le profil est créé, le CV est importé, puis le CV
    est associé au profil comme CV principal.
    """

    profile_id: str
    document: CVDocument
    association: ProfileCVAssociation
    analysis: CVAnalysisResult | None
    duplicate_reused: bool
    warnings: tuple[str, ...] = ()

    @property
    def cv_id(self) -> str:
        return self.document.cv_id

    @property
    def is_primary(self) -> bool:
        return self.association.is_primary


class WorkspaceOnboardingService:
    """
    Orchestre les services existants sans dupliquer
    leur logique métier.

    Ordre du parcours :

    1. importer le CV ;
    2. créer le profil utilisateur ;
    3. associer le CV comme principal ;
    4. retourner un résultat exploitable par l'UI.
    """

    def __init__(
        self,
        profile_service: UserCVProfileService,
        cv_service: CVService,
        association_service: ProfileCVService,
    ) -> None:
        if not isinstance(
            profile_service,
            UserCVProfileService,
        ):
            raise TypeError(
                "profile_service doit être un "
                "UserCVProfileService."
            )

        if not isinstance(
            cv_service,
            CVService,
        ):
            raise TypeError(
                "cv_service doit être un CVService."
            )

        if not isinstance(
            association_service,
            ProfileCVService,
        ):
            raise TypeError(
                "association_service doit être un "
                "ProfileCVService."
            )

        user_ids = {
            profile_service.user_id,
            cv_service.user_id,
            association_service.user_id,
        }

        if len(user_ids) != 1:
            raise WorkspaceOnboardingError(
                "Les services d'onboarding n'appartiennent "
                "pas au même utilisateur."
            )

        self.profile_service = profile_service
        self.cv_service = cv_service
        self.association_service = (
            association_service
        )

    @property
    def user_id(self) -> str:
        return self.cv_service.user_id

    def create_from_bytes(
        self,
        *,
        content: bytes,
        original_filename: str,
        profile: Profile,
        cv_title: str | None = None,
        duplicate_policy: str = (
            CVService.DUPLICATE_REUSE
        ),
        analyze: bool = True,
    ) -> WorkspaceOnboardingResult:
        """
        Crée un profil de recherche à partir d'un PDF
        déjà chargé en mémoire.
        """

        self._validate_profile(profile)

        imported = self.cv_service.import_bytes(
            content=content,
            title=(
                str(cv_title or "").strip()
                or profile.name
                or original_filename
            ),
            original_filename=original_filename,
            content_type="application/pdf",
            duplicate_policy=duplicate_policy,
            analyze=analyze,
        )

        profile_created = False

        try:
            profile_result = (
                self.profile_service.create_profile(
                    profile=profile
                )
            )

            profile_created = True

            profile_id = self._extract_profile_id(
                profile_result
            )

            association = (
                self.association_service.attach_cv(
                    profile_id=profile_id,
                    cv_id=imported.cv_id,
                    is_primary=True,
                )
            )

        except Exception as error:
            self._rollback(
                cv_id=imported.cv_id,
                duplicate_reused=(
                    imported.duplicate_reused
                ),
                profile_result=(
                    profile_result
                    if profile_created
                    else None
                ),
            )

            raise WorkspaceOnboardingError(
                "Impossible de terminer la création "
                "du profil et son association au CV."
            ) from error

        return WorkspaceOnboardingResult(
            profile_id=profile_id,
            document=imported.document,
            association=association,
            analysis=imported.analysis,
            duplicate_reused=(
                imported.duplicate_reused
            ),
            warnings=imported.warnings,
        )

    def create_from_stream(
        self,
        *,
        stream: BinaryIO,
        original_filename: str,
        profile: Profile,
        cv_title: str | None = None,
        duplicate_policy: str = (
            CVService.DUPLICATE_REUSE
        ),
        analyze: bool = True,
    ) -> WorkspaceOnboardingResult:
        reader = getattr(
            stream,
            "read",
            None,
        )

        if not callable(reader):
            raise TypeError(
                "stream doit fournir une méthode read()."
            )

        content = reader()

        if not isinstance(content, bytes):
            raise WorkspaceOnboardingError(
                "Le flux du CV doit retourner des bytes."
            )

        return self.create_from_bytes(
            content=content,
            original_filename=original_filename,
            profile=profile,
            cv_title=cv_title,
            duplicate_policy=duplicate_policy,
            analyze=analyze,
        )

    @staticmethod
    def _validate_profile(
        profile: Profile,
    ) -> None:
        if not isinstance(
            profile,
            Profile,
        ):
            raise TypeError(
                "profile doit être une instance "
                "de Profile."
            )

        if not str(
            profile.name or ""
        ).strip():
            raise WorkspaceOnboardingError(
                "Le profil doit posséder un nom."
            )

    @staticmethod
    def _extract_profile_id(
        result,
    ) -> str:
        profile_id = str(
            getattr(
                result,
                "profile_id",
                "",
            )
            or ""
        ).strip()

        if not profile_id:
            raise WorkspaceOnboardingError(
                "Le service de profils n'a pas retourné "
                "de profile_id."
            )

        return profile_id

    def _rollback(
        self,
        *,
        cv_id: str,
        duplicate_reused: bool,
        profile_result,
    ) -> None:
        """
        Compensation prudente en cas d'échec.

        Un CV déjà existant et réutilisé n'est jamais supprimé.
        Le profil est supprimé uniquement si le service expose
        explicitement une méthode compatible.
        """

        if not duplicate_reused:
            try:
                self.cv_service.delete_cv(
                    cv_id
                )
            except CVError:
                pass
            except Exception:
                pass

        if profile_result is None:
            return

        profile_id = str(
            getattr(
                profile_result,
                "profile_id",
                "",
            )
            or ""
        ).strip()

        if not profile_id:
            return

        delete_method = getattr(
            self.profile_service,
            "delete_profile",
            None,
        )

        if not callable(delete_method):
            return

        try:
            delete_method(profile_id)
        except Exception:
            pass