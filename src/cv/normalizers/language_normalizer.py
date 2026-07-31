class LanguageNormalizer:
    """Normalisation des langues."""

    _ALIASES = {
        "anglais": "English",
        "english": "English",
        "anglais courant": "English",
        "anglais professionnel": "English",
        "fluent english": "English",
        "en": "English",

        "français": "French",
        "francais": "French",
        "french": "French",
        "fr": "French",

        "espagnol": "Spanish",
        "spanish": "Spanish",
        "es": "Spanish",

        "allemand": "German",
        "german": "German",
        "de": "German",

        "italien": "Italian",
        "italian": "Italian",
        "it": "Italian",
    }

    @classmethod
    def normalize(cls, language: str) -> str:
        if not language:
            return ""

        key = language.strip().lower()
        return cls._ALIASES.get(key, language.strip())