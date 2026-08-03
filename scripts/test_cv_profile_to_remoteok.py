from __future__ import annotations

import re
import unicodedata
from pathlib import Path

from src.ai.skill_extractor import SkillExtractor
from src.career import (
    CareerProfileBuilder,
    RoleDetector,
)
from src.career.job_role_catalog import JOB_ROLE_CATALOG
from src.cv.cv_parser import CVParser
from src.services.job_service import JobService


PROJECT_ROOT = Path(__file__).resolve().parent.parent

CV_PATH = (
    PROJECT_ROOT
    / "profiles"
    / "data_engineer"
    / "cv.pdf"
)

MAX_RESULTS_DISPLAYED = 20
MINIMUM_SKILL_MATCHES = 2


def section(title: str) -> None:
    print()
    print("=" * 88)
    print(title)
    print("=" * 88)


def normalize_text(value: str) -> str:
    """
    Uniformise un texte pour les comparaisons métier.

    - minuscules ;
    - suppression des accents ;
    - espaces normalisés.
    """

    text = str(value or "").strip().casefold()

    decomposed = unicodedata.normalize(
        "NFKD",
        text,
    )

    without_accents = "".join(
        character
        for character in decomposed
        if not unicodedata.combining(character)
    )

    return " ".join(
        without_accents.split()
    )


def normalize_skills(
    values: list[str] | tuple[str, ...] | None,
) -> list[str]:
    """
    Nettoie et déduplique une liste de compétences.
    """

    normalized: list[str] = []
    seen: set[str] = set()

    for value in values or []:
        cleaned = normalize_text(value)

        if not cleaned:
            continue

        if cleaned in seen:
            continue

        seen.add(cleaned)
        normalized.append(cleaned)

    return normalized


def contains_phrase(
    text: str,
    phrase: str,
) -> bool:
    """
    Recherche une expression complète dans un texte.
    """

    normalized_text = normalize_text(text)
    normalized_phrase = normalize_text(phrase)

    if not normalized_phrase:
        return False

    pattern = (
        r"(?<!\w)"
        + re.escape(normalized_phrase)
        + r"(?!\w)"
    )

    return (
        re.search(
            pattern,
            normalized_text,
        )
        is not None
    )


def get_selected_role_terms(
    role_id: str | None,
) -> list[str]:
    """
    Retourne le libellé et les alias du métier sélectionné.
    """

    if not role_id:
        return []

    for role in JOB_ROLE_CATALOG:
        if role.role_id == role_id:
            return [
                role.label,
                *role.aliases,
            ]

    return []


def title_matches_role(
    job_title: str,
    role_terms: list[str],
) -> bool:
    """
    Indique si le titre de l'annonce correspond explicitement
    au métier sélectionné ou à l'un de ses synonymes.
    """

    return any(
        contains_phrase(
            text=job_title,
            phrase=term,
        )
        for term in role_terms
    )


def filter_relevant_jobs(
    jobs: list,
    role_terms: list[str],
) -> list:
    """
    Conserve une offre lorsque :

    - son titre correspond au métier sélectionné ;
    - ou elle possède au moins deux compétences communes.

    `match_details` seul n'est jamais considéré comme un signal
    suffisant, car ce dictionnaire peut être rempli même lorsque
    la correspondance métier est faible.
    """

    relevant_jobs = []

    for job in jobs:
        matched_skills = normalize_skills(
            getattr(
                job,
                "matched_skills",
                [],
            )
        )

        role_title_match = title_matches_role(
            job_title=getattr(
                job,
                "title",
                "",
            ),
            role_terms=role_terms,
        )

        enough_skill_matches = (
            len(matched_skills)
            >= MINIMUM_SKILL_MATCHES
        )

        if (
            job.score > 0
            and (
                role_title_match
                or enough_skill_matches
            )
        ):
            relevant_jobs.append(job)

    return relevant_jobs


def display_diagnostic(
    jobs: list,
    role_terms: list[str],
) -> None:
    """
    Affiche les critères utilisés pour chaque annonce.
    """

    section("DIAGNOSTIC DES OFFRES")

    if not jobs:
        print("Aucune offre reçue.")
        return

    for index, job in enumerate(
        jobs,
        start=1,
    ):
        matched_skills = normalize_skills(
            getattr(
                job,
                "matched_skills",
                [],
            )
        )

        role_title_match = title_matches_role(
            job_title=getattr(
                job,
                "title",
                "",
            ),
            role_terms=role_terms,
        )

        accepted = (
            job.score > 0
            and (
                role_title_match
                or len(matched_skills)
                >= MINIMUM_SKILL_MATCHES
            )
        )

        print()
        print("-" * 88)
        print(
            f"{index}. "
            f"{getattr(job, 'title', '')}"
        )
        print(
            "Entreprise            :",
            getattr(job, "company", ""),
        )
        print(
            "Score                 :",
            getattr(job, "score", 0),
        )
        print(
            "Compétences communes  :",
            matched_skills or "Aucune",
        )
        print(
            "Correspondance métier :",
            role_title_match,
        )
        print(
            "Décision               :",
            "RETENUE"
            if accepted
            else "REJETÉE",
        )


def display_results(
    jobs: list,
) -> None:
    """
    Affiche les offres finalement retenues.
    """

    section("RÉSULTATS")

    if not jobs:
        print(
            "Aucune offre RemoteOK ne correspond suffisamment "
            "au métier proposé et aux compétences du CV."
        )
        print()
        print(
            "Ce résultat est cohérent : RemoteOK n'est pas "
            "la source prioritaire pour un profil de direction "
            "de projet, de programme ou de DSI."
        )
        return

    print(
        f"{len(jobs)} offre(s) pertinente(s)"
    )

    for index, job in enumerate(
        jobs[:MAX_RESULTS_DISPLAYED],
        start=1,
    ):
        print()
        print("-" * 88)
        print(
            f"{index}. "
            f"{job.score:.1f} — "
            f"{job.title}"
        )
        print("Entreprise :", job.company)
        print("Source     :", job.source)
        print(
            "Compétences:",
            normalize_skills(
                job.matched_skills
            ),
        )
        print("URL        :", job.url)


def main() -> None:
    parser = CVParser()
    extractor = SkillExtractor()
    detector = RoleDetector()
    builder = CareerProfileBuilder()

    section("ANALYSE DU CV")

    cv_text = parser.extract_text(
        str(CV_PATH)
    )

    skills = extractor.extract(
        cv_text
    )

    analysis = detector.analyze(
        cv_text=cv_text,
        extracted_skills=skills,
        limit=5,
    )

    print(
        "Métier proposé :",
        analysis.suggested_title,
    )
    print(
        "Séniorité      :",
        analysis.seniority,
    )
    print(
        "Compétences    :",
        list(
            analysis.extracted_skills
        ),
    )

    section("PROPOSITIONS DE MÉTIERS")

    for suggestion in (
        analysis.role_suggestions
    ):
        print(
            f"- {suggestion.label}: "
            f"{suggestion.score:.2f}%"
        )

    generated = builder.build(
        analysis=analysis,
        locations=["Remote"],
        remote=True,
    )

    profile = generated.profile
    selected_role = (
        generated.selected_role
    )

    role_terms = get_selected_role_terms(
        selected_role.role_id
        if selected_role is not None
        else None
    )

    section("PROFIL DE RECHERCHE")

    print("Nom       :", profile.name)
    print(
        "Mots-clés :",
        profile.keywords,
    )
    print(
        "Intitulés métier :",
        role_terms,
    )

    if selected_role is not None:
        print(
            "Providers recommandés :",
            list(
                selected_role
                .preferred_providers
            ),
        )

    section("RECHERCHE REMOTEOK")

    service = JobService(
        persistence_enabled=False,
    )

    jobs = service.search(
        profile
    )

    print(
        f"{len(jobs)} offre(s) analysée(s)"
    )

    display_diagnostic(
        jobs=jobs,
        role_terms=role_terms,
    )

    relevant_jobs = filter_relevant_jobs(
        jobs=jobs,
        role_terms=role_terms,
    )

    print()
    print(
        "Règle : titre métier compatible "
        f"OU au moins {MINIMUM_SKILL_MATCHES} "
        "compétences communes."
    )

    display_results(
        relevant_jobs
    )


if __name__ == "__main__":
    main()