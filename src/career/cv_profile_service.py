from __future__ import annotations

import json
import re
import shutil
import unicodedata
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from src.ai.skill_extractor import SkillExtractor
from src.career.models import (
    CareerAnalysis,
    GeneratedProfile,
)
from src.career.profile_builder import (
    CareerProfileBuilder,
)
from src.career.role_detector import RoleDetector
from src.cv.cv_parser import CVParser
from src.profile import Profile


@dataclass(frozen=True, slots=True)
class ProfileSaveResult:
    """
    Résultat de la création ou de l'enrichissement d'un profil.
    """

    action: str
    profile_id: str
    profile_name: str
    profile_directory: Path
    config_path: Path
    cv_path: Path | None

    @property
    def created(self) -> bool:
        return self.action == "created"

    @property
    def updated(self) -> bool:
        return self.action == "updated"


class CVProfileService:
    """
    Orchestre l'analyse d'un CV et la sauvegarde d'un profil.

    Ce service ne dépend pas de Streamlit. Il peut être utilisé par :

    - l'interface web ;
    - les scripts ;
    - les tests ;
    - de futurs traitements automatisés.
    """

    def __init__(
        self,
        profiles_directory: str | Path = "profiles",
        parser: CVParser | None = None,
        skill_extractor: SkillExtractor | None = None,
        role_detector: RoleDetector | None = None,
        profile_builder: CareerProfileBuilder | None = None,
    ) -> None:
        self.profiles_directory = Path(
            profiles_directory
        )

        self.parser = parser or CVParser()
        self.skill_extractor = (
            skill_extractor
            or SkillExtractor()
        )
        self.role_detector = (
            role_detector
            or RoleDetector()
        )
        self.profile_builder = (
            profile_builder
            or CareerProfileBuilder()
        )

    def analyze_pdf(
        self,
        pdf_path: str | Path,
        limit: int = 5,
    ) -> CareerAnalysis:
        """
        Extrait et analyse le contenu d'un CV PDF.
        """

        path = Path(pdf_path)

        if not path.exists():
            raise FileNotFoundError(
                f"Le CV est introuvable : {path}"
            )

        if not path.is_file():
            raise ValueError(
                f"Le chemin n'est pas un fichier : {path}"
            )

        text = self.parser.extract_text(
            str(path)
        )

        return self.analyze_text(
            cv_text=text,
            limit=limit,
        )

    def analyze_text(
        self,
        cv_text: str,
        limit: int = 5,
    ) -> CareerAnalysis:
        """
        Analyse directement le texte déjà extrait d'un CV.
        """

        normalized_text = str(
            cv_text or ""
        ).strip()

        if not normalized_text:
            raise ValueError(
                "Le texte du CV est vide."
            )

        skills = self.skill_extractor.extract(
            normalized_text
        )

        return self.role_detector.analyze(
            cv_text=normalized_text,
            extracted_skills=skills,
            limit=limit,
        )

    def build_profile(
        self,
        analysis: CareerAnalysis,
        role_id: str | None = None,
        keywords: list[str] | None = None,
        locations: list[str] | None = None,
        salary_min: int | None = None,
        remote: bool = True,
        profile_name: str | None = None,
    ) -> GeneratedProfile:
        """
        Construit un profil modifiable à partir de l'analyse.

        Lorsque `keywords` est fourni, cette liste remplace les
        mots-clés générés automatiquement.
        """

        generated = self.profile_builder.build(
            analysis=analysis,
            role_id=role_id,
            locations=locations,
            salary_min=salary_min,
            remote=remote,
        )

        generated_profile = generated.profile

        final_name = str(
            profile_name
            or generated_profile.name
            or analysis.suggested_title
        ).strip()

        if not final_name:
            final_name = "Profil CV"

        final_keywords = self._normalize_list(
            keywords
            if keywords is not None
            else generated_profile.keywords
        )

        profile = Profile(
            name=final_name,
            keywords=final_keywords,
            locations=self._normalize_list(
                locations
                if locations is not None
                else generated_profile.locations
            ),
            salary_min=(
                self._normalize_salary(
                    salary_min
                )
                if salary_min is not None
                else generated_profile.salary_min
            ),
            remote=bool(remote),
        )

        return GeneratedProfile(
            profile=profile,
            analysis=analysis,
            selected_role=generated.selected_role,
            added_keywords=list(
                final_keywords
            ),
        )

    def list_profiles(self) -> list[str]:
        """
        Retourne les identifiants des profils possédant un config.json.
        """

        if not self.profiles_directory.exists():
            return []

        return sorted(
            profile_directory.name
            for profile_directory
            in self.profiles_directory.iterdir()
            if profile_directory.is_dir()
            and (
                profile_directory
                / "config.json"
            ).is_file()
        )

    def load_profile_config(
        self,
        profile_id: str,
    ) -> dict[str, Any]:
        """
        Charge la configuration JSON brute d'un profil.
        """

        config_path = self._profile_config_path(
            profile_id
        )

        if not config_path.exists():
            raise FileNotFoundError(
                "Le profil est introuvable : "
                f"{profile_id}"
            )

        try:
            with config_path.open(
                "r",
                encoding="utf-8",
            ) as config_file:
                data = json.load(
                    config_file
                )
        except json.JSONDecodeError as error:
            raise ValueError(
                "Le fichier de profil contient "
                f"un JSON invalide : {config_path}"
            ) from error

        if not isinstance(data, dict):
            raise ValueError(
                "La configuration du profil doit "
                "être un objet JSON."
            )

        return data

    def create_profile(
        self,
        profile: Profile,
        cv_source_path: str | Path | None = None,
        requested_profile_id: str | None = None,
    ) -> ProfileSaveResult:
        """
        Crée un nouveau profil sans écraser un profil existant.
        """

        base_profile_id = self.slugify(
            requested_profile_id
            or profile.name
        )

        profile_id = self._available_profile_id(
            base_profile_id
        )

        return self._save_profile(
            profile=profile,
            profile_id=profile_id,
            action="created",
            cv_source_path=cv_source_path,
            existing_config={},
        )

    def enrich_profile(
        self,
        profile_id: str,
        profile: Profile,
        cv_source_path: str | Path | None = None,
    ) -> ProfileSaveResult:
        """
        Enrichit un profil existant.

        Les compétences existantes sont conservées et fusionnées avec
        celles proposées depuis le nouveau CV.
        """

        existing_config = (
            self.load_profile_config(
                profile_id
            )
        )

        existing_keywords = self._normalize_list(
            existing_config.get(
                "keywords",
                [],
            )
        )

        merged_keywords = self._merge_lists(
            existing_keywords,
            profile.keywords,
        )

        existing_locations = self._normalize_list(
            existing_config.get(
                "locations",
                [],
            )
        )

        locations = self._merge_lists(
            existing_locations,
            profile.locations,
        )

        existing_name = str(
            existing_config.get(
                "name",
                "",
            )
            or ""
        ).strip()

        enriched_profile = Profile(
            name=existing_name or profile.name,
            keywords=merged_keywords,
            locations=locations,
            salary_min=(
                profile.salary_min
                or self._normalize_salary(
                    existing_config.get(
                        "salary_min",
                        0,
                    )
                )
            ),
            remote=(
                bool(
                    existing_config.get(
                        "remote",
                        False,
                    )
                )
                or profile.remote
            ),
        )

        return self._save_profile(
            profile=enriched_profile,
            profile_id=self.slugify(
                profile_id
            ),
            action="updated",
            cv_source_path=cv_source_path,
            existing_config=existing_config,
        )

    def _save_profile(
        self,
        profile: Profile,
        profile_id: str,
        action: str,
        cv_source_path: str | Path | None,
        existing_config: dict[str, Any],
    ) -> ProfileSaveResult:
        profile_directory = (
            self.profiles_directory
            / profile_id
        )

        profile_directory.mkdir(
            parents=True,
            exist_ok=True,
        )

        cv_path = self._copy_cv(
            source_path=cv_source_path,
            destination_directory=(
                profile_directory
            ),
        )

        current_cv_name = str(
            existing_config.get(
                "cv",
                "",
            )
            or ""
        ).strip()

        config = dict(
            existing_config
        )

        config.update(
            {
                "name": profile.name,
                "keywords": list(
                    profile.keywords
                ),
                "locations": list(
                    profile.locations
                ),
                "salary_min": int(
                    profile.salary_min or 0
                ),
                "remote": bool(
                    profile.remote
                ),
            }
        )

        if cv_path is not None:
            config["cv"] = cv_path.name
        elif current_cv_name:
            config["cv"] = current_cv_name

        config_path = (
            profile_directory
            / "config.json"
        )

        temporary_path = (
            profile_directory
            / "config.json.tmp"
        )

        with temporary_path.open(
            "w",
            encoding="utf-8",
        ) as config_file:
            json.dump(
                config,
                config_file,
                ensure_ascii=False,
                indent=2,
                sort_keys=True,
            )

            config_file.write("\n")

        temporary_path.replace(
            config_path
        )

        return ProfileSaveResult(
            action=action,
            profile_id=profile_id,
            profile_name=profile.name,
            profile_directory=(
                profile_directory
            ),
            config_path=config_path,
            cv_path=cv_path,
        )

    @staticmethod
    def slugify(
        value: str,
    ) -> str:
        """
        Convertit un nom de profil en identifiant de dossier sûr.
        """

        text = str(
            value or ""
        ).strip().casefold()

        decomposed = unicodedata.normalize(
            "NFKD",
            text,
        )

        without_accents = "".join(
            character
            for character in decomposed
            if not unicodedata.combining(
                character
            )
        )

        normalized = re.sub(
            r"[^a-z0-9]+",
            "_",
            without_accents,
        ).strip("_")

        return normalized or "profil_cv"

    def _available_profile_id(
        self,
        base_profile_id: str,
    ) -> str:
        candidate = (
            base_profile_id
            or "profil_cv"
        )

        index = 2

        while (
            self.profiles_directory
            / candidate
        ).exists():
            candidate = (
                f"{base_profile_id}_{index}"
            )

            index += 1

        return candidate

    def _profile_config_path(
        self,
        profile_id: str,
    ) -> Path:
        normalized_profile_id = (
            self.slugify(
                profile_id
            )
        )

        return (
            self.profiles_directory
            / normalized_profile_id
            / "config.json"
        )

    @staticmethod
    def _copy_cv(
        source_path: str | Path | None,
        destination_directory: Path,
    ) -> Path | None:
        if source_path is None:
            return None

        source = Path(
            source_path
        )

        if not source.exists():
            raise FileNotFoundError(
                f"Le CV à copier est introuvable : {source}"
            )

        if not source.is_file():
            raise ValueError(
                f"Le CV à copier n'est pas un fichier : {source}"
            )

        suffix = (
            source.suffix.casefold()
            or ".pdf"
        )

        destination = (
            destination_directory
            / f"cv{suffix}"
        )

        if (
            source.resolve()
            != destination.resolve()
        ):
            shutil.copy2(
                source,
                destination,
            )

        return destination

    @staticmethod
    def _normalize_salary(
        value: Any,
    ) -> int:
        if value in {
            None,
            "",
        }:
            return 0

        try:
            normalized = int(
                float(value)
            )
        except (
            TypeError,
            ValueError,
        ):
            return 0

        return max(
            0,
            normalized,
        )

    @staticmethod
    def _normalize_list(
        values: Any,
    ) -> list[str]:
        if isinstance(values, str):
            raw_values = re.split(
                r"[,;\n]",
                values,
            )
        else:
            raw_values = (
                values
                if isinstance(
                    values,
                    (
                        list,
                        tuple,
                        set,
                    ),
                )
                else []
            )

        normalized: list[str] = []
        seen: set[str] = set()

        for value in raw_values:
            cleaned = str(
                value or ""
            ).strip()

            if not cleaned:
                continue

            key = cleaned.casefold()

            if key in seen:
                continue

            seen.add(key)
            normalized.append(
                cleaned
            )

        return normalized

    @classmethod
    def _merge_lists(
        cls,
        first: Any,
        second: Any,
    ) -> list[str]:
        return cls._normalize_list(
            [
                *cls._normalize_list(
                    first
                ),
                *cls._normalize_list(
                    second
                ),
            ]
        )