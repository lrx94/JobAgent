from __future__ import annotations

import json
import tempfile
from pathlib import Path

from src.profile import Profile
from src.profile_manager import ProfileManager


def create_profile_config(
    profiles_directory: Path,
    directory_name: str,
    data: dict,
) -> Path:
    profile_directory = (
        profiles_directory
        / directory_name
    )

    profile_directory.mkdir(
        parents=True,
        exist_ok=True,
    )

    config_path = (
        profile_directory
        / "config.json"
    )

    config_path.write_text(
        json.dumps(
            data,
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    return config_path


def test_list_profiles() -> None:
    with tempfile.TemporaryDirectory() as temporary_directory:
        profiles_directory = Path(temporary_directory)

        create_profile_config(
            profiles_directory,
            "data_engineer",
            {
                "name": "Data Engineer",
                "keywords": ["Python"],
            },
        )

        create_profile_config(
            profiles_directory,
            "cloud_architect",
            {
                "name": "Cloud Architect",
                "keywords": ["Azure"],
            },
        )

        manager = ProfileManager(
            profiles_directory
        )

        assert manager.list_profiles() == [
            "Cloud Architect",
            "Data Engineer",
        ]


def test_load_profile_by_display_name() -> None:
    with tempfile.TemporaryDirectory() as temporary_directory:
        profiles_directory = Path(temporary_directory)

        create_profile_config(
            profiles_directory,
            "data_engineer",
            {
                "name": "Data Engineer",
                "keywords": [
                    "Python",
                    "Azure",
                ],
                "locations": [
                    "Paris",
                    "Remote",
                ],
                "salary_min": 65_000,
                "remote": True,
            },
        )

        manager = ProfileManager(
            profiles_directory
        )

        profile = manager.load_profile(
            "Data Engineer"
        )

        assert isinstance(profile, Profile)
        assert profile.name == "Data Engineer"
        assert profile.keywords == [
            "Python",
            "Azure",
        ]
        assert profile.locations == [
            "Paris",
            "Remote",
        ]
        assert profile.salary_min == 65_000
        assert profile.remote is True


def test_load_profile_by_directory_name() -> None:
    with tempfile.TemporaryDirectory() as temporary_directory:
        profiles_directory = Path(temporary_directory)

        create_profile_config(
            profiles_directory,
            "product_manager",
            {
                "name": "Product Manager",
                "keywords": [
                    "Product Strategy",
                ],
            },
        )

        manager = ProfileManager(
            profiles_directory
        )

        profile = manager.load_profile(
            "product_manager"
        )

        assert profile.name == "Product Manager"
        assert profile.keywords == [
            "Product Strategy",
        ]


def test_missing_profile_raises_error() -> None:
    with tempfile.TemporaryDirectory() as temporary_directory:
        manager = ProfileManager(
            temporary_directory
        )

        try:
            manager.load_profile(
                "Profil Inconnu"
            )

            raise AssertionError(
                "FileNotFoundError attendu."
            )

        except FileNotFoundError:
            pass


def test_save_profile() -> None:
    with tempfile.TemporaryDirectory() as temporary_directory:
        manager = ProfileManager(
            temporary_directory
        )

        profile = Profile(
            name="AI Engineer",
            keywords=[
                "Python",
                "Machine Learning",
            ],
            locations=[
                "Paris",
            ],
            salary_min=70_000,
            remote=True,
        )

        config_path = manager.save_profile(
            profile
        )

        assert config_path.is_file()
        assert config_path.parent.name == "ai_engineer"

        loaded_profile = manager.load_profile(
            "AI Engineer"
        )

        assert loaded_profile == profile


def test_invalid_salary_uses_zero() -> None:
    with tempfile.TemporaryDirectory() as temporary_directory:
        profiles_directory = Path(temporary_directory)

        create_profile_config(
            profiles_directory,
            "invalid_salary",
            {
                "name": "Invalid Salary",
                "salary_min": "inconnu",
            },
        )

        manager = ProfileManager(
            profiles_directory
        )

        profile = manager.load_profile(
            "Invalid Salary"
        )

        assert profile.salary_min == 0


if __name__ == "__main__":
    test_list_profiles()
    test_load_profile_by_display_name()
    test_load_profile_by_directory_name()
    test_missing_profile_raises_error()
    test_save_profile()
    test_invalid_salary_uses_zero()

    print("✅ test_profile_manager OK")