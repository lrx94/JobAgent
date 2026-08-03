from __future__ import annotations

from typing import Any

from src.auth.adapters.streamlit_auth import (
    StreamlitAuthAdapter,
)
from src.auth.exceptions import (
    AccessDeniedError,
    AuthenticationConfigurationError,
    IdentityClaimsError,
)
from src.auth.repositories.allowlist_repository import (
    AllowListRepository,
)
from src.auth.services.access_controller import (
    AccessController,
)
from src.auth.services.authorization_service import (
    AuthorizationService,
)
from src.auth.user_context import (
    UserContext,
)


def build_access_controller(
    adapter: StreamlitAuthAdapter,
) -> AccessController:
    """
    Construit la chaîne d'autorisation à partir
    des secrets de la session Streamlit.
    """

    repository = AllowListRepository(
        emails=adapter.allowed_emails()
    )

    authorization_service = (
        AuthorizationService(
            repository=repository
        )
    )

    return AccessController(
        authorization_service=(
            authorization_service
        )
    )


def require_streamlit_user(
    streamlit_module: Any | None = None,
    display_account_panel: bool = True,
) -> UserContext:
    """
    Protège une page Streamlit.

    - affiche la connexion si nécessaire ;
    - contrôle la liste blanche ;
    - arrête la page en cas de refus ;
    - retourne un UserContext autorisé.
    """

    adapter = StreamlitAuthAdapter(
        streamlit_module=streamlit_module
    )

    st = adapter.streamlit

    try:
        user = adapter.current_user()

    except (
        AuthenticationConfigurationError,
        IdentityClaimsError,
    ) as error:
        _render_configuration_error(
            st=st,
            error=error,
        )

        st.stop()
        raise

    if user is None:
        _render_login(
            st=st,
            adapter=adapter,
        )

        st.stop()

        raise RuntimeError(
            "Exécution poursuivie après st.stop()."
        )

    try:
        controller = build_access_controller(
            adapter
        )

        context = controller.require_access(
            user
        )

    except AuthenticationConfigurationError as error:
        _render_configuration_error(
            st=st,
            error=error,
        )

        st.stop()
        raise

    except AccessDeniedError:
        _render_access_denied(
            st=st,
            adapter=adapter,
            email=user.email,
        )

        st.stop()

        raise RuntimeError(
            "Exécution poursuivie après st.stop()."
        )

    if display_account_panel:
        _render_account_panel(
            st=st,
            adapter=adapter,
            context=context,
        )

    return context


def _render_login(
    st: Any,
    adapter: StreamlitAuthAdapter,
) -> None:
    st.title(
        "🔐 Connexion à JobAgent"
    )

    st.info(
        "JobAgent est actuellement accessible "
        "uniquement aux comptes autorisés."
    )

    if st.button(
        "Se connecter avec Google",
        type="primary",
        use_container_width=True,
        key="jobagent_google_login",
    ):
        adapter.login()


def _render_access_denied(
    st: Any,
    adapter: StreamlitAuthAdapter,
    email: str,
) -> None:
    st.title(
        "⛔ Accès non autorisé"
    )

    st.error(
        "Votre compte Google est authentifié, "
        "mais il n'est pas autorisé à utiliser "
        "JobAgent."
    )

    st.caption(
        f"Compte connecté : {email}"
    )

    if st.button(
        "Se déconnecter",
        use_container_width=True,
        key="jobagent_denied_logout",
    ):
        adapter.logout()


def _render_configuration_error(
    st: Any,
    error: Exception,
) -> None:
    st.title(
        "⚙️ Configuration requise"
    )

    st.error(
        "L'authentification JobAgent "
        "n'est pas correctement configurée."
    )

    st.caption(
        str(error)
    )


def _render_account_panel(
    st: Any,
    adapter: StreamlitAuthAdapter,
    context: UserContext,
) -> None:
    sidebar = getattr(
        st,
        "sidebar",
        st,
    )

    sidebar.divider()

    sidebar.caption(
        "Compte JobAgent"
    )

    sidebar.write(
        f"**{context.display_name}**"
    )

    sidebar.caption(
        context.email
    )

    if sidebar.button(
        "Se déconnecter",
        key="jobagent_sidebar_logout",
        use_container_width=True,
    ):
        adapter.logout()