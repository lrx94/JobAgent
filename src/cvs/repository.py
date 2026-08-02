from __future__ import annotations

import hashlib
import json
import shutil
from collections.abc import Iterable
from datetime import datetime, timezone
from pathlib import Path
from typing import BinaryIO
from uuid import uuid4

from src.auth.user_context import (
    UserContext,
)
from src.cvs.exceptions import (
    CVNotFoundError,
    CVStorageError,
    DuplicateCVError,
    InvalidCVError,
)
from src.cvs.models import (
    CVDocument,
)
from src.storage.user_paths import (
    UserStoragePaths,
)


class CVRepository:
    """
    Repository local et isolé par utilisateur pour les CV.

    Chaque instance est liée à un UserContext immuable.
    """

    METADATA_FILENAME = "metadata.json"
    DEFAULT_CONTENT_TYPE = "application/pdf"
    DEFAULT_EXTENSION = ".pdf"

    def __init__(
        self,
        user_context: UserContext,
        storage_root: str | Path = (
            Path("data")
            / "users"
        ),
        create_directories: bool = True,
    ) -> None:
        if not isinstance(
            user_context,
            UserContext,
        ):
            raise TypeError(
                "user_context doit être une instance "
                "de UserContext."
            )

        user_context.require_authorized()

        self.user_context = user_context

        self.paths = UserStoragePaths(
            user_id=user_context.user_id,
            root_directory=storage_root,
        )

        if create_directories:
            self.paths.ensure_directories()

    @property
    def user_id(self) -> str:
        return self.user_context.user_id

    def import_file(
        self,
        source_path: str | Path,
        title: str | None = None,
        original_filename: str | None = None,
        content_type: str = DEFAULT_CONTENT_TYPE,
        reject_duplicates: bool = True,
    ) -> CVDocument:
        """
        Importe un fichier existant dans la bibliothèque utilisateur.
        """

        source = Path(
            source_path
        ).expanduser().resolve()

        if not source.is_file():
            raise InvalidCVError(
                f"Le fichier CV n'existe pas : {source}"
            )

        return self.import_bytes(
            content=source.read_bytes(),
            title=(
                title
                or source.stem
            ),
            original_filename=(
                original_filename
                or source.name
            ),
            content_type=content_type,
            reject_duplicates=(
                reject_duplicates
            ),
        )

    def import_stream(
        self,
        stream: BinaryIO,
        title: str,
        original_filename: str,
        content_type: str = DEFAULT_CONTENT_TYPE,
        reject_duplicates: bool = True,
    ) -> CVDocument:
        """
        Importe un flux binaire.
        """

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

        if not isinstance(
            content,
            bytes,
        ):
            raise InvalidCVError(
                "Le flux CV doit retourner des bytes."
            )

        return self.import_bytes(
            content=content,
            title=title,
            original_filename=(
                original_filename
            ),
            content_type=content_type,
            reject_duplicates=(
                reject_duplicates
            ),
        )

    def import_bytes(
        self,
        content: bytes,
        title: str,
        original_filename: str,
        content_type: str = DEFAULT_CONTENT_TYPE,
        reject_duplicates: bool = True,
    ) -> CVDocument:
        """
        Enregistre un nouveau CV dans l'espace utilisateur.
        """

        self._validate_content(
            content
        )

        normalized_title = self._required_text(
            title,
            "title",
        )

        normalized_filename = (
            UserStoragePaths
            .validate_filename(
                original_filename
            )
        )

        normalized_content_type = (
            self._normalize_content_type(
                content_type
            )
        )

        checksum = self.compute_checksum(
            content
        )

        existing = self.find_by_checksum(
            checksum
        )

        if (
            existing is not None
            and reject_duplicates
        ):
            raise DuplicateCVError(
                "Un CV identique est déjà présent "
                f"sous l'identifiant {existing.cv_id}."
            )

        cv_id = str(
            uuid4()
        )

        extension = (
            Path(normalized_filename)
            .suffix
            .casefold()
            or self.DEFAULT_EXTENSION
        )

        if extension != ".pdf":
            raise InvalidCVError(
                "Seuls les fichiers PDF sont acceptés "
                "dans cette version."
            )

        directory = (
            self.paths.ensure_cv_directory(
                cv_id
            )
        )

        document_path = (
            self.paths.cv_document_file(
                cv_id=cv_id,
                extension=extension,
            )
        )

        metadata_path = (
            self.paths.cv_metadata_file(
                cv_id
            )
        )

        now = datetime.now(
            timezone.utc
        )

        document = CVDocument(
            cv_id=cv_id,
            user_id=self.user_id,
            title=normalized_title,
            original_filename=(
                normalized_filename
            ),
            content_type=(
                normalized_content_type
            ),
            size_bytes=len(content),
            checksum=checksum,
            document_path=document_path,
            created_at=now,
            updated_at=now,
        )

        try:
            document_path.write_bytes(
                content
            )

            self._write_metadata(
                document
            )

        except OSError as error:
            shutil.rmtree(
                directory,
                ignore_errors=True,
            )

            raise CVStorageError(
                "Impossible d'enregistrer le CV."
            ) from error

        return document

    def list_all(self) -> list[CVDocument]:
        """
        Liste uniquement les CV de l'utilisateur courant.
        """

        if not self.paths.cvs_directory.exists():
            return []

        documents: list[CVDocument] = []

        for directory in sorted(
            self.paths.cvs_directory.iterdir(),
            key=lambda path: path.name.casefold(),
        ):
            if not directory.is_dir():
                continue

            try:
                document = self._load_from_directory(
                    directory
                )
            except (
                CVNotFoundError,
                InvalidCVError,
                CVStorageError,
                ValueError,
                TypeError,
            ):
                continue

            documents.append(
                document
            )

        documents.sort(
            key=lambda item: (
                item.created_at,
                item.title.casefold(),
            ),
            reverse=True,
        )

        return documents

    def get(
        self,
        cv_id: str,
    ) -> CVDocument:
        normalized_cv_id = (
            UserStoragePaths
            .validate_identifier(
                cv_id,
                field_name="cv_id",
            )
        )

        directory = self.paths.cv_directory(
            normalized_cv_id
        )

        return self._load_from_directory(
            directory
        )

    def exists(
        self,
        cv_id: str,
    ) -> bool:
        try:
            self.get(cv_id)
        except CVNotFoundError:
            return False

        return True

    def find_by_checksum(
        self,
        checksum: str,
    ) -> CVDocument | None:
        normalized_checksum = str(
            checksum or ""
        ).strip().casefold()

        if len(normalized_checksum) != 64:
            return None

        for document in self.list_all():
            if (
                document.checksum
                == normalized_checksum
            ):
                return document

        return None

    def rename(
        self,
        cv_id: str,
        title: str,
    ) -> CVDocument:
        document = self.get(
            cv_id
        )

        renamed = document.renamed(
            title=self._required_text(
                title,
                "title",
            )
        )

        self._write_metadata(
            renamed
        )

        return renamed

    def delete(
        self,
        cv_id: str,
    ) -> CVDocument:
        """
        Supprime le document et ses métadonnées.

        Le contrôle « encore associé à un profil » sera ajouté
        dans la sous-brique ProfileCVRepository.
        """

        document = self.get(
            cv_id
        )

        directory = self.paths.cv_directory(
            document.cv_id
        )

        try:
            shutil.rmtree(
                directory
            )
        except OSError as error:
            raise CVStorageError(
                "Impossible de supprimer le CV."
            ) from error

        return document

    def read_content(
        self,
        cv_id: str,
    ) -> bytes:
        document = self.get(
            cv_id
        )

        try:
            return (
                document.document_path
                .read_bytes()
            )
        except OSError as error:
            raise CVStorageError(
                "Impossible de lire le fichier CV."
            ) from error

    def _load_from_directory(
        self,
        directory: Path,
    ) -> CVDocument:
        if not directory.is_dir():
            raise CVNotFoundError(
                "Le CV demandé n'existe pas."
            )

        owned_directory = (
            self.paths.assert_owned_path(
                directory
            )
        )

        metadata_path = (
            owned_directory
            / self.METADATA_FILENAME
        )

        if not metadata_path.is_file():
            raise CVNotFoundError(
                "Les métadonnées du CV sont absentes."
            )

        try:
            raw_data = json.loads(
                metadata_path.read_text(
                    encoding="utf-8"
                )
            )
        except json.JSONDecodeError as error:
            raise InvalidCVError(
                "Les métadonnées du CV "
                "contiennent un JSON invalide."
            ) from error
        except OSError as error:
            raise CVStorageError(
                "Impossible de lire les métadonnées du CV."
            ) from error

        if not isinstance(
            raw_data,
            dict,
        ):
            raise InvalidCVError(
                "Le format des métadonnées du CV "
                "est invalide."
            )

        metadata_user_id = str(
            raw_data.get(
                "user_id",
                "",
            )
        ).strip()

        if metadata_user_id != self.user_id:
            raise CVNotFoundError(
                "Le CV demandé n'existe pas."
            )

        metadata_cv_id = str(
            raw_data.get(
                "cv_id",
                "",
            )
        ).strip()

        if metadata_cv_id != directory.name:
            raise InvalidCVError(
                "L'identifiant du CV est incohérent."
            )

        document_path = (
            directory
            / "document.pdf"
        ).resolve()

        self.paths.assert_owned_path(
            document_path
        )

        if not document_path.is_file():
            raise CVNotFoundError(
                "Le document PDF du CV est absent."
            )

        document = CVDocument.from_dict(
            raw_data,
            document_path=document_path,
        )

        actual_size = (
            document_path.stat().st_size
        )

        if actual_size != document.size_bytes:
            raise InvalidCVError(
                "La taille du fichier CV ne correspond "
                "pas aux métadonnées."
            )

        return document

    def _write_metadata(
        self,
        document: CVDocument,
    ) -> None:
        if document.user_id != self.user_id:
            raise CVNotFoundError(
                "Le CV demandé n'existe pas."
            )

        metadata_path = (
            self.paths.cv_metadata_file(
                document.cv_id
            )
        )

        self.paths.assert_owned_path(
            metadata_path
        )

        data = document.to_dict(
            include_document_path=False
        )

        try:
            metadata_path.write_text(
                json.dumps(
                    data,
                    ensure_ascii=False,
                    indent=2,
                    sort_keys=True,
                )
                + "\n",
                encoding="utf-8",
            )
        except OSError as error:
            raise CVStorageError(
                "Impossible d'enregistrer "
                "les métadonnées du CV."
            ) from error

    @staticmethod
    def compute_checksum(
        content: bytes,
    ) -> str:
        if not isinstance(
            content,
            bytes,
        ):
            raise TypeError(
                "content doit être de type bytes."
            )

        return hashlib.sha256(
            content
        ).hexdigest()

    @staticmethod
    def _validate_content(
        content: bytes,
    ) -> None:
        if not isinstance(
            content,
            bytes,
        ):
            raise TypeError(
                "content doit être de type bytes."
            )

        if not content:
            raise InvalidCVError(
                "Le document CV est vide."
            )

        if not content.startswith(
            b"%PDF"
        ):
            raise InvalidCVError(
                "Le document fourni n'est pas "
                "un fichier PDF valide."
            )

    @staticmethod
    def _required_text(
        value: str,
        field_name: str,
    ) -> str:
        cleaned = str(
            value or ""
        ).strip()

        if not cleaned:
            raise InvalidCVError(
                f"{field_name} est obligatoire."
            )

        return cleaned

    @staticmethod
    def _normalize_content_type(
        value: str,
    ) -> str:
        cleaned = str(
            value or ""
        ).strip().casefold()

        if cleaned not in {
            "application/pdf",
            "application/x-pdf",
        }:
            raise InvalidCVError(
                "Le type de contenu doit être "
                "application/pdf."
            )

        return "application/pdf"