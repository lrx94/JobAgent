"""
Détection du niveau d'expérience.
"""


class SeniorityExtractor:

    LEVELS = [

        "principal",
        "lead",
        "senior",
        "confirmé",
        "confirme",
        "junior",

    ]

    def extract(self, text: str) -> str | None:

        text = text.lower()

        for level in self.LEVELS:

            if level in text:
                return level.title()

        return None