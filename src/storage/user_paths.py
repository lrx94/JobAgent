from __future__ import annotations

import re
from pathlib import Path


class InvalidStorageIdentifierError(ValueError):
    """
    Un identifiant utilisé pour construire un chemin
    de stockage n'est pas valide.
    """


class UnsafeStoragePathError(ValueError):
    """
    Le chemin construit pourrait sortir du répertoire
    autorisé pour l'utilisateur.
    """


class UserStoragePaths:
    """
    Construit les chemins de stockage propres à un utilisateur.

    Aucun service métier ne doit assembler directement un chemin
    contenant un user_id, un profile_id, un cv_id ou un nom de fichier.
    """

    IDENTIFIER_PATTERN = re.compile(
        r"^[A-Za-z0-9_-]+$"
    )

    DEFAULT_ROOT = Path("data") / "users"

    def __init__(
        self,
        user_id: str,
        root_directory: str | Path | None = None,
    ) -> None:
        self._user_id = self.validate_identifier(
            user_id,
            field_name="user_id",
        )

        configured_root = (
            Path(root_directory)
            if root_directory is not None
            else self.DEFAULT_ROOT
        )

        self._root_directory = (
            configured_root
            .expanduser()
            .resolve()
        )

        self._user_directory = self._safe_child(
            self._root_directory,
            self._user_id,
        )

    @property
    def user_id(self) -> str:
        return self._user_id

    @property
    def root_directory(self) -> Path:
        """
        Répertoire contenant les espaces de tous les utilisateurs.
        """

        return self._root_directory

    @property
    def user_directory(self) -> Path:
        """
        Racine privée de l'utilisateur courant.
        """

        return self._user_directory

    @property
    def profiles_directory(self) -> Path:
        return self._safe_child(
            self.user_directory,
            "profiles",
        )

    @property
    def cvs_directory(self) -> Path:
        return self._safe_child(
            self.user_directory,
            "cvs",
        )

    @property
    def jobs_directory(self) -> Path:
        return self._safe_child(
            self.user_directory,
            "jobs",
        )

    @property
    def exports_directory(self) -> Path:
        return self._safe_child(
            self.user_directory,
            "exports",
        )

    @property
    def cache_directory(self) -> Path:
        return self._safe_child(
            self.user_directory,
            "cache",
        )

    @property
    def settings_file(self) -> Path:
        return self._safe_child(
            self.user_directory,
            "settings.json",
        )

    @property
    def jobs_database_file(self) -> Path:
        return self._safe_child(
            self.jobs_directory,
            "jobs.db",
        )

    def profile_directory(
        self,
        profile_id: str,
    ) -> Path:
        normalized_profile_id = (
            self.validate_identifier(
                profile_id,
                field_name="profile_id",
            )
        )

        return self._safe_child(
            self.profiles_directory,
            normalized_profile_id,
        )

    def profile_config_file(
        self,
        profile_id: str,
    ) -> Path:
        return self._safe_child(
            self.profile_directory(
                profile_id
            ),
            "config.json",
        )

    def cv_directory(
        self,
        cv_id: str,
    ) -> Path:
        normalized_cv_id = (
            self.validate_identifier(
                cv_id,
                field_name="cv_id",
            )
        )

        return self._safe_child(
            self.cvs_directory,
            normalized_cv_id,
        )

    def cv_document_file(
        self,
        cv_id: str,
        extension: str = ".pdf",
    ) -> Path:
        normalized_extension = (
            self.validate_extension(
                extension
            )
        )

        return self._safe_child(
            self.cv_directory(cv_id),
            f"document{normalized_extension}",
        )

    def cv_metadata_file(
        self,
        cv_id: str,
    ) -> Path:
        return self._safe_child(
            self.cv_directory(cv_id),
            "metadata.json",
        )

    def export_file(
        self,
        filename: str,
    ) -> Path:
        safe_filename = self.validate_filename(
            filename
        )

        return self._safe_child(
            self.exports_directory,
            safe_filename,
        )

    def cache_file(
        self,
        filename: str,
    ) -> Path:
        safe_filename = self.validate_filename(
            filename
        )

        return self._safe_child(
            self.cache_directory,
            safe_filename,
        )

    def ensure_directories(self) -> None:
        """
        Crée l'arborescence minimale de l'utilisateur.
        """

        directories = (
            self.user_directory,
            self.profiles_directory,
            self.cvs_directory,
            self.jobs_directory,
            self.exports_directory,
            self.cache_directory,
        )

        for directory in directories:
            directory.mkdir(
                parents=True,
                exist_ok=True,
            )

    def ensure_profile_directory(
        self,
        profile_id: str,
    ) -> Path:
        directory = self.profile_directory(
            profile_id
        )

        directory.mkdir(
            parents=True,
            exist_ok=True,
        )

        return directory

    def ensure_cv_directory(
        self,
        cv_id: str,
    ) -> Path:
        directory = self.cv_directory(
            cv_id
        )

        directory.mkdir(
            parents=True,
            exist_ok=True,
        )

        return directory

    def assert_owned_path(
        self,
        candidate: str | Path,
    ) -> Path:
        """
        Vérifie qu'un chemin appartient bien à l'espace utilisateur.

        Cette méthode doit être appelée avant toute lecture ou écriture
        lorsqu'un chemin provient d'une autre couche.
        """

        resolved_candidate = (
            Path(candidate)
            .expanduser()
            .resolve()
        )

        if not self._is_within(
            resolved_candidate,
            self.user_directory,
        ):
            raise UnsafeStoragePathError(
                "Le chemin demandé se trouve hors "
                "de l'espace de stockage utilisateur."
            )

        return resolved_candidate

    @classmethod
    def validate_identifier(
        cls,
        value: str,
        field_name: str = "identifier",
    ) -> str:
        cleaned = str(
            value or ""
        ).strip()

        if not cleaned:
            raise InvalidStorageIdentifierError(
                f"{field_name} est obligatoire."
            )

        if (
            cleaned in {".", ".."}
            or "/" in cleaned
            or "\\" in cleaned
        ):
            raise InvalidStorageIdentifierError(
                f"{field_name} contient un chemin interdit."
            )

        if Path(cleaned).is_absolute():
            raise InvalidStorageIdentifierError(
                f"{field_name} ne peut pas être absolu."
            )

        if not cls.IDENTIFIER_PATTERN.fullmatch(
            cleaned
        ):
            raise InvalidStorageIdentifierError(
                f"{field_name} contient des caractères interdits. "
                "Seuls les lettres, chiffres, tirets et "
                "underscores sont autorisés."
            )

        return cleaned

    @staticmethod
    def validate_filename(
        value: str,
    ) -> str:
        cleaned = str(
            value or ""
        ).strip()

        if not cleaned:
            raise InvalidStorageIdentifierError(
                "Le nom de fichier est obligatoire."
            )

        path = Path(cleaned)

        if (
            path.is_absolute()
            or path.name != cleaned
            or cleaned in {".", ".."}
            or "/" in cleaned
            or "\\" in cleaned
        ):
            raise InvalidStorageIdentifierError(
                "Le nom de fichier contient un chemin interdit."
            )

        if "\x00" in cleaned:
            raise InvalidStorageIdentifierError(
                "Le nom de fichier contient un caractère interdit."
            )

        return cleaned

    @staticmethod
    def validate_extension(
        value: str,
    ) -> str:
        cleaned = str(
            value or ""
        ).strip().casefold()

        if not cleaned:
            raise InvalidStorageIdentifierError(
                "L'extension est obligatoire."
            )

        if not cleaned.startswith("."):
            cleaned = f".{cleaned}"

        if not re.fullmatch(
            r"\.[a-z0-9]+",
            cleaned,
        ):
            raise InvalidStorageIdentifierError(
                "L'extension de fichier est invalide."
            )

        return cleaned

    def _safe_child(
        self,
        parent: Path,
        child_name: str,
    ) -> Path:
        candidate = (
            parent
            / child_name
        ).resolve()

        if not self._is_within(
            candidate,
            self.root_directory,
        ):
            raise UnsafeStoragePathError(
                "Le chemin construit sort du répertoire "
                "racine de stockage."
            )

        return candidate

    @staticmethod
    def _is_within(
        candidate: Path,
        parent: Path,
    ) -> bool:
        resolved_candidate = candidate.resolve()
        resolved_parent = parent.resolve()

        return (
            resolved_candidate == resolved_parent
            or resolved_parent
            in resolved_candidate.parents
        )