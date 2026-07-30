"""
Extraction de la localisation.
"""

import re


KNOWN_LOCATIONS = [

    "paris",
    "lyon",
    "lille",
    "bordeaux",
    "toulouse",
    "marseille",
    "nantes",
    "rennes",
    "france",

]


class LocationExtractor:

    def extract(self, text: str) -> list[str]:

        text = text.lower()

        found = []

        for city in KNOWN_LOCATIONS:

            if re.search(rf"\b{re.escape(city)}\b", text):

                found.append(city.title())

        return sorted(found)