from __future__ import annotations

from src.domain import CV
from .skills import SkillParser
from .education_parser import EducationParser
from .experience_parser import ExperienceParser
from .section_parser import SectionParser


class CVBuilder:

    SKILL_HEADERS = {
        "Domaines d’expertise",
        "Domaines d'expertise",
        "Gouvernance",
        "Management",
        "Méthodologies",
        "Methodologies",
        "Réalisation clés",
        "Realisation clés",
    }

    # TODO(V3.x)
# Ce hack est spécifique au CV de test.
# Il devra être remplacé par un LayoutAnalyzer capable
# de reconstruire correctement les colonnes du PDF.
    INTEREST_STOP = {
    "Ludovic ROUMIEUX",
    }

    def __init__(self) -> None:

        self.section_parser = SectionParser()
        self.experience_parser = ExperienceParser()
        self.education_parser = EducationParser()
        self.skill_parser = SkillParser()

    def build(self, text: str) -> CV:

        sections = self.section_parser.parse(text)

        cv = CV()
    
        #
        # Résumé
        #

        cv.summary = sections.get("summary", "").strip()

        #
        # Expériences
        #

        cv.experiences = self.experience_parser.parse(
            sections.get("experiences", "")
        )

        #
        # Formations + Certifications
        #

        education_result = self.education_parser.parse(
            sections.get("education", "")
        )

        cv.education = education_result.education
        cv.certifications = education_result.certifications

        #
        # Langues
        #

        cv.languages = [
            line.strip()
            for line in sections.get("languages", "").splitlines()
            if line.strip()
        ]

        #
        # Compétences
        #
        skills_text = "\n".join(
            line.strip()
            for line in sections.get("skills", "").splitlines()
            if line.strip()
            and line.strip() not in self.SKILL_HEADERS
        )
        cv.skills = self.skill_parser.parse(skills_text)

        #
        # Centres d'intérêt
        #

        interests = []

        for line in sections.get("interests", "").splitlines():

            line = line.strip()

            if not line:
                continue

            if line == "Ludovic ROUMIEUX":
                break

            interests.append(line)

        cv.interests = interests

        return cv