from __future__ import annotations

from dataclasses import dataclass

from src.career.user_cv_profile_service import (
    UserCVProfileService,
)
from src.cvs.profile_cv_repository import (
    ProfileCVRepository,
)
from src.cvs.profile_cv_service import (
    ProfileCVService,
)
from src.cvs.repository import (
    CVRepository,
)
from src.cvs.service import (
    CVService,
)
from src.storage.user_paths import (
    UserStoragePaths,
)
from src.workspace.exceptions import (
    WorkspaceConfigurationError,
)
from src.workspace.onboarding import (
    WorkspaceOnboardingService,
)
from src.workspace.analysis_service import (
    WorkspaceAnalysisService,
)

@dataclass(frozen=True, slots=True)
class WorkspaceServices:
    """
    Ensemble cohérent des services utilisateur.

    Tous les services doivent appartenir au même user_id
    et utiliser le même espace de stockage.
    """

    paths: UserStoragePaths
    profile_service: UserCVProfileService
    cv_repository: CVRepository
    cv_service: CVService
    association_repository: ProfileCVRepository
    association_service: ProfileCVService
    onboarding_service: WorkspaceOnboardingService
    analysis_service: WorkspaceAnalysisService

    def __post_init__(self) -> None:
        expected_user_id = self.paths.user_id

        components = {
            "profile_service": (
                self.profile_service.user_id
            ),
            "cv_repository": (
                self.cv_repository.user_id
            ),
            "cv_service": (
                self.cv_service.user_id
            ),
            "association_repository": (
                self.association_repository.user_id
            ),
            "association_service": (
                self.association_service.user_id
            ),
            "onboarding_service": (
                self.onboarding_service.user_id
            ),
            "analysis_service": (
                self.analysis_service.user_id
            ),
        }

        invalid_components = {
            name: user_id
            for name, user_id
            in components.items()
            if user_id != expected_user_id
        }

        if invalid_components:
            details = ", ".join(
                (
                    f"{name}={user_id!r}"
                    for name, user_id
                    in sorted(
                        invalid_components.items()
                    )
                )
            )

            raise WorkspaceConfigurationError(
                "Les services du Workspace "
                "n'appartiennent pas tous au même "
                f"utilisateur : {details}"
            )

        expected_profiles_directory = (
            self.paths
            .profiles_directory
            .resolve()
        )

        actual_profiles_directory = (
            self.profile_service
            .profiles_directory
            .resolve()
        )

        if (
            actual_profiles_directory
            != expected_profiles_directory
        ):
            raise WorkspaceConfigurationError(
                "Le service de profils n'utilise pas "
                "le répertoire du Workspace."
            )

        expected_cvs_directory = (
            self.paths
            .cvs_directory
            .resolve()
        )

        actual_cvs_directory = (
            self.cv_repository
            .paths
            .cvs_directory
            .resolve()
        )

        if (
            actual_cvs_directory
            != expected_cvs_directory
        ):
            raise WorkspaceConfigurationError(
                "Le repository CV n'utilise pas "
                "le répertoire du Workspace."
            )

        if (
            self.cv_service.repository
            is not self.cv_repository
        ):
            raise WorkspaceConfigurationError(
                "CVService doit utiliser le repository "
                "CV partagé par le Workspace."
            )

        if (
            self.association_repository
            .cv_repository
            is not self.cv_repository
        ):
            raise WorkspaceConfigurationError(
                "ProfileCVRepository doit utiliser "
                "le repository CV partagé."
            )

        if (
            self.association_service
            .cv_repository
            is not self.cv_repository
        ):
            raise WorkspaceConfigurationError(
                "ProfileCVService doit utiliser "
                "le repository CV partagé."
            )

        if (
            self.association_service
            .association_repository
            is not self.association_repository
        ):
            raise WorkspaceConfigurationError(
                "ProfileCVService doit utiliser "
                "le repository d'associations partagé."
            )
        
        if (
            self.onboarding_service
            .profile_service
            is not self.profile_service
        ):
            raise WorkspaceConfigurationError(
                "WorkspaceOnboardingService doit utiliser "
                "le service de profils partagé."
            )

        if (
            self.onboarding_service
            .cv_service
            is not self.cv_service
        ):
            raise WorkspaceConfigurationError(
                "WorkspaceOnboardingService doit utiliser "
                "le service CV partagé."
            )

        if (
            self.onboarding_service
            .association_service
            is not self.association_service
        ):
            raise WorkspaceConfigurationError(
                "WorkspaceOnboardingService doit utiliser "
                "le service d'associations partagé."
            )
        
        if (
            self.analysis_service.cv_service
            is not self.cv_service
        ):
            raise WorkspaceConfigurationError(
                "WorkspaceAnalysisService doit utiliser "
                "le service CV partagé."
            )

        if (
            self.analysis_service
            .association_service
            is not self.association_service
        ):
            raise WorkspaceConfigurationError(
                "WorkspaceAnalysisService doit utiliser "
                "le service d'associations partagé."
            )
            
    @property
    def user_id(self) -> str:
        return self.paths.user_id