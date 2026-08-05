from __future__ import annotations

from enum import Enum


class LearningObservationOrigin(
    str,
    Enum,
):
    """
    Composant technique ayant produit une observation.

    La source métier reste portée séparément par
    LearningObservation.source, par exemple :
    France Travail ou RemoteOK.
    """

    JOB_ANALYZER = "job_analyzer"
    PROVIDER = "provider"
    RAW_TEXT_FALLBACK = "raw_text_fallback"
    CV = "cv"
    MARKET_ANALYZER = "market_analyzer"
    UNKNOWN = "unknown"