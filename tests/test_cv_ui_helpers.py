from __future__ import annotations

import unittest
from datetime import datetime, timezone
from pathlib import Path

from src.cvs.models import CVDocument
from src.cvs.profile_cv_models import (
    ProfileCVAssociation,
)
from src.cvs.ui_helpers import (
    association_by_cv_id,
    document_by_id,
    document_label,
    format_size,
    primary_cv_id,
    profile_ids_for_cv,
)


class TestCVUIHelpers(unittest.TestCase):

    def create_document(
        self,
        cv_id: str = "cv-123",
        title: str = "CV DSI",
    ) -> CVDocument:
        now = datetime.now(
            timezone.utc
        )

        return CVDocument(
            cv_id=cv_id,
            user_id="user-123",
            title=title,
            original_filename="cv_dsi.pdf",
            content_type="application/pdf",
            size_bytes=2048,
            checksum="a" * 64,
            document_path=Path(
                f"/tmp/{cv_id}/document.pdf"
            ),
            created_at=now,
            updated_at=now,
        )

    def create_association(
        self,
        profile_id: str = "dsi_cio",
        cv_id: str = "cv-123",
        is_primary: bool = False,
    ) -> ProfileCVAssociation:
        now = datetime.now(
            timezone.utc
        )

        return ProfileCVAssociation(
            user_id="user-123",
            profile_id=profile_id,
            cv_id=cv_id,
            is_primary=is_primary,
            created_at=now,
            updated_at=now,
        )

    def test_format_bytes(self):
        self.assertEqual(
            format_size(500),
            "500 o",
        )

    def test_format_kilobytes(self):
        self.assertEqual(
            format_size(2048),
            "2.0 Ko",
        )

    def test_format_megabytes(self):
        self.assertEqual(
            format_size(
                5 * 1024 * 1024
            ),
            "5.0 Mo",
        )

    def test_document_label(self):
        document = self.create_document()

        self.assertEqual(
            document_label(document),
            "CV DSI — cv_dsi.pdf",
        )

    def test_document_by_id(self):
        document = self.create_document()

        result = document_by_id(
            [document]
        )

        self.assertIs(
            result["cv-123"],
            document,
        )

    def test_association_by_cv_id(self):
        association = (
            self.create_association()
        )

        result = association_by_cv_id(
            [association]
        )

        self.assertIs(
            result["cv-123"],
            association,
        )

    def test_primary_cv_id(self):
        associations = [
            self.create_association(
                cv_id="cv-1",
                is_primary=False,
            ),
            self.create_association(
                cv_id="cv-2",
                is_primary=True,
            ),
        ]

        self.assertEqual(
            primary_cv_id(associations),
            "cv-2",
        )

    def test_primary_cv_id_returns_none(self):
        self.assertIsNone(
            primary_cv_id([])
        )

    def test_profile_ids_for_cv(self):
        associations = [
            self.create_association(
                profile_id="dsi_cio",
                cv_id="cv-1",
            ),
            self.create_association(
                profile_id=(
                    "directeur_programme"
                ),
                cv_id="cv-1",
            ),
            self.create_association(
                profile_id="data_engineer",
                cv_id="cv-2",
            ),
        ]

        self.assertEqual(
            profile_ids_for_cv(
                associations,
                "cv-1",
            ),
            (
                "directeur_programme",
                "dsi_cio",
            ),
        )


if __name__ == "__main__":
    unittest.main()