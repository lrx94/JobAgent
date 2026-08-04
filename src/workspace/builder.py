from __future__ import annotations

from pathlib import Path

from src.auth.user_context import (
    UserContext,
)
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
    WorkspaceAccessError,
)
from src.workspace.models import (
    Workspace,
)
from src.workspace.services import (
    WorkspaceServices,
)
from src.workspace.state import (
    WorkspaceState,
)
from src.workspace.onboarding import (
    WorkspaceOnboardingService,
)
from src.learning import (
    AssistedLearningService,
    LearningSuggestionDetector,
    LearningSuggestionRepository,
)
from src.skills import BUSINESS_CONCEPTS
from src.workspace.learning_service import (
    WorkspaceLearningService,
)

DEFAULT_STORAGE_ROOT = (
    Path("data")
    / "users"
)


def build_workspace(
    user_context: UserContext,
    storage_root: str | Path = (
        DEFAULT_STORAGE_ROOT
    ),
    state: WorkspaceState | None = None,
    create_directories: bool = True,
) -> Workspace:
    """
    Construit un Career Workspace complet et cohérent.

    Cette fonction est l'unique point de construction
    recommandé dans les pages Streamlit.
    """

    if not isinstance(
        user_context,
        UserContext,
    ):
        raise TypeError(
            "user_context doit être "
            "un UserContext."
        )

    try:
        user_context.require_authorized()
    except Exception as error:
        raise WorkspaceAccessError(
            "Un contexte utilisateur autorisé "
            "est requis pour construire "
            "le Workspace."
        ) from error

    normalized_root = (
        Path(storage_root)
        .expanduser()
        .resolve()
    )

    paths = UserStoragePaths(
        user_id=user_context.user_id,
        root_directory=normalized_root,
    )

    if create_directories:
        paths.ensure_directories()

    profile_service = (
        UserCVProfileService(
            user_context=user_context,
            storage_root=normalized_root,
            create_directories=(
                create_directories
            ),
        )
    )

    cv_repository = CVRepository(
        user_context=user_context,
        storage_root=normalized_root,
        create_directories=(
            create_directories
        ),
    )

    cv_service = CVService(
        repository=cv_repository
    )

    association_repository = (
        ProfileCVRepository(
            user_context=user_context,
            cv_repository=cv_repository,
            storage_root=normalized_root,
            create_directories=(
                create_directories
            ),
        )
    )

    association_service = (
        ProfileCVService(
            association_repository=(
                association_repository
            ),
            cv_repository=cv_repository,
        )
    )
    onboarding_service = (
        WorkspaceOnboardingService(
            profile_service=profile_service,
            cv_service=cv_service,
            association_service=(
                association_service
            ),
        )
    )
    known_learning_terms = tuple(
        value
        for concept in BUSINESS_CONCEPTS
        for value in (
            concept.label,
            *concept.aliases,
        )
    )

    learning_repository = (
        LearningSuggestionRepository(
            paths.learning_suggestions_file
        )
    )

    assisted_learning_service = (
        AssistedLearningService(
            detector=(
                LearningSuggestionDetector(
                    known_terms=known_learning_terms,
                    minimum_occurrences=3,
                    minimum_sources=1,
                )
            ),
            repository=learning_repository,
        )
    )

    learning_service = (
        WorkspaceLearningService(
            user_id=user_context.user_id,
            learning_service=(
                assisted_learning_service
            ),
        )
    )

    services = WorkspaceServices(
        paths=paths,
        profile_service=profile_service,
        cv_repository=cv_repository,
        cv_service=cv_service,
        association_repository=(
            association_repository
        ),
        association_service=(
            association_service
        ),
                onboarding_service=(
            onboarding_service
        ),
        learning_service=(
            learning_service
        ),
    )

    return Workspace(
        user_context=user_context,
        services=services,
        state=state or WorkspaceState(),
    )