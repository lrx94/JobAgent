"""
Utilitaires de normalisation de texte.
"""

from __future__ import annotations

import re
import unicodedata


def normalize_text(text: str) -> str:
    """
    Normalise un texte pour faciliter les comparaisons.

    - minuscules
    - suppression des accents
    - apostrophes unifiées
    - espaces multiples supprimés
    """

    text = text.lower()

    # Apostrophes
    text = (
        text.replace("’", "'")
            .replace("`", "'")
            .replace("´", "'")
    )

    # Accents
    text = unicodedata.normalize("NFKD", text)
    text = "".join(
        c for c in text
        if not unicodedata.combining(c)
    )

    # Espaces
    text = re.sub(r"\s+", " ", text)

    return text.strip()