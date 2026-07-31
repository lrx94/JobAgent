from __future__ import annotations

from src.domain import CV
from src.matching.skill_classifier import SkillClassifier

from .education_parser import EducationParser
from .experience_parser import ExperienceParser
from .language_parser import LanguageParser
from .normalizers import SkillNormalizer, TextNormalizer
from .section_parser import SectionParser
from .skills import SkillParser


class CVBuilder:
    """
    Construit un objet CV à partir du texte extrait d'un document.

    Le builder orchestre les différents composants spécialisés :

    - SectionParser ;
    - ExperienceParser ;
    - EducationParser ;
    - LanguageParser ;
    - SkillParser ;
    - SkillClassifier.

    Il ne porte pas directement la logique métier propre
    à chaque type de section.
    """

    # TODO(V3.x)
    # Ce marqueur est spécifique au CV de test.
    # Il devra être remplacé par un LayoutAnalyzer capable
    # de reconstruire correctement les colonnes du PDF.
    INTEREST_STOP = {
        "Ludovic ROUMIEUX",
    }

    def __init__(self) -> None:
        self.section_parser = SectionParser()
        self.experience_parser = ExperienceParser()
        self.education_parser = EducationParser()
        self.language_parser = LanguageParser()
        self.skill_parser = SkillParser()
        self.skill_classifier = SkillClassifier()

    def build(self, text: str) -> CV:
        """
        Construit un CV structuré depuis un texte brut.
        """

        sections = self.section_parser.parse(text)

        cv = CV()

        self._build_summary(cv, sections)
        self._build_experiences(cv, sections)
        self._build_education(cv, sections)
        self._build_languages(cv, sections)
        self._build_skills(cv, sections)
        self._build_interests(cv, sections)

        return cv

    def _build_summary(
        self,
        cv: CV,
        sections: dict[str, str],
    ) -> None:
        """
        Construit et normalise le résumé professionnel.
        """

        summary = sections.get("summary", "").strip()

        cv.summary = TextNormalizer.normalize(summary)

    def _build_experiences(
        self,
        cv: CV,
        sections: dict[str, str],
    ) -> None:
        """
        Construit les expériences professionnelles.
        """

        cv.experiences = self.experience_parser.parse(
            sections.get("experiences", "")
        )

    def _build_education(
        self,
        cv: CV,
        sections: dict[str, str],
    ) -> None:
        """
        Construit les formations et les certifications.
        """

        education_result = self.education_parser.parse(
            sections.get("education", "")
        )

        cv.education = education_result.education
        cv.certifications = education_result.certifications

    def _build_languages(
        self,
        cv: CV,
        sections: dict[str, str],
    ) -> None:
        """
        Construit les langues.
        """

        cv.languages = self.language_parser.parse(
            sections.get("languages", "")
        )

    def _build_skills(
        self,
        cv: CV,
        sections: dict[str, str],
    ) -> None:
        """
        Construit, normalise et classifie les compétences.

        Pipeline :

        texte brut
            -> SkillParser
            -> TextNormalizer
            -> SkillNormalizer
            -> SkillClassifier
            -> objets Skill enrichis
        """

        cv.skills = self.skill_parser.parse(
            sections.get("skills", "")
        )

        for skill in cv.skills:
            skill.name = SkillNormalizer.normalize(
                TextNormalizer.normalize(skill.name)
            )

        cv.skills = self.skill_classifier.classify_many(cv.skills)

    def _build_interests(
        self,
        cv: CV,
        sections: dict[str, str],
    ) -> None:
        """
        Construit les centres d'intérêt.
        """

        interests: list[str] = []

        for raw_line in sections.get("interests", "").splitlines():
            line = raw_line.strip()

            if not line:
                continue

            if line in self.INTEREST_STOP:
                break

            interests.append(line)

        cv.interests = interests