from __future__ import annotations

from collections.abc import Iterable
from pathlib import Path
from typing import Any, BinaryIO

from src.ai.skill_extractor import (
    SkillExtractor,
)
from src.cv.cv_parser import (
    CVParser,
)
from src.cvs.exceptions import (
    CVAnalysisError,
    CVNotFoundError,
    CVTooLargeError,
    DuplicateCVError,
    InvalidCVError,
)
from src.cvs.models import (
    CVDocument,
)
from src.cvs.repository import (
    CVRepository,
)
from src.cvs.results import (
    CVAnalysisResult,
    CVImportResult,
)


class CVService:
    """
    Service métier de gestion de la bibliothèque CV.

    Responsabilités :

    - validation fonctionnelle du fichier ;
    - import dans le repository utilisateur ;
    - politique de gestion des doublons ;
    - extraction du texte ;
    - extraction des compétences ;
    - production d’un résultat explicable.
    """

    DEFAULT_MAX_SIZE_BYTES = (
        10 * 1024 * 1024
    )

    DUPLICATE_REJECT = "reject"
    DUPLICATE_REUSE = "reuse"
    DUPLICATE_ALLOW = "allow"

    ALLOWED_DUPLICATE_POLICIES = {
        DUPLICATE_REJECT,
        DUPLICATE_REUSE,
        DUPLICATE_ALLOW,
    }

    def __init__(
        self,
        repository: CVRepository,
        parser: Any | None = None,
        skill_extractor: Any | None = None,
        max_size_bytes: int = (
            DEFAULT_MAX_SIZE_BYTES
        ),
    ) -> None:
        if not isinstance(
            repository,
            CVRepository,
        ):
            raise TypeError(
                "repository doit être une instance "
                "de CVRepository."
            )

        normalized_max_size = int(
            max_size_bytes
        )

        if normalized_max_size <= 0:
            raise ValueError(
                "max_size_bytes doit être supérieur "
                "à zéro."
            )

        self.repository = repository
        self.parser = parser or CVParser()
        self.skill_extractor = (
            skill_extractor
            or SkillExtractor()
        )
        self.max_size_bytes = (
            normalized_max_size
        )

    @property
    def user_id(self) -> str:
        return self.repository.user_id

    def import_bytes(
        self,
        content: bytes,
        title: str,
        original_filename: str,
        content_type: str = "application/pdf",
        duplicate_policy: str = DUPLICATE_REJECT,
        analyze: bool = True,
    ) -> CVImportResult:
        """
        Importe un CV fourni sous forme de bytes.
        """

        self._validate_size(
            content
        )

        policy = self._normalize_duplicate_policy(
            duplicate_policy
        )

        checksum = (
            self.repository
            .compute_checksum(content)
        )

        existing = (
            self.repository
            .find_by_checksum(checksum)
        )

        if existing is not None:
            if policy == self.DUPLICATE_REJECT:
                raise DuplicateCVError(
                    "Un CV identique est déjà "
                    "présent dans la bibliothèque."
                )

            if policy == self.DUPLICATE_REUSE:
                analysis = (
                    self.analyze(existing.cv_id)
                    if analyze
                    else None
                )

                return CVImportResult(
                    document=existing,
                    analysis=analysis,
                    duplicate_reused=True,
                    warnings=(
                        "Le document existant a été "
                        "réutilisé car son contenu est "
                        "identique.",
                    ),
                )

        document = self.repository.import_bytes(
            content=content,
            title=self._normalize_title(
                title=title,
                original_filename=(
                    original_filename
                ),
            ),
            original_filename=(
                original_filename
            ),
            content_type=content_type,
            reject_duplicates=(
                policy != self.DUPLICATE_ALLOW
            ),
        )

        analysis: CVAnalysisResult | None = None
        warnings: list[str] = []

        if analyze:
            try:
                analysis = self.analyze(
                    document.cv_id
                )
            except CVAnalysisError as error:
                warnings.append(str(error))

        return CVImportResult(
            document=document,
            analysis=analysis,
            duplicate_reused=False,
            warnings=tuple(warnings),
        )

    def import_file(
        self,
        source_path: str | Path,
        title: str | None = None,
        duplicate_policy: str = DUPLICATE_REJECT,
        analyze: bool = True,
    ) -> CVImportResult:
        """
        Importe un PDF présent sur le disque.
        """

        path = Path(
            source_path
        ).expanduser().resolve()

        if not path.is_file():
            raise InvalidCVError(
                f"Le fichier CV n’existe pas : {path}"
            )

        return self.import_bytes(
            content=path.read_bytes(),
            title=(
                title
                or path.stem
            ),
            original_filename=path.name,
            content_type="application/pdf",
            duplicate_policy=(
                duplicate_policy
            ),
            analyze=analyze,
        )

    def import_stream(
        self,
        stream: BinaryIO,
        title: str,
        original_filename: str,
        content_type: str = "application/pdf",
        duplicate_policy: str = DUPLICATE_REJECT,
        analyze: bool = True,
    ) -> CVImportResult:
        """
        Importe un flux provenant notamment de Streamlit.
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

        if not isinstance(content, bytes):
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
            duplicate_policy=(
                duplicate_policy
            ),
            analyze=analyze,
        )

    def analyze(
        self,
        cv_id: str,
    ) -> CVAnalysisResult:
        """
        Analyse un CV déjà présent dans la bibliothèque.
        """

        document = self.repository.get(
            cv_id
        )

        try:
            text = self.parser.extract_text(
                str(document.document_path)
            )
        except Exception as error:
            raise CVAnalysisError(
                "Impossible d’extraire le texte du CV."
            ) from error

        normalized_text = str(
            text or ""
        ).strip()

        if not normalized_text:
            raise CVAnalysisError(
                "Aucun texte exploitable n’a été "
                "extrait du CV."
            )

        try:
            extracted_skills = (
                self.skill_extractor.extract(
                    normalized_text
                )
            )
        except Exception as error:
            raise CVAnalysisError(
                "Impossible d’extraire les "
                "compétences du CV."
            ) from error

        skills = self._normalize_skills(
            extracted_skills
        )

        return CVAnalysisResult(
            text=normalized_text,
            skills=skills,
        )

    def list_cvs(
        self,
    ) -> list[CVDocument]:
        return self.repository.list_all()

    def get_cv(
        self,
        cv_id: str,
    ) -> CVDocument:
        return self.repository.get(cv_id)

    def rename_cv(
        self,
        cv_id: str,
        title: str,
    ) -> CVDocument:
        return self.repository.rename(
            cv_id=cv_id,
            title=self._required_text(
                title,
                "title",
            ),
        )

    def delete_cv(
        self,
        cv_id: str,
    ) -> CVDocument:
        return self.repository.delete(cv_id)

    def read_cv(
        self,
        cv_id: str,
    ) -> bytes:
        return self.repository.read_content(
            cv_id
        )

    def find_duplicate(
        self,
        content: bytes,
    ) -> CVDocument | None:
        self._validate_size(content)

        checksum = (
            self.repository
            .compute_checksum(content)
        )

        return (
            self.repository
            .find_by_checksum(checksum)
        )

    def _validate_size(
        self,
        content: bytes,
    ) -> None:
        if not isinstance(content, bytes):
            raise TypeError(
                "content doit être de type bytes."
            )

        if not content:
            raise InvalidCVError(
                "Le document CV est vide."
            )

        if len(content) > self.max_size_bytes:
            raise CVTooLargeError(
                "Le CV dépasse la taille maximale "
                f"autorisée de {self.max_size_bytes} "
                "octets."
            )

    @classmethod
    def _normalize_duplicate_policy(
        cls,
        value: str,
    ) -> str:
        normalized = str(
            value or ""
        ).strip().casefold()

        if (
            normalized
            not in cls.ALLOWED_DUPLICATE_POLICIES
        ):
            raise ValueError(
                "duplicate_policy doit valoir "
                "'reject', 'reuse' ou 'allow'."
            )

        return normalized

    @classmethod
    def _normalize_title(
        cls,
        title: str,
        original_filename: str,
    ) -> str:
        normalized = str(
            title or ""
        ).strip()

        if normalized:
            return normalized

        fallback = Path(
            str(original_filename or "")
        ).stem.strip()

        return cls._required_text(
            fallback,
            "title",
        )

    @staticmethod
    def _normalize_skills(
        values: Iterable[Any] | None,
    ) -> tuple[str, ...]:
        result: list[str] = []
        seen: set[str] = set()

        for value in values or ():
            skill = str(
                value or ""
            ).strip().casefold()

            if not skill or skill in seen:
                continue

            seen.add(skill)
            result.append(skill)

        return tuple(
            sorted(result)
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