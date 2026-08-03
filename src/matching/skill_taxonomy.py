from __future__ import annotations


UNKNOWN_CATEGORY = "Unknown"

CATEGORY_PROGRAMMING_LANGUAGE = "Programming Language"
CATEGORY_DATABASE = "Database"
CATEGORY_CLOUD = "Cloud"
CATEGORY_DEVOPS = "DevOps"
CATEGORY_DATA = "Data"
CATEGORY_AI = "Artificial Intelligence"
CATEGORY_ARCHITECTURE = "Architecture"
CATEGORY_CYBERSECURITY = "Cybersecurity"
CATEGORY_GOVERNANCE = "Governance Framework"
CATEGORY_PROJECT_MANAGEMENT = "Project Management"
CATEGORY_PRODUCT_MANAGEMENT = "Product Management"
CATEGORY_AGILE = "Agile"
CATEGORY_SOFT_SKILL = "Soft Skill"


SKILL_TAXONOMY: dict[str, frozenset[str]] = {
    CATEGORY_PROGRAMMING_LANGUAGE: frozenset(
        {
            "c",
            "c++",
            "c#",
            "css",
            "go",
            "golang",
            "html",
            "java",
            "javascript",
            "kotlin",
            "php",
            "python",
            "ruby",
            "rust",
            "scala",
            "shell",
            "sql",
            "swift",
            "typescript",
            "visual basic",
        }
    ),
    CATEGORY_DATABASE: frozenset(
        {
            "cassandra",
            "cosmos db",
            "elasticsearch",
            "mariadb",
            "mongodb",
            "mysql",
            "neo4j",
            "oracle",
            "postgresql",
            "redis",
            "snowflake",
            "sql server",
        }
    ),
    CATEGORY_CLOUD: frozenset(
        {
            "amazon web services",
            "aws",
            "azure",
            "azure cloud",
            "cloud computing",
            "cloud hybride",
            "gcp",
            "google cloud",
            "google cloud platform",
            "openstack",
            "saas",
        }
    ),
    CATEGORY_DEVOPS: frozenset(
        {
            "ansible",
            "argocd",
            "azure devops",
            "ci/cd",
            "continuous delivery",
            "continuous deployment",
            "docker",
            "github actions",
            "gitlab ci",
            "helm",
            "jenkins",
            "kubernetes",
            "terraform",
        }
    ),
    CATEGORY_DATA: frozenset(
        {
            "airflow",
            "analytics",
            "big data",
            "business intelligence",
            "data engineering",
            "data governance",
            "data lake",
            "data warehouse",
            "databricks",
            "etl",
            "hadoop",
            "kafka",
            "power bi",
            "spark",
        }
    ),
    CATEGORY_AI: frozenset(
        {
            "artificial intelligence",
            "computer vision",
            "deep learning",
            "generative ai",
            "ia",
            "intelligence artificielle",
            "large language model",
            "llm",
            "machine learning",
            "mlops",
            "natural language processing",
            "nlp",
            "openai",
            "pytorch",
            "scikit-learn",
            "tensorflow",
        }
    ),
    CATEGORY_ARCHITECTURE: frozenset(
        {
            "architecture applicative",
            "architecture cloud",
            "architecture d'entreprise",
            "architecture logicielle",
            "architecture métier",
            "architecture si",
            "architecture technique",
            "design authority",
            "enterprise architecture",
            "interopérabilité",
            "microservices",
            "solution architecture",
            "urbanisation",
        }
    ),
    CATEGORY_CYBERSECURITY: frozenset(
        {
            "audit de sécurité",
            "cybersecurity",
            "cybersécurité",
            "iso 27001",
            "nist",
            "privacy by design",
            "rgpd",
            "security by design",
            "sécurité",
            "zero trust",
        }
    ),
    CATEGORY_GOVERNANCE: frozenset(
        {
            "cobit",
            "gouvernance des données",
            "gouvernance it",
            "it governance",
            "itil",
            "itil v4",
            "itilv4",
            "togaf",
        }
    ),
    CATEGORY_PROJECT_MANAGEMENT: frozenset(
        {
            "gestion de portefeuille",
            "gestion de programme",
            "gestion de projet",
            "pmbok",
            "pmo",
            "pmp",
            "prince2",
            "project management",
            "programme management",
        }
    ),
    CATEGORY_PRODUCT_MANAGEMENT: frozenset(
        {
            "discovery",
            "product management",
            "product manager",
            "product owner",
            "product strategy",
            "roadmap produit",
            "stratégie produit",
        }
    ),
    CATEGORY_AGILE: frozenset(
        {
            "agile",
            "kanban",
            "lean",
            "safe",
            "scaled agile framework",
            "scrum",
            "scrum master",
        }
    ),
    CATEGORY_SOFT_SKILL: frozenset(
        {
            "communication",
            "conduite du changement",
            "leadership",
            "management",
            "management d'équipe",
            "mentoring",
            "négociation",
            "prise de décision",
            "résolution de problèmes",
            "team management",
        }
    ),
}


def normalize_taxonomy_value(value: str) -> str:
    """
    Normalise une valeur avant sa recherche dans la taxonomie.

    Cette normalisation reste volontairement légère afin de ne pas
    modifier les termes techniques tels que C++, C# ou CI/CD.
    """

    return " ".join(value.strip().casefold().split())


def get_category_for_exact_skill(skill_name: str) -> str:
    """
    Retourne la catégorie associée à un nom exact de compétence.

    Cette fonction ne cherche pas encore les compétences contenues
    dans une phrase complète. Cette responsabilité appartiendra au
    futur SkillClassifier.

    Exemple :
        Azure -> Cloud
        Python -> Programming Language
    """

    normalized_name = normalize_taxonomy_value(skill_name)

    if not normalized_name:
        return UNKNOWN_CATEGORY

    for category, known_skills in SKILL_TAXONOMY.items():
        if normalized_name in known_skills:
            return category

    return UNKNOWN_CATEGORY


def get_known_categories() -> tuple[str, ...]:
    """
    Retourne toutes les catégories disponibles.
    """

    return tuple(SKILL_TAXONOMY.keys())


def get_skills_for_category(category: str) -> frozenset[str]:
    """
    Retourne les compétences connues d'une catégorie.

    Une catégorie inconnue retourne un ensemble immuable vide.
    """

    return SKILL_TAXONOMY.get(category, frozenset())