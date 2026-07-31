from __future__ import annotations

from collections.abc import Iterable

from .models import SemanticMatch


class Scorer:
    """
    Calcule les différentes composantes du score d'une offre.
    """

    SKILL_WEIGHT = 0.50
    LOCATION_WEIGHT = 0.20
    REMOTE_WEIGHT = 0.15
    SALARY_WEIGHT = 0.15

    def skill_score(
        self,
        matches: float,
        total: int,
    ) -> int:
        """
        Calcule un score de compétences à partir d'un nombre pondéré.

        Cette méthode reste compatible avec l'ancien moteur.

        Exemple :
            2 correspondances exactes ;
            1 correspondance de poids 0.70.

            matches = 2.70
        """

        if total <= 0:
            return 0

        bounded_matches = min(
            max(matches, 0.0),
            float(total),
        )

        return round(
            bounded_matches / total * 100
        )

    def semantic_skill_score(
        self,
        exact_matches: Iterable[str],
        semantic_matches: Iterable[SemanticMatch],
        total: int,
    ) -> int:
        """
        Calcule le score des compétences en utilisant les poids
        portés par les objets SemanticMatch.
        """

        exact_count = sum(
            1
            for _ in exact_matches
        )

        semantic_weight = sum(
            match.weight
            for match in semantic_matches
        )

        weighted_matches = (
            exact_count
            + semantic_weight
        )

        return self.skill_score(
            weighted_matches,
            total,
        )

    def location_score(
        self,
        profile,
        job,
    ) -> int:
        """
        Calcule la compatibilité géographique.
        """

        profile_locations = getattr(
            profile,
            "locations",
            [],
        )

        if not profile_locations:
            return 100

        job_location = str(
            getattr(job, "location", "") or ""
        ).casefold()

        for location in profile_locations:
            if str(location).casefold() in job_location:
                return 100

        return 0

    def remote_score(
        self,
        profile,
        job,
    ) -> int:
        """
        Calcule la compatibilité avec le travail à distance.
        """

        profile_remote = bool(
            getattr(profile, "remote", False)
        )

        job_remote = bool(
            getattr(job, "remote", False)
        )

        if not profile_remote:
            return 100

        if job_remote:
            return 100

        return 0

    def salary_score(
        self,
        profile,
        job,
    ) -> int:
        """
        Calcule la compatibilité salariale.

        Une rémunération absente ou invalide obtient zéro lorsque
        le profil impose un minimum salarial.
        """

        salary_min = self._safe_number(
            getattr(profile, "salary_min", 0)
        )

        if salary_min <= 0:
            return 100

        job_salary = self._safe_number(
            getattr(job, "salary", 0)
        )

        if job_salary <= 0:
            return 0

        if job_salary >= salary_min:
            return 100

        return round(
            job_salary / salary_min * 100
        )

    def global_score(
        self,
        skill: int,
        location: int,
        remote: int,
        salary: int,
    ) -> int:
        """
        Calcule le score global et garantit une valeur entre 0 et 100.
        """

        score = round(
            skill * self.SKILL_WEIGHT
            + location * self.LOCATION_WEIGHT
            + remote * self.REMOTE_WEIGHT
            + salary * self.SALARY_WEIGHT
        )

        return max(
            0,
            min(score, 100),
        )

    def _safe_number(
        self,
        value,
    ) -> float:
        """
        Convertit une valeur numérique en float sans interrompre
        le moteur lorsque les données fournisseur sont incomplètes.
        """

        try:
            return float(value or 0)

        except (TypeError, ValueError):
            return 0.0