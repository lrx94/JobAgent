from __future__ import annotations

from pathlib import Path

from src.ai.skill_extractor import SkillExtractor
from src.cv.cv_parser import CVParser
from src.profile import Profile
from src.services.job_service import JobService


# ---------------------------------------------------------------------------
# Configuration du test
# ---------------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parent.parent

CV_PATH = PROJECT_ROOT / "profiles" / "data_engineer" / "cv.pdf"

PROFILE_NAME = "Profil généré depuis le CV"
PROFILE_LOCATIONS = ["Remote"]
PROFILE_REMOTE = True
PROFILE_SALARY_MIN = 0

MAX_RESULTS_DISPLAYED = 20


def minimum_required_matches(
    profile_skills: list[str],
) -> int:
    """
    Détermine le nombre minimal de compétences communes.

    Un profil court nécessite une correspondance.
    Un profil plus riche en nécessite au moins deux.
    """

    return 1 if len(profile_skills) <= 3 else 2

def display_jobs_before_filtering(jobs: list) -> None:
    """Affiche les offres reçues du JobService avant filtrage final."""

    print_section("DIAGNOSTIC AVANT FILTRAGE")

    if not jobs:
        print("Aucune offre reçue du JobService.")
        return

    for index, job in enumerate(jobs, start=1):
        title = getattr(job, "title", "Titre non renseigné")
        company = getattr(job, "company", "Entreprise non renseignée")
        score = getattr(job, "score", 0)

        matched_skills = normalize_skill_list(
            getattr(job, "matched_skills", [])
        )

        missing_skills = normalize_skill_list(
            getattr(job, "missing_skills", [])
        )

        provider_skills = normalize_skill_list(
            getattr(job, "skills", [])
        )

        print()
        print("-" * 80)
        print(f"{index}. {title}")
        print(f"Entreprise : {company}")
        print(f"Score : {score}")
        print(f"Tags RemoteOK : {provider_skills or 'Aucun'}")
        print(f"Compétences trouvées : {matched_skills or 'Aucune'}")
        print(f"Compétences manquantes : {missing_skills or 'Aucune'}")

def print_section(title: str) -> None:
    """Affiche un titre de section lisible dans le terminal."""

    print()
    print("=" * 80)
    print(title)
    print("=" * 80)


def normalize_skill_list(skills: list[str] | None) -> list[str]:
    """
    Nettoie et déduplique une liste de compétences.

    La casse est uniformisée pour éviter que Python, PYTHON et python
    soient considérés comme trois compétences différentes.
    """

    normalized_skills: set[str] = set()

    for skill in skills or []:
        cleaned_skill = str(skill or "").strip().casefold()

        if cleaned_skill:
            normalized_skills.add(cleaned_skill)

    return sorted(normalized_skills)


def extract_cv_text(cv_path: Path) -> str:
    """Extrait le texte contenu dans le fichier PDF."""

    if not cv_path.exists():
        raise FileNotFoundError(
            f"Le CV est introuvable : {cv_path}\n"
            "Vérifie la valeur de CV_PATH dans le script."
        )

    if not cv_path.is_file():
        raise ValueError(f"Le chemin du CV n'est pas un fichier : {cv_path}")

    parser = CVParser()
    text = parser.extract_text(str(cv_path))

    if not text or not text.strip():
        raise ValueError(
            "Aucun texte n'a été extrait du CV. "
            "Le PDF est peut-être vide, protégé ou composé uniquement d'images."
        )

    return text.strip()


def extract_skills(cv_text: str) -> list[str]:
    """Détecte et normalise les compétences présentes dans le CV."""

    extractor = SkillExtractor()
    extracted_skills = extractor.extract(cv_text)

    return normalize_skill_list(extracted_skills)


def create_profile(skills: list[str]) -> Profile:
    """Crée un profil temporaire à partir des compétences détectées."""

    return Profile(
        name=PROFILE_NAME,
        keywords=skills,
        locations=PROFILE_LOCATIONS,
        salary_min=PROFILE_SALARY_MIN,
        remote=PROFILE_REMOTE,
    )


def filter_relevant_jobs(
    jobs: list,
    profile_skills: list[str],
) -> list:
    """
    Retire les offres trop peu liées au CV.
    """

    minimum_matches = minimum_required_matches(
        profile_skills
    )

    relevant_jobs = []

    for job in jobs:
        matched_skills = normalize_skill_list(
            getattr(job, "matched_skills", [])
        )

        if len(matched_skills) >= minimum_matches:
            relevant_jobs.append(job)

    return relevant_jobs


def display_jobs(jobs: list) -> None:
    """Affiche les résultats retenus dans le terminal."""

    if not jobs:
        print(
            "Aucune offre suffisamment pertinente n'a été retenue.\n"
            "Le flux technique fonctionne, mais les offres disponibles "
            "ne correspondent pas encore assez aux compétences du CV."
        )
        return

    jobs_to_display = jobs[:MAX_RESULTS_DISPLAYED]

    print(f"{len(jobs)} offre(s) pertinente(s) retenue(s)")

    if len(jobs) > MAX_RESULTS_DISPLAYED:
        print(
            f"Affichage limité aux {MAX_RESULTS_DISPLAYED} "
            "premières offres."
        )

    for index, job in enumerate(jobs_to_display, start=1):
        title = getattr(job, "title", "Titre non renseigné")
        company = getattr(job, "company", "Entreprise non renseignée")
        location = getattr(job, "location", "Localisation non renseignée")
        score = getattr(job, "score", 0)
        source = getattr(job, "source", "Source non renseignée")
        url = getattr(job, "url", None)

        matched_skills = normalize_skill_list(
            getattr(job, "matched_skills", [])
        )
        missing_skills = normalize_skill_list(
            getattr(job, "missing_skills", [])
        )

        explanation = str(
            getattr(job, "explanation", "") or ""
        ).strip()

        print()
        print("-" * 80)
        print(f"{index}. {title}")
        print(f"Entreprise : {company}")
        print(f"Localisation : {location}")
        print(f"Source : {source}")
        print(f"Score : {score}")

        print(
            "Compétences trouvées : "
            f"{matched_skills if matched_skills else 'Aucune'}"
        )

        print(
            "Compétences manquantes : "
            f"{missing_skills if missing_skills else 'Aucune'}"
        )

        if explanation:
            print(f"Explication : {explanation}")

        if url:
            print(f"URL : {url}")


def main() -> None:
    try:
        print_section("LECTURE DU CV")

        cv_text = extract_cv_text(CV_PATH)

        print(f"CV utilisé : {CV_PATH}")
        print(f"{len(cv_text)} caractères extraits")

        print_section("EXTRACTION DES COMPÉTENCES")

        skills = extract_skills(cv_text)

        if not skills:
            print("Aucune compétence détectée dans le CV.")
            return

        for skill in skills:
            print(f"✓ {skill}")

        print()
        print(f"Total : {len(skills)} compétence(s)")

        print_section("CRÉATION DU PROFIL TEMPORAIRE")

        profile = create_profile(skills)

        print(f"Nom : {profile.name}")
        print(f"Compétences : {profile.keywords}")
        print(f"Localisations : {profile.locations}")
        print(f"Télétravail : {profile.remote}")
        print(f"Salaire minimum : {profile.salary_min}")

        print_section("RECHERCHE REMOTEOK")

        service = JobService( persistence_enabled=False,)
        jobs = service.search(profile)

        print(f"{len(jobs)} offre(s) récupérée(s) avant filtrage")

        display_jobs_before_filtering(jobs)

        print_section("FILTRAGE DES OFFRES")

        relevant_jobs = filter_relevant_jobs(
            jobs=jobs,
            profile_skills=skills,
        )

        minimum_matches = minimum_required_matches(  skills)

        print(
            "Nombre minimal de compétences communes requis : "
            f"{minimum_matches}"
        )
        print(
            f"{len(relevant_jobs)} offre(s) conservée(s) "
            f"sur {len(jobs)}"
        )

        print_section("RÉSULTATS")

        display_jobs(relevant_jobs)

    except FileNotFoundError as error:
        print()
        print(f"ERREUR FICHIER : {error}")

    except AttributeError as error:
        print()
        print(f"ERREUR D'INTERFACE : {error}")
        print(
            "Une classe utilisée par le test ne possède probablement pas "
            "la méthode attendue."
        )

    except Exception as error:
        print()
        print(
            f"ERREUR INATTENDUE : "
            f"{type(error).__name__}: {error}"
        )
        raise


if __name__ == "__main__":
    main()