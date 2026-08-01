"""
Dictionnaire partagé des synonymes de compétences.

La clé représente la compétence canonique.
Les valeurs représentent les différentes formulations pouvant apparaître
dans un CV ou une annonce.
"""

SKILL_SYNONYMS = {
    # Langages
    "python": [
        "python3",
        "python 3",
        "cpython",
    ],
    "sql": [
        "postgresql",
        "postgres",
        "mysql",
        "mariadb",
        "sqlite",
        "sql server",
        "t-sql",
        "tsql",
        "oracle sql",
    ],

    # Data engineering
    "spark": [
        "apache spark",
        "pyspark",
        "spark sql",
        "spark streaming",
    ],
    "etl": [
        "elt",
        "data pipeline",
        "data pipelines",
        "pipeline de données",
        "pipelines de données",
        "data integration",
        "intégration de données",
    ],
    "databricks": [
        "azure databricks",
    ],
    "airflow": [
        "apache airflow",
    ],
    "snowflake": [
        "snowflake data cloud",
    ],
    "dbt": [
        "data build tool",
        "dbt core",
        "dbt cloud",
    ],
    "power bi": [
        "powerbi",
        "microsoft power bi",
    ],
    "microsoft fabric": [
        "ms fabric",
        "fabric data",
    ],
    "azure data factory": [
        "adf",
        "data factory",
        "azure datafactory",
    ],
    "azure synapse": [
        "synapse",
        "synapse analytics",
        "azure synapse analytics",
    ],

    # Cloud
    "azure": [
        "microsoft azure",
        "azure cloud",
        "azure platform",
    ],
    "aws": [
        "amazon web services",
        "aws cloud",
    ],
    "gcp": [
        "google cloud",
        "google cloud platform",
    ],

    # Infrastructure et DevOps
    "docker": [
        "docker engine",
        "containers",
        "containerisation",
        "containerization",
    ],
    "kubernetes": [
        "k8s",
        "kube",
    ],
    "terraform": [
        "infrastructure as code",
        "iac",
    ],
    "devops": [
        "dev ops",
        "devsecops",
    ],

    # Intelligence artificielle
    "machine learning": [
        "ml",
        "apprentissage automatique",
    ],
    "generative ai": [
        "genai",
        "generative artificial intelligence",
        "ia générative",
        "intelligence artificielle générative",
    ],
    "openai": [
        "chatgpt",
        "gpt",
        "gpt-4",
        "gpt-5",
    ],
    "langchain": [
        "lang chain",
    ],

    # Gestion et gouvernance
    "itil": [
        "itsm",
        "it service management",
    ],
    "cobit": [
        "alignement dir/dsi cobit",
        "it governance cobit",
    ],
    "prince2": [
        "prince 2",
    ],
    "pmp": [
        "project management professional",
    ],
    "agile": [
        "méthode agile",
        "méthodes agiles",
        "agile methodology",
        "agile methodologies",
    ],
    "scrum": [
        "scrum master",
        "scrum methodology",
    ],
    "gestion de projet": [
        "pilotage de projet",
        "direction de projet",
        "project management",
    ],
    "gestion de programme": [
        "pilotage de programme",
        "program management",
        "programme management",
    ],
    "gouvernance si": [
        "gouvernance du si",
        "gouvernance des systèmes d'information",
        "it governance",
        "technology governance",
    ],
    "transformation si": [
        "transformation des si",
        "transformation digitale",
        "transformation numérique",
        "it transformation",
        "digital transformation",
    ],
}