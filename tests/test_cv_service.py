from __future__ import annotations

import io
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
    CVAnalysisError,
    CVTooLargeError,
    DuplicateCVError,
)
from src.cvs.repository import (
    CVRepository,
)
from src.cvs.service import (
    CVService,
)


PDF_CONTENT = (
    b"%PDF-1.4\n"
    b"JobAgent CV test\n"
    b"%%EOF\n"
)


class FakeParser:

    def __init__(
        self,
        text: str = (
            "Data Engineer Python SQL Azure"
        ),
        fail: bool = False,
    ) -> None:
        self.text = text
        self.fail = fail
        self.paths: list[str] = []

    def extract_text(
        self,
        path: str,
    ) -> str:
        self.paths.append(path)

        if self.fail:
            raise RuntimeError(
                "parser failure"
            )

        return self.text


class FakeSkillExtractor:

    def __init__(
        self,
        skills=None,
        fail: bool = False,
    ) -> None:
        self.skills = (
            skills
            if skills is not None
            else [
                "Python",
                "SQL",
                "Azure",
            ]
        )
        self.fail = fail
        self.texts: list[str] = []

    def extract(
        self,
        text: str,
    ):
        self.texts.append(text)

        if self.fail:
            raise RuntimeError(
                "extractor failure"
            )

        return self.skills


class TestCVService(unittest.TestCase):

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
    ) -> UserContext:
        return UserContext(
            current_user=CurrentUser(
                user_id=user_id,
                subject=f"subject-{user_id}",
                email=f"{user_id}@example.com",
                display_name=user_id,
                authenticated=True,
                authorized=True,
                roles=(Role.USER,),
            )
        )

    def create_service(
        self,
        user_id: str = "user-123",
        parser=None,
        extractor=None,
        max_size_bytes: int = 1024 * 1024,
    ) -> CVService:
        repository = CVRepository(
            user_context=self.create_context(
                user_id
            ),
            storage_root=self.storage_root,
        )

        return CVService(
            repository=repository,
            parser=parser or FakeParser(),
            skill_extractor=(
                extractor
                or FakeSkillExtractor()
            ),
            max_size_bytes=max_size_bytes,
        )

    def test_import_analyzes_document(self):
        service = self.create_service()

        result = service.import_bytes(
            content=PDF_CONTENT,
            title="CV Data",
            original_filename="cv_data.pdf",
        )

        self.assertTrue(result.analyzed)

        self.assertEqual(
            result.skills,
            (
                "azure",
                "python",
                "sql",
            ),
        )

        self.assertTrue(
            result.document.document_path.is_file()
        )

    def test_analysis_contains_text_metrics(self):
        service = self.create_service(
            parser=FakeParser(
                "Python SQL Azure"
            )
        )

        result = service.import_bytes(
            content=PDF_CONTENT,
            title="CV",
            original_filename="cv.pdf",
        )

        self.assertEqual(
            result.analysis.character_count,
            len("Python SQL Azure"),
        )

        self.assertEqual(
            result.analysis.word_count,
            3,
        )

    def test_import_without_analysis(self):
        service = self.create_service()

        result = service.import_bytes(
            content=PDF_CONTENT,
            title="CV",
            original_filename="cv.pdf",
            analyze=False,
        )

        self.assertFalse(result.analyzed)
        self.assertEqual(result.skills, ())

    def test_duplicate_reject_policy(self):
        service = self.create_service()

        service.import_bytes(
            content=PDF_CONTENT,
            title="Premier",
            original_filename="first.pdf",
            analyze=False,
        )

        with self.assertRaises(
            DuplicateCVError
        ):
            service.import_bytes(
                content=PDF_CONTENT,
                title="Deuxième",
                original_filename="second.pdf",
                duplicate_policy="reject",
                analyze=False,
            )

    def test_duplicate_reuse_policy(self):
        service = self.create_service()

        first = service.import_bytes(
            content=PDF_CONTENT,
            title="Premier",
            original_filename="first.pdf",
            analyze=False,
        )

        second = service.import_bytes(
            content=PDF_CONTENT,
            title="Deuxième",
            original_filename="second.pdf",
            duplicate_policy="reuse",
            analyze=False,
        )

        self.assertEqual(
            second.cv_id,
            first.cv_id,
        )

        self.assertTrue(
            second.duplicate_reused
        )

        self.assertTrue(second.warnings)

    def test_duplicate_allow_policy(self):
        service = self.create_service()

        first = service.import_bytes(
            content=PDF_CONTENT,
            title="Premier",
            original_filename="first.pdf",
            analyze=False,
        )

        second = service.import_bytes(
            content=PDF_CONTENT,
            title="Deuxième",
            original_filename="second.pdf",
            duplicate_policy="allow",
            analyze=False,
        )

        self.assertNotEqual(
            first.cv_id,
            second.cv_id,
        )

    def test_invalid_duplicate_policy(self):
        service = self.create_service()

        with self.assertRaises(ValueError):
            service.import_bytes(
                content=PDF_CONTENT,
                title="CV",
                original_filename="cv.pdf",
                duplicate_policy="invalid",
            )

    def test_size_limit_is_enforced(self):
        service = self.create_service(
            max_size_bytes=5
        )

        with self.assertRaises(
            CVTooLargeError
        ):
            service.import_bytes(
                content=PDF_CONTENT,
                title="CV",
                original_filename="cv.pdf",
            )

    def test_parser_failure_becomes_warning_on_import(
        self,
    ):
        service = self.create_service(
            parser=FakeParser(
                fail=True
            )
        )

        result = service.import_bytes(
            content=PDF_CONTENT,
            title="CV",
            original_filename="cv.pdf",
        )

        self.assertFalse(result.analyzed)
        self.assertTrue(result.warnings)

    def test_explicit_analysis_failure_is_raised(
        self,
    ):
        service = self.create_service(
            parser=FakeParser(
                fail=True
            )
        )

        result = service.import_bytes(
            content=PDF_CONTENT,
            title="CV",
            original_filename="cv.pdf",
            analyze=False,
        )

        with self.assertRaises(
            CVAnalysisError
        ):
            service.analyze(result.cv_id)

    def test_empty_extracted_text_is_rejected(self):
        service = self.create_service(
            parser=FakeParser("")
        )

        result = service.import_bytes(
            content=PDF_CONTENT,
            title="CV",
            original_filename="cv.pdf",
            analyze=False,
        )

        with self.assertRaises(
            CVAnalysisError
        ):
            service.analyze(result.cv_id)

    def test_skill_extractor_failure_is_wrapped(
        self,
    ):
        service = self.create_service(
            extractor=FakeSkillExtractor(
                fail=True
            )
        )

        result = service.import_bytes(
            content=PDF_CONTENT,
            title="CV",
            original_filename="cv.pdf",
            analyze=False,
        )

        with self.assertRaises(
            CVAnalysisError
        ):
            service.analyze(result.cv_id)

    def test_skills_are_normalized_and_deduplicated(
        self,
    ):
        service = self.create_service(
            extractor=FakeSkillExtractor(
                [
                    "Python",
                    " python ",
                    "SQL",
                    "",
                    "Azure",
                ]
            )
        )

        result = service.import_bytes(
            content=PDF_CONTENT,
            title="CV",
            original_filename="cv.pdf",
        )

        self.assertEqual(
            result.skills,
            (
                "azure",
                "python",
                "sql",
            ),
        )

    def test_empty_title_uses_filename(self):
        service = self.create_service()

        result = service.import_bytes(
            content=PDF_CONTENT,
            title="",
            original_filename=(
                "cv_directeur_si.pdf"
            ),
            analyze=False,
        )

        self.assertEqual(
            result.title,
            "cv_directeur_si",
        )

    def test_import_stream(self):
        service = self.create_service()

        result = service.import_stream(
            stream=io.BytesIO(
                PDF_CONTENT
            ),
            title="CV Stream",
            original_filename="stream.pdf",
            analyze=False,
        )

        self.assertEqual(
            result.title,
            "CV Stream",
        )

    def test_import_file(self):
        service = self.create_service()

        source = (
            Path(
                self.temporary_directory.name
            )
            / "source.pdf"
        )

        source.write_bytes(PDF_CONTENT)

        result = service.import_file(
            source_path=source,
            analyze=False,
        )

        self.assertEqual(
            result.document.original_filename,
            "source.pdf",
        )

    def test_list_get_rename_read_and_delete(self):
        service = self.create_service()

        result = service.import_bytes(
            content=PDF_CONTENT,
            title="CV Initial",
            original_filename="cv.pdf",
            analyze=False,
        )

        self.assertEqual(
            len(service.list_cvs()),
            1,
        )

        self.assertEqual(
            service.get_cv(
                result.cv_id
            ).title,
            "CV Initial",
        )

        renamed = service.rename_cv(
            result.cv_id,
            "CV Renommé",
        )

        self.assertEqual(
            renamed.title,
            "CV Renommé",
        )

        self.assertEqual(
            service.read_cv(
                result.cv_id
            ),
            PDF_CONTENT,
        )

        service.delete_cv(
            result.cv_id
        )

        self.assertEqual(
            service.list_cvs(),
            [],
        )

    def test_two_services_are_user_isolated(self):
        first = self.create_service(
            user_id="user-a"
        )

        second = self.create_service(
            user_id="user-b"
        )

        first.import_bytes(
            content=PDF_CONTENT,
            title="CV A",
            original_filename="cv.pdf",
            analyze=False,
        )

        self.assertEqual(
            len(first.list_cvs()),
            1,
        )

        self.assertEqual(
            len(second.list_cvs()),
            0,
        )


if __name__ == "__main__":
    unittest.main()