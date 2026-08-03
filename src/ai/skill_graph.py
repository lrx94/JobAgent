"""
Graphe de proximité des compétences.

Les compétences "related" sont volontairement
stockées dans des listes afin de :

- conserver un ordre stable ;
- faciliter les tests ;
- améliorer l'affichage dans l'interface ;
- préparer les futurs scores de proximité.
"""

SKILL_GRAPH = {

    "python": {
        "related": [
            "pandas",
            "numpy",
            "fastapi",
            "flask",
            "django",
            "pytest",
        ]
    },

    "sql": {
        "related": [
            "postgresql",
            "mysql",
            "sqlite",
            "oracle",
        ]
    },

    "docker": {
        "related": [
            "kubernetes",
            "podman",
            "container",
        ]
    },

    "spark": {
        "related": [
            "pyspark",
            "hadoop",
        ]
    },

    "azure": {
        "related": [
            "azure data factory",
            "azure devops",
            "synapse",
        ]
    },

}