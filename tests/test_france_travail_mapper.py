from __future__ import annotations

import unittest

from src.providers.france_travail_mapper import (
    FranceTravailJobMapper,
)


class TestFranceTravailMapper(
    unittest.TestCase
):

    def setUp(self):
        self.mapper = (
            FranceTravailJobMapper()
        )

    def test_maps_complete_offer(self):
        item = {
            "id": "123ABC",
            "intitule": "Directeur SI",
            "description": (
                "Poste hybride avec "
                "télétravail."
            ),
            "dateCreation": (
                "2026-08-01T10:00:00Z"
            ),
            "typeContrat": "CDI",
            "entreprise": {
                "nom": "Example",
            },
            "lieuTravail": {
                "libelle": "75 - Paris",
            },
            "salaire": {
                "min": 80000,
                "max": 100000,
            },
            "competences": [
                {
                    "libelle": (
                        "Gouvernance SI"
                    ),
                },
                {
                    "libelle": "COBIT",
                },
            ],
            "langues": [
                {
                    "libelle": "Anglais",
                }
            ],
        }

        job = self.mapper.map(item)

        self.assertIsNotNone(job)
        self.assertEqual(
            job.external_id,
            "123ABC",
        )
        self.assertEqual(
            job.title,
            "Directeur SI",
        )
        self.assertEqual(
            job.company,
            "Example",
        )
        self.assertEqual(
            job.salary_min,
            80000,
        )
        self.assertEqual(
            job.salary_max,
            100000,
        )
        self.assertEqual(
            job.remote_type,
            "hybrid",
        )
        self.assertIn(
            "COBIT",
            job.skills,
        )

    def test_invalid_offer_is_ignored(self):
        self.assertIsNone(
            self.mapper.map(
                {
                    "id": "123",
                }
            )
        )


if __name__ == "__main__":
    unittest.main()