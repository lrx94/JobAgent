from __future__ import annotations

import io
import json
import tempfile
import unittest
from pathlib import Path

from src.auth.models import (
    CurrentUser,
    Role,
)
from src.auth.user_context import (
    UserContext,
)
from src.cvs.exceptions import (
    CVNotFoundError,
    DuplicateCVError,
    InvalidCVError,
)
from src.cvs.repository import (
    CVRepository,
)


PDF_CONTENT = (
    b"%PDF-1.4\n"
    b"JobAgent test CV\n"
    b"%%EOF\n"
)


class TestCVRepository(unittest.TestCase):

    def setUp(self) -> None:
        self.temporary_directory = (
            tempfile.TemporaryDirectory()
        )

        self.storage_root = (
            Path(
                self.temporary_directory.name
            )
            / "users"
        )

    def tearDown(self) -> None:
        self.temporary_directory.cleanup()

    def create_context(
        self,
        user_id: str = "user-123",
        email: str = "first@example.com",
        authenticated: bool = True,
        authorized: bool = True,
    ) -> UserContext:
        return UserContext(
            current_user=CurrentUser(
                user_id=user_id,
                subject=f"subject-{user_id}",
                email=email,
                display_name=user_id,
                authenticated=authenticated,
                authorized=authorized,
                roles=(
                    Role.USER,
                ),
            )
        )

    def create_repository(
        self,
        user_id: str = "user-123",
        email: str = "first@example.com",
    ) -> CVRepository:
        return CVRepository(
            user_context=self.create_context(
                user_id=user_id,
                email=email,
            ),
            storage_root=self.storage_root,
        )

    def test_import_bytes_creates_files(self):
        repository = self.create_repository()

        document = repository.import_bytes(
            content=PDF_CONTENT,
            title="CV DSI",
            original_filename="cv_dsi.pdf",
        )

        self.assertTrue(
            document.document_path.is_file()
        )

        metadata_path = (
            repository.paths
            .cv_metadata_file(
                document.cv_id
            )
        )

        self.assertTrue(
            metadata_path.is_file()
        )

    def test_metadata_contains_user_id(self):
        repository = self.create_repository()

        document = repository.import_bytes(
            content=PDF_CONTENT,
            title="CV DSI",
            original_filename="cv_dsi.pdf",
        )

        metadata_path = (
            repository.paths
            .cv_metadata_file(
                document.cv_id
            )
        )

        data = json.loads(
            metadata_path.read_text(
                encoding="utf-8"
            )
        )

        self.assertEqual(
            data["user_id"],
            "user-123",
        )

    def test_get_returns_document(self):
        repository = self.create_repository()

        created = repository.import_bytes(
            content=PDF_CONTENT,
            title="CV DSI",
            original_filename="cv_dsi.pdf",
        )

        loaded = repository.get(
            created.cv_id
        )

        self.assertEqual(
            loaded.cv_id,
            created.cv_id,
        )

        self.assertEqual(
            loaded.checksum,
            created.checksum,
        )

    def test_list_all_returns_user_documents(
        self,
    ):
        repository = self.create_repository()

        repository.import_bytes(
            content=PDF_CONTENT,
            title="CV DSI",
            original_filename="cv_dsi.pdf",
        )

        repository.import_bytes(
            content=(
                PDF_CONTENT
                + b"second"
            ),
            title="CV Data",
            original_filename="cv_data.pdf",
        )

        documents = repository.list_all()

        self.assertEqual(
            len(documents),
            2,
        )

    def test_duplicate_is_rejected(self):
        repository = self.create_repository()

        repository.import_bytes(
            content=PDF_CONTENT,
            title="CV DSI",
            original_filename="cv_dsi.pdf",
        )

        with self.assertRaises(
            DuplicateCVError
        ):
            repository.import_bytes(
                content=PDF_CONTENT,
                title="Copie CV DSI",
                original_filename="copy.pdf",
            )

    def test_duplicate_can_be_allowed(self):
        repository = self.create_repository()

        first = repository.import_bytes(
            content=PDF_CONTENT,
            title="CV DSI",
            original_filename="cv_dsi.pdf",
        )

        second = repository.import_bytes(
            content=PDF_CONTENT,
            title="CV DSI Copie",
            original_filename="copy.pdf",
            reject_duplicates=False,
        )

        self.assertNotEqual(
            first.cv_id,
            second.cv_id,
        )

        self.assertEqual(
            first.checksum,
            second.checksum,
        )

    def test_find_by_checksum(self):
        repository = self.create_repository()

        created = repository.import_bytes(
            content=PDF_CONTENT,
            title="CV DSI",
            original_filename="cv_dsi.pdf",
        )

        found = repository.find_by_checksum(
            created.checksum
        )

        self.assertIsNotNone(found)

        self.assertEqual(
            found.cv_id,
            created.cv_id,
        )

    def test_rename_updates_title(self):
        repository = self.create_repository()

        created = repository.import_bytes(
            content=PDF_CONTENT,
            title="CV DSI",
            original_filename="cv_dsi.pdf",
        )

        renamed = repository.rename(
            cv_id=created.cv_id,
            title="CV CIO",
        )

        self.assertEqual(
            renamed.title,
            "CV CIO",
        )

        reloaded = repository.get(
            created.cv_id
        )

        self.assertEqual(
            reloaded.title,
            "CV CIO",
        )

    def test_delete_removes_directory(self):
        repository = self.create_repository()

        document = repository.import_bytes(
            content=PDF_CONTENT,
            title="CV DSI",
            original_filename="cv_dsi.pdf",
        )

        directory = repository.paths.cv_directory(
            document.cv_id
        )

        repository.delete(
            document.cv_id
        )

        self.assertFalse(
            directory.exists()
        )

        with self.assertRaises(
            CVNotFoundError
        ):
            repository.get(
                document.cv_id
            )

    def test_read_content_returns_pdf(self):
        repository = self.create_repository()

        document = repository.import_bytes(
            content=PDF_CONTENT,
            title="CV DSI",
            original_filename="cv_dsi.pdf",
        )

        self.assertEqual(
            repository.read_content(
                document.cv_id
            ),
            PDF_CONTENT,
        )

    def test_empty_content_is_rejected(self):
        repository = self.create_repository()

        with self.assertRaises(
            InvalidCVError
        ):
            repository.import_bytes(
                content=b"",
                title="CV vide",
                original_filename="empty.pdf",
            )

    def test_non_pdf_content_is_rejected(self):
        repository = self.create_repository()

        with self.assertRaises(
            InvalidCVError
        ):
            repository.import_bytes(
                content=b"not a pdf",
                title="Faux CV",
                original_filename="fake.pdf",
            )

    def test_non_pdf_extension_is_rejected(self):
        repository = self.create_repository()

        with self.assertRaises(
            InvalidCVError
        ):
            repository.import_bytes(
                content=PDF_CONTENT,
                title="CV texte",
                original_filename="cv.txt",
            )

    def test_import_stream(self):
        repository = self.create_repository()

        document = repository.import_stream(
            stream=io.BytesIO(
                PDF_CONTENT
            ),
            title="CV Stream",
            original_filename="stream.pdf",
        )

        self.assertTrue(
            repository.exists(
                document.cv_id
            )
        )

    def test_import_file(self):
        repository = self.create_repository()

        source = (
            Path(
                self.temporary_directory.name
            )
            / "source.pdf"
        )

        source.write_bytes(
            PDF_CONTENT
        )

        document = repository.import_file(
            source_path=source,
            title="CV fichier",
        )

        self.assertEqual(
            document.original_filename,
            "source.pdf",
        )

    def test_two_users_are_isolated(self):
        first = self.create_repository(
            user_id="user-123",
            email="first@example.com",
        )

        second = self.create_repository(
            user_id="user-456",
            email="second@example.com",
        )

        first_document = first.import_bytes(
            content=PDF_CONTENT,
            title="CV partagé",
            original_filename="cv.pdf",
        )

        second_document = second.import_bytes(
            content=PDF_CONTENT,
            title="CV partagé",
            original_filename="cv.pdf",
        )

        self.assertNotEqual(
            first_document.cv_id,
            second_document.cv_id,
        )

        self.assertEqual(
            len(first.list_all()),
            1,
        )

        self.assertEqual(
            len(second.list_all()),
            1,
        )

        with self.assertRaises(
            CVNotFoundError
        ):
            first.get(
                second_document.cv_id
            )

    def test_unauthorized_context_is_rejected(
        self,
    ):
        context = self.create_context(
            authorized=False
        )

        with self.assertRaises(
            Exception
        ):
            CVRepository(
                user_context=context,
                storage_root=self.storage_root,
            )

    def test_invalid_context_type_is_rejected(
        self,
    ):
        with self.assertRaises(
            TypeError
        ):
            CVRepository(
                user_context=object(),
                storage_root=self.storage_root,
            )

    def test_metadata_with_foreign_user_is_hidden(
        self,
    ):
        repository = self.create_repository()

        document = repository.import_bytes(
            content=PDF_CONTENT,
            title="CV DSI",
            original_filename="cv.pdf",
        )

        metadata_path = (
            repository.paths
            .cv_metadata_file(
                document.cv_id
            )
        )

        data = json.loads(
            metadata_path.read_text(
                encoding="utf-8"
            )
        )

        data["user_id"] = "other-user"

        metadata_path.write_text(
            json.dumps(data),
            encoding="utf-8",
        )

        with self.assertRaises(
            CVNotFoundError
        ):
            repository.get(
                document.cv_id
            )


if __name__ == "__main__":
    unittest.main()