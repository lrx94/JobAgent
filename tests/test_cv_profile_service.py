from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from src.career import (
    CVProfileService,
)
from src.profile import Profile
from src.ai.skill_extractor import (
    SkillExtractor,
)

class FakeSkillExtractor:

    def extract(
        self,
        text: str,
    ) -> list[str]:
        return [
            "cobit",
            "gouvernance si",
            "transformation si",
            "pmp",
        ]


class TestCVProfileService(unittest.TestCase):

    def setUp(self) -> None:
        self.temporary_directory = (
            tempfile.TemporaryDirectory()
        )

        self.root = Path(
            self.temporary_directory.name
        )

        self.profiles_directory = (
            self.root
            / "profiles"
        )

        self.service = CVProfileService(
            profiles_directory=(
                self.profiles_directory
            ),
            skill_extractor=(
                FakeSkillExtractor()
            ),
        )

    def tearDown(self) -> None:
        self.temporary_directory.cleanup()

    def create_cv_file(self) -> Path:
        cv_path = (
            self.root
            / "source_cv.pdf"
        )

        cv_path.write_bytes(
            b"%PDF-1.4 fake test content"
        )

        return cv_path

    def test_analyzes_text(self):
        analysis = self.service.analyze_text(
            """
            DSI Groupe, directeur de programme.
            Transformation SI, gouvernance et COBIT.
            """
        )

        self.assertTrue(
            analysis.role_suggestions
        )

        self.assertIn(
            "cobit",
            analysis.extracted_skills,
        )

    def test_empty_text_is_rejected(self):
        with self.assertRaises(ValueError):
            self.service.analyze_text(
                "   "
            )

    def test_builds_editable_profile(self):
        analysis = self.service.analyze_text(
            """
            DSI Groupe, transformation SI,
            gouvernance et COBIT.
            """
        )

        generated = self.service.build_profile(
            analysis=analysis,
            role_id="cio",
            keywords=(
                "COBIT, ITIL\n"
                "Transformation SI"
            ),
            locations=(
                "Paris; Remote"
            ),
            salary_min=90000,
            remote=True,
            profile_name="DSI Groupe",
        )

        profile = generated.profile

        self.assertEqual(
            profile.name,
            "DSI Groupe",
        )

        self.assertEqual(
            profile.keywords,
            [
                "COBIT",
                "ITIL",
                "Transformation SI",
            ],
        )

        self.assertEqual(
            profile.locations,
            [
                "Paris",
                "Remote",
            ],
        )

        self.assertEqual(
            profile.salary_min,
            90000,
        )

    def test_creates_profile_and_copies_cv(self):
        cv_path = self.create_cv_file()

        profile = Profile(
            name="Directeur de projet IT",
            keywords=[
                "PMP",
                "PRINCE2",
            ],
            locations=[
                "Paris",
            ],
            salary_min=80000,
            remote=True,
        )

        result = self.service.create_profile(
            profile=profile,
            cv_source_path=cv_path,
        )

        self.assertTrue(
            result.created
        )

        self.assertEqual(
            result.profile_id,
            "directeur_de_projet_it",
        )

        self.assertTrue(
            result.config_path.exists()
        )

        self.assertIsNotNone(
            result.cv_path
        )

        self.assertTrue(
            result.cv_path.exists()
        )

        with result.config_path.open(
            "r",
            encoding="utf-8",
        ) as config_file:
            config = json.load(
                config_file
            )

        self.assertEqual(
            config["name"],
            "Directeur de projet IT",
        )

        self.assertEqual(
            config["keywords"],
            [
                "PMP",
                "PRINCE2",
            ],
        )

        self.assertEqual(
            config["cv"],
            "cv.pdf",
        )

    def test_duplicate_profile_gets_unique_id(self):
        profile = Profile(
            name="DSI Groupe",
            keywords=["COBIT"],
            locations=[],
            salary_min=0,
            remote=True,
        )

        first = self.service.create_profile(
            profile
        )

        second = self.service.create_profile(
            profile
        )

        self.assertEqual(
            first.profile_id,
            "dsi_groupe",
        )

        self.assertEqual(
            second.profile_id,
            "dsi_groupe_2",
        )

    def test_enriches_existing_profile(self):
        initial_directory = (
            self.profiles_directory
            / "data_engineer"
        )

        initial_directory.mkdir(
            parents=True
        )

        initial_config = {
            "name": "Data Engineer",
            "keywords": [
                "Python",
                "SQL",
            ],
            "locations": [
                "Paris",
            ],
            "salary_min": 65000,
            "remote": False,
            "custom_field": "preserved",
        }

        config_path = (
            initial_directory
            / "config.json"
        )

        config_path.write_text(
            json.dumps(
                initial_config
            ),
            encoding="utf-8",
        )

        enrichment = Profile(
            name="Nom ignoré",
            keywords=[
                "SQL",
                "Azure",
                "Spark",
            ],
            locations=[
                "Remote",
            ],
            salary_min=70000,
            remote=True,
        )

        result = self.service.enrich_profile(
            profile_id="data_engineer",
            profile=enrichment,
        )

        self.assertTrue(
            result.updated
        )

        updated = (
            self.service.load_profile_config(
                "data_engineer"
            )
        )

        self.assertEqual(
            updated["name"],
            "Data Engineer",
        )

        self.assertEqual(
            updated["keywords"],
            [
                "Python",
                "SQL",
                "Azure",
                "Spark",
            ],
        )

        self.assertEqual(
            updated["locations"],
            [
                "Paris",
                "Remote",
            ],
        )

        self.assertEqual(
            updated["salary_min"],
            70000,
        )

        self.assertTrue(
            updated["remote"]
        )

        self.assertEqual(
            updated["custom_field"],
            "preserved",
        )

    def test_lists_existing_profiles(self):
        for profile_id in (
            "data_engineer",
            "cloud_architect",
        ):
            directory = (
                self.profiles_directory
                / profile_id
            )

            directory.mkdir(
                parents=True
            )

            (
                directory
                / "config.json"
            ).write_text(
                "{}",
                encoding="utf-8",
            )

        (
            self.profiles_directory
            / "empty_directory"
        ).mkdir(
            parents=True
        )

        self.assertEqual(
            self.service.list_profiles(),
            [
                "cloud_architect",
                "data_engineer",
            ],
        )

    def test_slugify(self):
        self.assertEqual(
            self.service.slugify(
                "Directeur de Projet SI"
            ),
            "directeur_de_projet_si",
        )

        self.assertEqual(
            self.service.slugify(
                "  DAF / CFO  "
            ),
            "daf_cfo",
        )
    def test_analyzes_finance_cv_text(
        self,
    ) -> None:

        service = CVProfileService(
            profiles_directory=(
                self.profiles_directory
            ),
            skill_extractor=SkillExtractor(),
        )
        analysis = service.analyze_text(
            """
            Directeur Financier - Responsable du pilotage
            budgétaire et de la performance financière.

            Contrôle de gestion, reporting financier,
            analyse financière, suivi de la trésorerie,
            pilotage de la masse salariale et SAP.
            """
        )

        self.assertTrue(
            analysis.extracted_skills
        )

        self.assertIn(
            "pilotage budgetaire",
            analysis.extracted_skills,
        )

        self.assertIn(
            "controle de gestion",
            analysis.extracted_skills,
        )

        self.assertIn(
            "sap",
            analysis.extracted_skills,
        )

        self.assertTrue(
            analysis.role_suggestions
        )

        self.assertEqual(
            analysis.role_suggestions[0].role_id,
            "cfo",
        )

        self.assertEqual(
            analysis.suggested_title,
            "Direction financière / DAF / CFO",
        )

if __name__ == "__main__":
    unittest.main()