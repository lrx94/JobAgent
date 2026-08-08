from __future__ import annotations

import unittest

from src.domain import Job
from src.learning import (
    JobLearningObservationExtractor,
)


class TestJobLearningObservationExtractor(
    unittest.TestCase
):

    def setUp(self) -> None:
        self.extractor = (
            JobLearningObservationExtractor()
        )

    @staticmethod
    def create_job() -> Job:
        return Job(
            title="Data Engineer Microsoft Fabric",
            company="Example",
            location="Paris",
            description=(
                "Expérience requise sur Microsoft Fabric, "
                "Azure OpenAI et LangGraph."
            ),
            source="France Travail",
            external_id="ft-1",
            skills=[
                "Microsoft Fabric",
                "FinOps",
            ],
        )

    def test_extracts_provider_tags(
        self,
    ):
        observations = (
            self.extractor.extract_job(
                self.create_job()
            )
        )

        terms = {
            item.term
            for item in observations
        }

        self.assertIn(
            "Microsoft Fabric",
            terms,
        )

        self.assertIn(
            "FinOps",
            terms,
        )

    def test_keeps_source_and_reference(
        self,
    ):
        observations = (
            self.extractor.extract_job(
                self.create_job()
            )
        )

        self.assertTrue(
            all(
                item.source
                == "france travail"
                for item in observations
            )
        )

        self.assertTrue(
            all(
                item.reference_id
                == "ft-1"
                for item in observations
            )
        )

    def test_duplicate_term_is_observed_once_per_job(
        self,
    ):
        observations = (
            self.extractor.extract_job(
                self.create_job()
            )
        )

        normalized = [
            item.term.casefold()
            for item in observations
        ]

        self.assertEqual(
            normalized.count(
                "microsoft fabric"
            ),
            1,
        )

    def test_invalid_job_is_rejected(
        self,
    ):
        with self.assertRaises(TypeError):
            self.extractor.extract_job(
                object()
            )

    def test_apostrophes_do_not_create_truncated_candidates(self):
        job = Job(
            title="Responsable des systèmes d'information",
            company="Example",
            location="Paris",
            description=(
                "Esprit d'analyse requis. Participer à l'élaboration "
                "de la gouvernance SI."
            ),
            source="France Travail",
            external_id="ft-apostrophes",
        )

        terms = {
            item.term
            for item in self.extractor.extract_job(job)
        }

        self.assertNotIn("Systèmes d", terms)
        self.assertNotIn("Esprit d", terms)
        self.assertNotIn("Participer à l", terms)

    def test_extraction_does_not_cross_sentence_boundaries(self):
        job = Job(
            title="Ingénieur plateforme",
            company="Example",
            location="Paris",
            description=(
                "Description du poste. Expérience Node.js et .NET. "
                "Maîtrise de C++ et C#."
            ),
            source="France Travail",
            external_id="ft-boundaries",
        )

        terms = {
            item.term
            for item in self.extractor.extract_job(job)
        }

        self.assertTrue(
            all("poste." not in term for term in terms)
        )
        self.assertTrue(
            any("Node.js" in term for term in terms)
        )
        self.assertTrue(
            any(".NET" in term for term in terms)
        )
        self.assertTrue(
            any("C++" in term for term in terms)
        )
        self.assertTrue(
            any("C#" in term for term in terms)
        )

    def test_extracts_business_term_without_sentence_prefix(self):
        job = Job(
            title="Contrôleur de gestion",
            company="Example",
            location="Paris",
            description=(
                "Vous avez une première expérience en gestion de projet."
            ),
            source="France Travail",
            external_id="ft-business-term",
        )

        terms = {
            item.term.casefold()
            for item in self.extractor.extract_job(job)
        }

        self.assertIn("gestion de projet", terms)
        self.assertNotIn("vous avez une", terms)
        self.assertNotIn("une première expérience", terms)

    def test_extracts_cybersecurity_without_sentence_prefix(self):
        job = Job(
            title="Consultant sécurité",
            company="Example",
            location="Paris",
            description=(
                "Vous disposez d'une expertise en cybersécurité."
            ),
            source="France Travail",
            external_id="ft-cybersecurity",
        )

        terms = {
            item.term.casefold()
            for item in self.extractor.extract_job(job)
        }

        self.assertIn("cybersécurité", terms)
        self.assertNotIn("vous disposez d'une", terms)

    def test_extracts_coordinated_nouns_without_apostrophe_fragment(self):
        job = Job(
            title="Manager",
            company="Example",
            location="Paris",
            description="Esprit d'analyse et de synthèse.",
            source="France Travail",
            external_id="ft-soft-skills",
        )

        terms = {
            item.term.casefold()
            for item in self.extractor.extract_job(job)
        }

        self.assertIn("analyse", terms)
        self.assertIn("synthèse", terms)
        self.assertNotIn("esprit d", terms)

    def test_extracts_soft_skill_from_complete_hr_sentence(self):
        job = Job(
            title="Manager",
            company="Example",
            location="Paris",
            description="Vous avez une très bonne écoute.",
            source="France Travail",
            external_id="ft-soft-skill",
        )

        terms = {
            item.term.casefold()
            for item in self.extractor.extract_job(job)
        }

        self.assertIn("écoute", terms)
        self.assertNotIn("vous avez une", terms)
        self.assertNotIn("très bonne", terms)

    def test_extracts_coordinated_business_groups(self):
        job = Job(
            title="Manager",
            company="Example",
            location="Paris",
            description=(
                "Vous avez une expérience confirmée dans "
                "l'encadrement de managers et la gestion "
                "d'équipes pluridisciplinaires."
            ),
            source="France Travail",
            external_id="ft-management",
        )

        terms = {
            item.term.casefold()
            for item in self.extractor.extract_job(job)
        }

        self.assertIn("encadrement de managers", terms)
        self.assertIn("gestion d'équipes pluridisciplinaires", terms)
        self.assertNotIn("expérience confirmée dans", terms)

    def test_extracts_reliable_optional_business_complement(self):
        job = Job(
            title="Chef de projet",
            company="Example",
            location="Paris",
            description=(
                "Vous avez une première expérience en gestion de projet "
                "et idéalement de l'écosystème numérique."
            ),
            source="France Travail",
            external_id="ft-ecosystem",
        )

        terms = {
            item.term.casefold()
            for item in self.extractor.extract_job(job)
        }

        self.assertIn("gestion de projet", terms)
        self.assertIn("écosystème numérique", terms)

    def test_contextual_term_survives_wrapped_source_line(self):
        job = Job(
            title="Chef de projet",
            company="Example",
            location="Paris",
            description="Expérience en gestion de\nprojet requise.",
            source="France Travail",
            external_id="ft-wrapped-line",
        )

        terms = {
            item.term.casefold()
            for item in self.extractor.extract_job(job)
        }

        self.assertIn("gestion de projet", terms)


if __name__ == "__main__":
    unittest.main()
