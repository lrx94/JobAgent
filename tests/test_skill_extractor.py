from src.cv.skills.extractor import SkillExtractor


def test_extract_empty_text() -> None:
    extractor = SkillExtractor()

    assert extractor.extract("") == []


def test_clean_lines() -> None:
    extractor = SkillExtractor()

    text = """
        Architecture SI.

        Cloud     hybride.
    """

    result = extractor._clean_lines(text)

    assert result == [
        "Architecture SI.",
        "Cloud hybride.",
    ]


def test_remove_headers() -> None:
    extractor = SkillExtractor()

    lines = [
        "Gouvernance",
        "Architecture SI.",
        "Management",
        "Cloud hybride.",
    ]

    result = extractor._remove_headers(lines)

    assert result == [
        "Architecture SI.",
        "Cloud hybride.",
    ]


def test_merge_wrapped_lines() -> None:
    extractor = SkillExtractor()

    lines = [
        "Reporting DG/CODIR, KPI,",
        "gestion des risques,",
        "dépendances et engagements.",
        "Transformation numérique.",
    ]

    result = extractor._merge_wrapped_lines(lines)

    assert result == [
        (
            "Reporting DG/CODIR, KPI, gestion des risques, "
            "dépendances et engagements."
        ),
        "Transformation numérique.",
    ]


def test_extract_complete_section() -> None:
    extractor = SkillExtractor()

    text = """
    Gouvernance
    Reporting DG/CODIR, KPI,
    gestion des risques,
    dépendances et engagements.
    Management
    Management d'équipes pluridisciplinaires.
    """

    result = extractor.extract(text)

    assert result == [
        (
            "Reporting DG/CODIR, KPI, gestion des risques, "
            "dépendances et engagements."
        ),
        "Management d'équipes pluridisciplinaires.",
    ]
def test_does_not_merge_two_distinct_skills() -> None:
    extractor = SkillExtractor()

    lines = [
        "Conformité santé et audit qualité",
        "Alignement Dir/DSI COBIT",
    ]

    result = extractor._merge_wrapped_lines(lines)

    assert result == [
        "Conformité santé et audit qualité",
        "Alignement Dir/DSI COBIT",
    ]


def test_merges_line_starting_with_lowercase() -> None:
    extractor = SkillExtractor()

    lines = [
        "Pilotage d'un portefeuille de 100 projets et 400",
        "applications dans un environnement critique.",
    ]

    result = extractor._merge_wrapped_lines(lines)

    assert result == [
        (
            "Pilotage d'un portefeuille de 100 projets et 400 "
            "applications dans un environnement critique."
        )
    ]


def test_removes_domain_headers() -> None:
    extractor = SkillExtractor()

    lines = [
        "Tech Produit Métiers",
        "Responsable R&D Éditeur.",
        "Sécurité et conformité",
        "Sécurisation des plateformes critiques.",
    ]

    result = extractor._remove_headers(lines)

    assert result == [
        "Responsable R&D Éditeur.",
        "Sécurisation des plateformes critiques.",
    ]
def test_does_not_merge_new_skill_after_comma() -> None:
    extractor = SkillExtractor()

    lines = [
        "Build projet PRINCE2, PMP, Agile / Scrum, cycle en V,",
        (
            "Mise en place d'une gouvernance dédiée pour "
            "un portefeuille stratégique."
        ),
    ]

    result = extractor._merge_wrapped_lines(lines)

    assert result == [
        "Build projet PRINCE2, PMP, Agile / Scrum, cycle en V,",
        (
            "Mise en place d'une gouvernance dédiée pour "
            "un portefeuille stratégique."
        ),
    ]


def test_extracts_finance_skills() -> None:
    extractor = SkillExtractor()

    text = """
    Directeur financier spécialisé dans le pilotage
    budgétaire, le contrôle de gestion, le reporting
    financier et l'analyse financière.

    Suivi de la trésorerie, pilotage de la masse salariale,
    indicateurs de performance, SAP et MS Office.
    """

    skills = set(
        extractor.extract(text)
    )

    assert {
        "pilotage budgétaire",
        "contrôle de gestion",
        "reporting financier",
        "analyse financière",
        "trésorerie",
        "gestion de la masse salariale",
        "indicateurs de performance",
        "sap",
        "microsoft office",
    }.issubset(skills)
if __name__ == "__main__":
    test_extract_empty_text()
    test_clean_lines()
    test_remove_headers()
    test_merge_wrapped_lines()
    test_extract_complete_section()
    test_does_not_merge_two_distinct_skills()
    test_merges_line_starting_with_lowercase()
    test_removes_domain_headers()
    test_does_not_merge_new_skill_after_comma()

    print("✅ test_skill_extractor OK")