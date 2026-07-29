import re


class SkillExtractor:

    SKILLS = [
        "Python",
        "SQL",
        "Azure",
        "Databricks",
        "Spark",
        "Airflow",
        "Docker",
        "Kubernetes",
        "Snowflake",
        "Power BI",
        "Microsoft Fabric",
        "Synapse",
        "Data Factory",
        "GenAI",
        "OpenAI",
        "LangChain",
        "Machine Learning",
        "IA",
        "ITIL",
        "COBIT",
        "PRINCE2",
        "PMP",
        "Agile",
        "Scrum"
    ]

    def extract(self, text: str):

        found = []

        for skill in self.SKILLS:

            if re.search(
                rf"\b{re.escape(skill)}\b",
                text,
                re.IGNORECASE
            ):
                found.append(skill)

        return sorted(found)