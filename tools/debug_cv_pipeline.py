from __future__ import annotations

import argparse
import sys
import traceback
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(
        0,
        str(PROJECT_ROOT),
    )

def print_section(
    title: str,
) -> None:
    print()
    print("=" * 88)
    print(title)
    print("=" * 88)


def print_value(
    label: str,
    value: Any,
) -> None:
    print(f"{label:<30}: {value}")


def extract_pdf_text(
    pdf_path: Path,
) -> str:
    """
    Extraction indépendante du pipeline JobAgent.

    Cette étape permet de vérifier que le PDF contient
    bien du texte exploitable avant l'analyse métier.
    """
    try:
        import fitz
    except ImportError as error:
        raise RuntimeError(
            "PyMuPDF n'est pas installé dans "
            "l'environnement courant."
        ) from error

    document = fitz.open(
        pdf_path
    )

    try:
        pages = [
            page.get_text("text")
            for page in document
        ]
    finally:
        document.close()

    return "\n".join(
        pages
    ).strip()


def run_cv_skill_extractor(
    text: str,
) -> Any:
    """
    Extracteur actuellement utilisé dans le domaine CV.
    """
    from src.cv.skills.extractor import (
        SkillExtractor,
    )

    extractor = SkillExtractor()

    return extractor.extract(
        text
    )


def run_ai_skill_extractor(
    text: str,
) -> Any:
    """
    Extracteur fondé sur le dictionnaire partagé IA.

    Cette seconde mesure permet de comparer les deux
    chemins d'extraction présents dans JobAgent.
    """
    from src.ai.skill_extractor import (
        SkillExtractor,
    )

    extractor = SkillExtractor()

    return extractor.extract(
        text
    )


def build_debug_workspace():
    
    from src.auth.models import (
        CurrentUser,
    )
    from src.auth.user_context import (
        UserContext,
    )
    from src.workspace import (
        build_workspace,
    )


    current_user = CurrentUser(
        user_id="debug-cv-pipeline",
        subject="debug-cv-pipeline",
        email="ludovic.roumieux@gmail.com",
        display_name="CV Pipeline Debug",
        authenticated=True,
        authorized=True,
        roles=("user",),
    )

    user_context = UserContext(
        current_user=current_user,
    )

    return build_workspace(
        user_context=user_context,
        storage_root=(
            PROJECT_ROOT
            / "data"
            / "debug_users"
        ),
    )


def run_onboarding_preview(
    *,
    pdf_path: Path,
    content: bytes,
) -> Any:
    """
    Exécute exactement le service utilisé par le formulaire
    « Créer un profil depuis mon CV » du Career Workspace.
    """
    workspace = (
        build_debug_workspace()
    )

    return (
        workspace
        .onboarding_service
        .preview_from_bytes(
            content=content,
            original_filename=pdf_path.name,
        )
    )


def show_object_fields(
    value: Any,
) -> None:
    """
    Affiche les propriétés publiques disponibles afin
    d'éviter de masquer une information produite par
    une version différente du modèle.
    """
    if value is None:
        print("Aucun résultat.")
        return

    field_names = (
        "detected_role",
        "detected_role_score",
        "detected_family",
        "detected_job_family",
        "job_family",
        "suggested_profile_name",
        "suggested_cv_title",
        "detected_skills",
        "normalized_skills",
        "suggested_keywords",
        "warnings",
    )

    displayed: set[str] = set()

    for field_name in field_names:
        if not hasattr(
            value,
            field_name,
        ):
            continue

        displayed.add(
            field_name
        )

        field_value = getattr(
            value,
            field_name,
        )

        print_value(
            field_name,
            field_value,
        )

    print()
    print("Propriétés publiques supplémentaires :")

    additional_fields = []

    for field_name in dir(value):
        if field_name.startswith("_"):
            continue

        if field_name in displayed:
            continue

        try:
            field_value = getattr(
                value,
                field_name,
            )
        except Exception:
            continue

        if callable(field_value):
            continue

        additional_fields.append(
            (
                field_name,
                field_value,
            )
        )

    if not additional_fields:
        print("- aucune")
        return

    for field_name, field_value in additional_fields:
        print_value(
            field_name,
            field_value,
        )


def show_exception(
    *,
    stage: str,
    error: Exception,
) -> None:
    print()
    print(f"ERREUR pendant : {stage}")
    print(
        f"{type(error).__name__}: {error}"
    )
    print()
    traceback.print_exc()


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Diagnostic du pipeline d'analyse CV "
            "de JobAgent."
        )
    )

    parser.add_argument(
        "pdf_path",
        type=Path,
        help="Chemin du CV PDF à analyser.",
    )

    parser.add_argument(
        "--text-limit",
        type=int,
        default=5000,
        help=(
            "Nombre maximal de caractères affichés "
            "pour le texte extrait."
        ),
    )

    return parser.parse_args()


def main() -> int:
    arguments = parse_arguments()

    pdf_path = (
        arguments.pdf_path
        .expanduser()
        .resolve()
    )

    print_section(
        "0. FICHIER"
    )

    print_value(
        "Chemin",
        pdf_path,
    )

    if not pdf_path.exists():
        print(
            "ERREUR : le fichier n'existe pas."
        )
        return 1

    if not pdf_path.is_file():
        print(
            "ERREUR : le chemin ne désigne "
            "pas un fichier."
        )
        return 1

    content = pdf_path.read_bytes()

    print_value(
        "Nom",
        pdf_path.name,
    )
    print_value(
        "Taille",
        f"{len(content)} octets",
    )

    # --------------------------------------------------------------
    # 1. Extraction PDF indépendante
    # --------------------------------------------------------------

    try:
        text = extract_pdf_text(
            pdf_path
        )
    except Exception as error:
        show_exception(
            stage="extraction du texte PDF",
            error=error,
        )
        return 1

    print_section(
        "1. TEXTE EXTRAIT DU PDF"
    )

    print_value(
        "Nombre de caractères",
        len(text),
    )

    print_value(
        "Nombre de lignes",
        len(text.splitlines()),
    )

    print()

    if text:
        print(
            text[
                : arguments.text_limit
            ]
        )

        if (
            len(text)
            > arguments.text_limit
        ):
            print()
            print(
                "... texte tronqué pour "
                "l'affichage ..."
            )
    else:
        print(
            "AUCUN TEXTE EXTRAIT"
        )

    # --------------------------------------------------------------
    # 2. Extracteur du domaine CV
    # --------------------------------------------------------------

    print_section(
        "2. SRC.CV.SKILLS.EXTRACTOR"
    )

    try:
        cv_skills = (
            run_cv_skill_extractor(
                text
            )
        )

        print_value(
            "Type du résultat",
            type(cv_skills).__name__,
        )

        print_value(
            "Résultat",
            cv_skills,
        )

        try:
            print_value(
                "Nombre",
                len(cv_skills),
            )
        except TypeError:
            pass

    except Exception as error:
        show_exception(
            stage=(
                "src.cv.skills.extractor"
            ),
            error=error,
        )

    # --------------------------------------------------------------
    # 3. Extracteur IA partagé
    # --------------------------------------------------------------

    print_section(
        "3. SRC.AI.SKILL_EXTRACTOR"
    )

    try:
        ai_skills = (
            run_ai_skill_extractor(
                text
            )
        )

        print_value(
            "Type du résultat",
            type(ai_skills).__name__,
        )

        print_value(
            "Résultat",
            ai_skills,
        )

        try:
            print_value(
                "Nombre",
                len(ai_skills),
            )
        except TypeError:
            pass

    except Exception as error:
        show_exception(
            stage=(
                "src.ai.skill_extractor"
            ),
            error=error,
        )

    # --------------------------------------------------------------
    # 4. Pipeline réel du Career Workspace
    # --------------------------------------------------------------

    print_section(
        "4. ONBOARDING_SERVICE.PREVIEW_FROM_BYTES"
    )

    try:
        preview = (
            run_onboarding_preview(
                pdf_path=pdf_path,
                content=content,
            )
        )

        print_value(
            "Type du résultat",
            type(preview).__name__,
        )

        print()

        show_object_fields(
            preview
        )

    except Exception as error:
        show_exception(
            stage=(
                "workspace.onboarding_service."
                "preview_from_bytes"
            ),
            error=error,
        )
        return 1

    # --------------------------------------------------------------
    # 5. Résumé diagnostic
    # --------------------------------------------------------------

    print_section(
        "5. RÉSUMÉ DU DIAGNOSTIC"
    )

    detected_role = getattr(
        preview,
        "detected_role",
        None,
    )

    detected_skills = (
        getattr(
            preview,
            "detected_skills",
            None,
        )
        or getattr(
            preview,
            "normalized_skills",
            None,
        )
        or ()
    )

    print_value(
        "Texte disponible",
        bool(text),
    )

    print_value(
        "Métier détecté",
        detected_role,
    )

    print_value(
        "Compétences détectées",
        detected_skills,
    )

    if text and not detected_skills:
        print()
        print(
            "DIAGNOSTIC PROBABLE :"
        )
        print(
            "- l'extraction PDF fonctionne ;"
        )
        print(
            "- les compétences disparaissent "
            "pendant l'extraction ou la "
            "normalisation métier."
        )

    if text and not detected_role:
        print()
        print(
            "DIAGNOSTIC PROBABLE POUR LE MÉTIER :"
        )
        print(
            "- le texte contient bien un intitulé ;"
        )
        print(
            "- le classificateur ou le référentiel "
            "de familles métiers ne reconnaît pas "
            "ce domaine."
        )

    return 0


if __name__ == "__main__":
    raise SystemExit(
        main()
    )