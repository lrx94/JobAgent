from __future__ import annotations


class SkillExtractor:
    """
    Extrait et reconstruit les compétences contenues
    dans une section de CV.
    """
    NEW_SKILL_PREFIXES = (
        "Alignement ",
        "Mise en place ",
        "Reprise en main ",
        "Transformation ",
        "Pilotage ",
        "Intégration ",
        "Optimisation ",
        "Conduite ",
        "Réécriture ",
        "Sécurisation ",
        "Définition ",
        "Structuration ",
        "Organisation ",
        "Architecture ",
        "Management ",
    )

    HEADERS = {
        "Domaines d’expertise",
        "Domaines d'expertise",
        "Gouvernance",
        "Management",
        "Méthodologies",
        "Methodologies",
        "Réalisation clé",
        "Réalisation clés",
        "Réalisations clés",
        "Realisation clé",
        "Realisation clés",
        "Realisations clés",
        "Tech Produit Métiers",
        "Sécurité et conformité",
    }

    CONTINUATION_ENDINGS = (
        ",",
        ";",
        ":",
        "/",
        "-",
    )

    def extract(self, text: str) -> list[str]:
        if not text:
            return []

        lines = self._clean_lines(text)
        lines = self._remove_headers(lines)
        lines = self._merge_wrapped_lines(lines)

        return lines

    def _clean_lines(self, text: str) -> list[str]:
        lines: list[str] = []

        for raw_line in text.splitlines():
            line = " ".join(raw_line.strip().split())

            if line:
                lines.append(line)

        return lines

    def _remove_headers(self, lines: list[str]) -> list[str]:
        return [
            line
            for line in lines
            if line not in self.HEADERS
        ]

    def _merge_wrapped_lines(self, lines: list[str]) -> list[str]:
        """
        Fusionne uniquement les lignes qui ressemblent réellement
        à la continuation d'une phrase.

        Une ligne est considérée comme une continuation lorsque :
        - la ligne précédente se termine par une virgule, un deux-points,
          un point-virgule, un slash ou un tiret ;
        - ou la ligne suivante commence par une minuscule.
        """

        if not lines:
            return []

        merged: list[str] = []
        current = lines[0]

        for next_line in lines[1:]:
            if self._is_continuation(current, next_line):
                current = f"{current} {next_line}"
            else:
                merged.append(current)
                current = next_line

        merged.append(current)

        return merged

    def _is_continuation(
        self,
        current: str,
        next_line: str,
    ) -> bool:
        """
        Détermine si next_line prolonge la ligne courante.

        Une ligne identifiée comme le début d'une nouvelle compétence
        reste indépendante, même si la ligne précédente se termine
        par une virgule.
        """

        if next_line.startswith(self.NEW_SKILL_PREFIXES):
            return False

        if current.endswith(self.CONTINUATION_ENDINGS):
            return True

        return next_line[0].islower()