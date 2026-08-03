from __future__ import annotations

import unittest
from dataclasses import FrozenInstanceError
from datetime import datetime, timezone

from src.cvs.profile_cv_models import (
    ProfileCVAssociation,
)


class TestProfileCVAssociation(
    unittest.TestCase
):

    def create_association(
        self,
        **overrides,
    ) -> ProfileCVAssociation:
        now = datetime.now(
            timezone.utc
        )

        values = {
            "user_id": "user-123",
            "profile_id": "dsi_cio",
            "cv_id": "cv-123",
            "is_primary": True,
            "created_at": now,
            "updated_at": now,
        }

        values.update(overrides)

        return ProfileCVAssociation(
            **values
        )

    def test_association_is_created(self):
        association = (
            self.create_association()
        )

        self.assertEqual(
            association.identity,
            "dsi_cio:cv-123",
        )

        self.assertTrue(
            association.is_primary
        )

    def test_association_is_immutable(self):
        association = (
            self.create_association()
        )

        with self.assertRaises(
            FrozenInstanceError
        ):
            association.is_primary = False

    def test_invalid_profile_id_is_rejected(self):
        with self.assertRaises(ValueError):
            self.create_association(
                profile_id="../other"
            )

    def test_invalid_cv_id_is_rejected(self):
        with self.assertRaises(ValueError):
            self.create_association(
                cv_id="cv/other"
            )

    def test_primary_status_returns_new_instance(
        self,
    ):
        association = self.create_association(
            is_primary=False
        )

        updated = (
            association
            .with_primary_status(True)
        )

        self.assertTrue(updated.is_primary)
        self.assertFalse(
            association.is_primary
        )

    def test_to_dict_and_from_dict(self):
        association = (
            self.create_association()
        )

        rebuilt = (
            ProfileCVAssociation
            .from_dict(
                association.to_dict()
            )
        )

        self.assertEqual(
            rebuilt,
            association,
        )


if __name__ == "__main__":
    unittest.main()