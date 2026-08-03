import re


class TextNormalizer:
    """Normalisation générique des textes."""

    @staticmethod
    def normalize(text: str) -> str:
        if not text:
            return ""

        text = text.replace("\u00A0", " ")
        text = text.replace("\t", " ")

        text = text.replace("’", "'")
        text = text.replace("‘", "'")

        text = text.replace("–", "-")
        text = text.replace("—", "-")

        text = re.sub(r"[ ]+", " ", text)
        text = re.sub(r"\n\s*\n+", "\n", text)

        return text.strip()