from __future__ import annotations

from collections.abc import Mapping
from typing import Any
from uuid import NAMESPACE_URL, uuid5

from src.auth.exceptions import (
    AuthenticationConfigurationError,
    IdentityClaimsError,
)
from src.auth.models import (
    CurrentUser,
    Role,
)


class StreamlitAuthAdapter:
    """
    Adaptateur entre l'authentification Streamlit
    et le domaine Auth de JobAgent.

    Cette classe est la seule couche autorisée
    à interpréter directement st.user et à appeler
    st.login() ou st.logout().
    """

    DEFAULT_ISSUER = "google"

    def __init__(
        self,
        streamlit_module: Any | None = None,
    ) -> None:
        self._streamlit = (
            streamlit_module
            if streamlit_module is not None
            else self._import_streamlit()
        )

    @property
    def streamlit(self) -> Any:
        return self._streamlit

    def is_logged_in(self) -> bool:
        """
        Indique si Streamlit possède une identité
        authentifiée pour la session courante.
        """

        user = self._streamlit_user()

        return bool(
            self._claim(
                user,
                "is_logged_in",
                False,
            )
        )

    def current_user(
        self,
    ) -> CurrentUser | None:
        """
        Convertit les claims OIDC Streamlit
        en CurrentUser.

        Retourne None si aucune session
        authentifiée n'est disponible.
        """

        if not self.is_logged_in():
            return None

        claims = self._streamlit_user()

        subject = self._required_claim(
            claims,
            "sub",
        )

        email = self._required_claim(
            claims,
            "email",
        )

        self._validate_verified_email(
            claims
        )

        issuer = self._text_claim(
            claims,
            "iss",
        ) or self.DEFAULT_ISSUER

        display_name = (
            self._text_claim(
                claims,
                "name",
            )
            or self._text_claim(
                claims,
                "given_name",
            )
            or email.split(
                "@",
                maxsplit=1,
            )[0]
        )

        user_id = self.build_user_id(
            issuer=issuer,
            subject=subject,
        )

        return CurrentUser(
            user_id=user_id,
            subject=subject,
            email=email,
            display_name=display_name,
            authenticated=True,
            authorized=False,
            roles=(
                Role.USER,
            ),
        )

    def login(self) -> None:
        """
        Redirige l'utilisateur vers le fournisseur
        OIDC configuré dans Streamlit.
        """

        login = getattr(
            self._streamlit,
            "login",
            None,
        )

        if not callable(login):
            raise AuthenticationConfigurationError(
                "st.login() n'est pas disponible. "
                "Vérifiez la version et la configuration "
                "de Streamlit."
            )

        login()

    def logout(self) -> None:
        """
        Déconnecte la session Streamlit courante.
        """

        logout = getattr(
            self._streamlit,
            "logout",
            None,
        )

        if not callable(logout):
            raise AuthenticationConfigurationError(
                "st.logout() n'est pas disponible."
            )

        logout()

    def allowed_emails(
        self,
    ) -> list[str]:
        """
        Lit la liste blanche depuis :

        [access]
        allowed_emails = [...]
        """

        try:
            secrets = self._streamlit.secrets
        except (
            AttributeError,
            FileNotFoundError,
        ) as error:
            raise AuthenticationConfigurationError(
                "Les secrets Streamlit sont introuvables."
            ) from error

        access_section = self._mapping_value(
            secrets,
            "access",
        )

        if access_section is None:
            raise AuthenticationConfigurationError(
                "La section [access] est absente "
                "des secrets Streamlit."
            )

        values = self._mapping_value(
            access_section,
            "allowed_emails",
        )

        if values is None:
            raise AuthenticationConfigurationError(
                "access.allowed_emails est absent "
                "des secrets Streamlit."
            )

        if isinstance(values, str):
            values = [
                values,
            ]

        if not isinstance(
            values,
            (
                list,
                tuple,
            ),
        ):
            raise AuthenticationConfigurationError(
                "access.allowed_emails doit être "
                "une liste."
            )

        return [
            str(value).strip()
            for value in values
            if str(value or "").strip()
        ]

    @staticmethod
    def build_user_id(
        issuer: str,
        subject: str,
    ) -> str:
        """
        Produit un identifiant interne stable à partir
        de l'émetteur OIDC et du claim subject.
        """

        normalized_issuer = str(
            issuer or ""
        ).strip()

        normalized_subject = str(
            subject or ""
        ).strip()

        if not normalized_subject:
            raise IdentityClaimsError(
                "Le claim OIDC 'sub' est obligatoire."
            )

        identity = (
            f"{normalized_issuer}|"
            f"{normalized_subject}"
        )

        return str(
            uuid5(
                NAMESPACE_URL,
                identity,
            )
        )

    def _streamlit_user(self) -> Any:
        try:
            return self._streamlit.user
        except AttributeError as error:
            raise AuthenticationConfigurationError(
                "st.user n'est pas disponible. "
                "L'authentification Streamlit semble "
                "ne pas être configurée."
            ) from error

    @classmethod
    def _required_claim(
        cls,
        claims: Any,
        name: str,
    ) -> str:
        value = cls._text_claim(
            claims,
            name,
        )

        if not value:
            raise IdentityClaimsError(
                f"Le claim OIDC {name!r} "
                "est obligatoire."
            )

        return value

    @classmethod
    def _text_claim(
        cls,
        claims: Any,
        name: str,
    ) -> str:
        value = cls._claim(
            claims,
            name,
            "",
        )

        return str(
            value or ""
        ).strip()

    @classmethod
    def _validate_verified_email(
        cls,
        claims: Any,
    ) -> None:
        value = cls._claim(
            claims,
            "email_verified",
            None,
        )

        if value is None:
            return

        if isinstance(value, str):
            verified = (
                value.strip().casefold()
                in {
                    "true",
                    "1",
                    "yes",
                }
            )
        else:
            verified = bool(value)

        if not verified:
            raise IdentityClaimsError(
                "L'adresse e-mail Google "
                "n'est pas vérifiée."
            )

    @staticmethod
    def _claim(
        claims: Any,
        name: str,
        default: Any = None,
    ) -> Any:
        if isinstance(
            claims,
            Mapping,
        ):
            return claims.get(
                name,
                default,
            )

        getter = getattr(
            claims,
            "get",
            None,
        )

        if callable(getter):
            try:
                return getter(
                    name,
                    default,
                )
            except TypeError:
                pass

        return getattr(
            claims,
            name,
            default,
        )

    @staticmethod
    def _mapping_value(
        mapping: Any,
        key: str,
    ) -> Any:
        if isinstance(
            mapping,
            Mapping,
        ):
            return mapping.get(key)

        getter = getattr(
            mapping,
            "get",
            None,
        )

        if callable(getter):
            try:
                return getter(key)
            except (
                KeyError,
                TypeError,
            ):
                return None

        return getattr(
            mapping,
            key,
            None,
        )

    @staticmethod
    def _import_streamlit() -> Any:
        try:
            import streamlit as st
        except ImportError as error:
            raise AuthenticationConfigurationError(
                "Streamlit n'est pas installé."
            ) from error

        return st