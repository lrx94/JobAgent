from __future__ import annotations

import unittest
from dataclasses import FrozenInstanceError
from datetime import datetime, timezone
from pathlib import Path

from src.cvs.models import (
    CVDocument,
)


class TestCVDocument(unittest.TestCase):

    def create_document(
        self,
        **overrides,
    ) -> CVDocument:
        now = datetime.now(
            timezone.utc
        )

        values = {
            "cv_id": "cv-123",
            "user_id": "user-123",
            "title": "CV DSI",
            "original_filename": "cv_dsi.pdf",
            "content_type": "application/pdf",
            "size_bytes": 1024,
            "checksum": "a" * 64,
            "document_path": Path(
                "/tmp/cv-123/document.pdf"
            ),
            "created_at": now,
            "updated_at": now,
        }

        values.update(
            overrides
        )

        return CVDocument(
            **values
        )

    def test_document_is_created(self):
        document = self.create_document()

        self.assertEqual(
            document.cv_id,
            "cv-123",
        )

        self.assertEqual(
            document.extension,
            ".pdf",
        )

    def test_document_is_immutable(self):
        document = self.create_document()

        with self.assertRaises(
            FrozenInstanceError
        ):
            document.title = "Autre"

    def test_checksum_is_normalized(self):
        document = self.create_document(
            checksum="A" * 64
        )

        self.assertEqual(
            document.checksum,
            "a" * 64,
        )

    def test_invalid_checksum_is_rejected(self):
        with self.assertRaises(
            ValueError
        ):
            self.create_document(
                checksum="invalid"
            )

    def test_empty_title_is_rejected(self):
        with self.assertRaises(
            ValueError
        ):
            self.create_document(
                title=""
            )

    def test_zero_size_is_rejected(self):
        with self.assertRaises(
            ValueError
        ):
            self.create_document(
                size_bytes=0
            )

    def test_rename_creates_new_instance(self):
        document = self.create_document()

        renamed = document.renamed(
            "CV Directeur SI"
        )

        self.assertEqual(
            renamed.title,
            "CV Directeur SI",
        )

        self.assertEqual(
            document.title,
            "CV DSI",
        )

        self.assertIsNot(
            renamed,
            document,
        )

    def test_to_dict_and_from_dict(self):
        document = self.create_document()

        rebuilt = CVDocument.from_dict(
            document.to_dict()
        )

        self.assertEqual(
            rebuilt.cv_id,
            document.cv_id,
        )

        self.assertEqual(
            rebuilt.checksum,
            document.checksum,
        )

        self.assertEqual(
            rebuilt.document_path,
            document.document_path,
        )

    def test_naive_datetime_becomes_utc(self):
        naive = datetime(
            2026,
            8,
            2,
            12,
            0,
            0,
        )

        document = self.create_document(
            created_at=naive,
            updated_at=naive,
        )

        self.assertEqual(
            document.created_at.tzinfo,
            timezone.utc,
        )

    def test_updated_before_created_is_rejected(
        self,
    ):
        with self.assertRaises(
            ValueError
        ):
            self.create_document(
                created_at=datetime(
                    2026,
                    8,
                    2,
                    12,
                    tzinfo=timezone.utc,
                ),
                updated_at=datetime(
                    2026,
                    8,
                    1,
                    12,
                    tzinfo=timezone.utc,
                ),
            )


if __name__ == "__main__":
    unittest.main()