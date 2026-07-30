"""
Détection du télétravail.
"""


class RemoteDetector:

    KEYWORDS = [

        "remote",
        "full remote",
        "hybrid",
        "hybride",
        "télétravail",
        "teletravail",

    ]

    def detect(self, text: str) -> bool:

        text = text.lower()

        for keyword in self.KEYWORDS:

            if keyword in text:
                return True

        return False