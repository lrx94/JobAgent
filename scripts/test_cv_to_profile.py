from __future__ import annotations

from pathlib import Path

from src.ai.skill_extractor import SkillExtractor
from src.career import (
    CareerProfileBuilder,
    RoleDetector,
)
from src.cv.cv_parser import CVParser


PROJECT_ROOT = Path(__file__).resolve().parent.parent

CV_PATH = (
    PROJECT_ROOT
    / "profiles"
    / "data_engineer"
    / "cv.pdf"
)


def section(title: str) -> None:
    print()
    print("=" * 88)
    print(title)
    print("=" * 88)


def main() -> None:
    section("LECTURE DU CV")

    parser = CVParser()
    cv_text = parser.extract_text(
        str(CV_PATH)
    )

    print("CV :", CV_PATH)
    print("Caractères :", len(cv_text))

    section("COMPÉTENCES")

    extractor = SkillExtractor()
    skills = extractor.extract(cv_text)

    for skill in skills:
        print("✓", skill)

    section("ANALYSE MÉTIER")

    detector = RoleDetector()

    analysis = detector.analyze(
        cv_text=cv_text,
        extracted_skills=skills,
        limit=5,
    )

    print("Titre suggéré :", analysis.suggested_title)
    print("Séniorité     :", analysis.seniority)

    for index, suggestion in enumerate(
        analysis.role_suggestions,
        start=1,
    ):
        print()
        print(
            f"{index}. {suggestion.label} "
            f"— {suggestion.score:.2f}%"
        )
        print(
            "   Intitulés trouvés :",
            list(suggestion.matched_aliases),
        )
        print(
            "   Compétences liées :",
            list(suggestion.matched_skills),
        )
        print(
            "   Compétences cœur absentes :",
            list(
                suggestion.missing_core_skills
            ),
        )
        print(
            "   Providers conseillés :",
            list(
                suggestion.preferred_providers
            ),
        )

    section("PROFIL GÉNÉRÉ")

    builder = CareerProfileBuilder()

    generated = builder.build(
        analysis=analysis,
        locations=["Remote"],
        remote=True,
    )

    profile = generated.profile

    print("Nom          :", profile.name)
    print("Mots-clés    :", profile.keywords)
    print("Localisations:", profile.locations)
    print("Remote       :", profile.remote)


if __name__ == "__main__":
    main()