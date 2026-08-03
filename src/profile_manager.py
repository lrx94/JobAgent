from __future__ import annotations

import json
import re
import unicodedata
from pathlib import Path
from typing import Any

from src.profile import Profile


class ProfileManager:
    """
    Charge et enregistre les profils de recherche JobAgent.

    Structure attendue :

        profiles/
            data_engineer/
                config.json
                cv.pdf
            cloud_architect/
                config.json
    """

    def __init__(
        self,
        profiles_dir: str | Path = "profiles",
    ) -> None:
        self.profiles_dir = Path(profiles_dir)

    def list_profiles(self) -> list[str]:
        """
        Retourne les noms des profils valides, triés alphabétiquement.

        Le nom affiché provient du champ `name` de config.json.
        Lorsque ce champ est absent, le nom du dossier est transformé
        en libellé lisible.
        """

        if not self.profiles_dir.exists():
            return []

        profile_names: list[str] = []

        for profile_directory in sorted(
            self.profiles_dir.iterdir(),
            key=lambda path: path.name.casefold(),
        ):
            if not profile_directory.is_dir():
                continue

            config_path = profile_directory / "config.json"

            if not config_path.is_file():
                continue

            try:
                data = self._read_config(config_path)
            except (OSError, ValueError, TypeError):
                continue

            name = str(
                data.get("name")
                or self._display_name(profile_directory.name)
            ).strip()

            if name:
                profile_names.append(name)

        return sorted(
            profile_names,
            key=str.casefold,
        )

    def load_profile(
        self,
        profile_identifier: str,
    ) -> Profile:
        """
        Charge un profil depuis son nom affiché ou le nom de son dossier.

        Exemples acceptés :

            "Data Engineer"
            "data_engineer"
            "data-engineer"
        """

        config_path = self._find_config(profile_identifier)

        if config_path is None:
            raise FileNotFoundError(
                f"Profil introuvable : {profile_identifier!r}"
            )

        data = self._read_config(config_path)

        return self._build_profile(
            data=data,
            fallback_name=self._display_name(
                config_path.parent.name
            ),
        )

    def get_profile(
        self,
        profile_identifier: str,
    ) -> Profile:
        """
        Alias de load_profile conservé pour compatibilité avec l'UI.
        """

        return self.load_profile(profile_identifier)

    def load(
        self,
        profile_identifier: str,
    ) -> Profile:
        """
        Alias court conservé pour compatibilité.
        """

        return self.load_profile(profile_identifier)

    def save_profile(
        self,
        profile: Profile,
        directory_name: str | None = None,
    ) -> Path:
        """
        Enregistre un profil dans un fichier config.json.

        Retourne le chemin du fichier créé.
        """

        folder_name = (
            self._slugify(directory_name)
            if directory_name
            else self._slugify(profile.name)
        )

        if not folder_name:
            raise ValueError(
                "Impossible de déterminer le dossier du profil."
            )

        profile_directory = self.profiles_dir / folder_name
        profile_directory.mkdir(
            parents=True,
            exist_ok=True,
        )

        config_path = profile_directory / "config.json"

        data = {
            "name": profile.name,
            "keywords": list(profile.keywords),
            "locations": list(profile.locations),
            "salary_min": profile.salary_min,
            "remote": profile.remote,
        }

        config_path.write_text(
            json.dumps(
                data,
                ensure_ascii=False,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )

        return config_path

    def profile_exists(
        self,
        profile_identifier: str,
    ) -> bool:
        """
        Indique si un profil peut être retrouvé.
        """

        return self._find_config(profile_identifier) is not None

    def _find_config(
        self,
        profile_identifier: str,
    ) -> Path | None:
        """
        Retrouve config.json depuis un nom affiché ou un nom de dossier.
        """

        if not profile_identifier:
            return None

        requested = self._normalized_identifier(
            profile_identifier
        )

        direct_directory = (
            self.profiles_dir
            / self._slugify(profile_identifier)
        )

        direct_config = direct_directory / "config.json"

        if direct_config.is_file():
            return direct_config

        if not self.profiles_dir.exists():
            return None

        for profile_directory in self.profiles_dir.iterdir():
            if not profile_directory.is_dir():
                continue

            config_path = profile_directory / "config.json"

            if not config_path.is_file():
                continue

            directory_identifier = self._normalized_identifier(
                profile_directory.name
            )

            if directory_identifier == requested:
                return config_path

            try:
                data = self._read_config(config_path)
            except (OSError, ValueError, TypeError):
                continue

            configured_name = str(
                data.get("name", "")
            )

            if (
                self._normalized_identifier(configured_name)
                == requested
            ):
                return config_path

        return None

    def _read_config(
        self,
        config_path: Path,
    ) -> dict[str, Any]:
        """
        Lit et valide le contenu JSON d'un profil.
        """

        with config_path.open(
            "r",
            encoding="utf-8",
        ) as file:
            data = json.load(file)

        if not isinstance(data, dict):
            raise ValueError(
                f"Configuration invalide : {config_path}"
            )

        return data

    def _build_profile(
        self,
        data: dict[str, Any],
        fallback_name: str,
    ) -> Profile:
        """
        Construit un objet Profile à partir d'une configuration JSON.
        """

        name = str(
            data.get("name")
            or fallback_name
        ).strip()

        keywords = self._string_list(
            data.get("keywords", [])
        )

        locations = self._string_list(
            data.get("locations", [])
        )

        salary_min = self._safe_integer(
            data.get("salary_min", 0)
        )

        remote = self._safe_boolean(
            data.get("remote", False)
        )

        return Profile(
            name=name,
            keywords=keywords,
            locations=locations,
            salary_min=salary_min,
            remote=remote,
        )

    def _string_list(
        self,
        value: Any,
    ) -> list[str]:
        """
        Convertit une valeur JSON en liste de chaînes nettoyées.
        """

        if value is None:
            return []

        if isinstance(value, str):
            values = [value]
        elif isinstance(value, (list, tuple, set)):
            values = list(value)
        else:
            return []

        result: list[str] = []

        for item in values:
            text = str(item).strip()

            if text and text not in result:
                result.append(text)

        return result

    def _safe_integer(
        self,
        value: Any,
    ) -> int:
        """
        Convertit proprement un salaire en entier.
        """

        try:
            return max(
                int(float(value or 0)),
                0,
            )
        except (TypeError, ValueError):
            return 0

    def _safe_boolean(
        self,
        value: Any,
    ) -> bool:
        """
        Convertit les valeurs booléennes provenant du JSON.
        """

        if isinstance(value, bool):
            return value

        if isinstance(value, str):
            return value.strip().casefold() in {
                "1",
                "true",
                "yes",
                "oui",
                "on",
            }

        return bool(value)

    def _display_name(
        self,
        directory_name: str,
    ) -> str:
        """
        Transforme `data_engineer` en `Data Engineer`.
        """

        return re.sub(
            r"[_\-]+",
            " ",
            directory_name,
        ).strip().title()

    def _slugify(
        self,
        value: str | None,
    ) -> str:
        """
        Transforme un nom de profil en nom de dossier stable.
        """

        if not value:
            return ""

        normalized = unicodedata.normalize(
            "NFKD",
            str(value),
        )

        without_accents = "".join(
            character
            for character in normalized
            if not unicodedata.combining(character)
        )

        slug = re.sub(
            r"[^a-zA-Z0-9]+",
            "_",
            without_accents,
        )

        return slug.strip("_").casefold()

    def _normalized_identifier(
        self,
        value: str,
    ) -> str:
        """
        Normalise les identifiants pour les comparaisons.
        """

        return self._slugify(value)