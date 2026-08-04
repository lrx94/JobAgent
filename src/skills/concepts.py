from __future__ import annotations

from dataclasses import dataclass


@dataclass(
    frozen=True,
    slots=True,
)
class BusinessConcept:
    """
    Concept métier canonique et formulations permettant
    de le détecter dans un CV ou une annonce.
    """

    concept_id: str
    label: str
    aliases: tuple[str, ...]
    categories: tuple[str, ...] = ()
    minimum_alias_matches: int = 1

    def __post_init__(self) -> None:
        concept_id = str(
            self.concept_id or ""
        ).strip().casefold()

        label = str(
            self.label or ""
        ).strip()

        if not concept_id:
            raise ValueError(
                "BusinessConcept.concept_id est obligatoire."
            )

        if not label:
            raise ValueError(
                "BusinessConcept.label est obligatoire."
            )

        aliases = self._normalize_values(
            (
                label,
                *tuple(self.aliases or ()),
            )
        )

        if not aliases:
            raise ValueError(
                "BusinessConcept.aliases ne peut pas être vide."
            )

        object.__setattr__(
            self,
            "concept_id",
            concept_id,
        )

        object.__setattr__(
            self,
            "label",
            label,
        )

        object.__setattr__(
            self,
            "aliases",
            aliases,
        )

        object.__setattr__(
            self,
            "categories",
            self._normalize_values(
                self.categories
            ),
        )

        object.__setattr__(
            self,
            "minimum_alias_matches",
            max(
                1,
                int(
                    self.minimum_alias_matches
                    or 1
                ),
            ),
        )

    @staticmethod
    def _normalize_values(
        values,
    ) -> tuple[str, ...]:
        result: list[str] = []
        seen: set[str] = set()

        for value in values or ():
            cleaned = str(
                value or ""
            ).strip()

            if not cleaned:
                continue

            identity = cleaned.casefold()

            if identity in seen:
                continue

            seen.add(identity)
            result.append(cleaned)

        return tuple(result)


BUSINESS_CONCEPTS: tuple[
    BusinessConcept,
    ...
] = (
    BusinessConcept(
        concept_id="itil",
        label="ITIL",
        aliases=(
            "itilv4",
            "itil v4",
            "itil 4",
            "itil4",
            "itil foundation",
            "itil v4 foundation",
            "itil 4 foundation",
            "information technology "
            "infrastructure library",
        ),
        categories=(
            "itsm",
            "certification",
            "governance",
        ),
    ),
    BusinessConcept(
        concept_id="project_management",
        label="Gestion de projet",
        aliases=(
            "Pilotage BUILD",
            "gestion de projet",
            "pilotage de projet",
            "pilotage des projets",
            "conduite de projet",
            "conduite des projets",
            "direction de projet",
            "directeur de projet",
            "directrice de projet",
            "chef de projet",
            "cheffe de projet",
            "project management",
            "project manager",
            "gestion de programme",
            "pilotage de programme",
            "direction de programme",
            "program management",
            "programme management",
            "pmo",
            "portefeuille de projets",
            "portfolio management",
            "coordination des projets",
            "coordination de projets",
            "pilotage de projets",
            "conduite de projets",
            "direction de projets",
            "gestion de portefeuilles",
            "gestion de portefeuille",
            "gestion de programmes",
            "gestion de programme",
            "gestion de portefeuilles de projets",
            "gestion de portefeuille de projets",
            "gestion de programmes de projets",
            "gestion de programme de projets",
            "gestion de projets",
            "direction de projets",
            "conduite de projets",
            "coordination de projet",
            "coordination de projets",
            "coordination de programme",
            "coordination de programmes",
            
        ),
        categories=(
            "project_management",
            "management",
        ),
    ),
    BusinessConcept(
        concept_id="it_governance",
        label="Gouvernance SI",
        aliases=(
            "gouvernance si",
            "gouvernance informatique",
            "gouvernance des systèmes "
            "d'information",
            "gouvernance du système "
            "d'information",
            "gouvernance applicative",
            "gouvernance technologique",
            "gouvernance digitale",
            "stratégie si",
            "strategie si",
            "stratégie informatique",
            "strategie informatique",
            "stratégie technologique",
            "strategie technologique",
            "schéma directeur",
            "schema directeur",
            "urbanisation si",
            "urbanisation du si",
            "urbanisation des systèmes "
            "d'information",
            "design authority",
            "comité de pilotage",
            "comite de pilotage",
            "arbitrage stratégique",
            "arbitrage strategique",
            "priorisation et arbitrage",
            "gouvernance comex",
            "gouvernance codir",
            "Gouvernance Stratégique et arbitrage",
            "Gouvernance",

        ),
        categories=(
            "governance",
            "technology",
            "strategy",
        ),
    ),
)