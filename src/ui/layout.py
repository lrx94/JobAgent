from __future__ import annotations

from datetime import datetime
from typing import Any

import streamlit as st


def render_brand() -> None:
    st.html(
        """
        <div class="ja-brand">
          <div class="ja-brand-mark">
            <span class="ja-brand-icon">⌕</span><span>JOBAGENT</span>
          </div>
          <div class="ja-brand-subtitle">Recherche d’emploi intelligente</div>
        </div>
        """
    )


def render_sidebar_navigation() -> None:
    """Affiche les repères fonctionnels de l’espace sans changer le routage."""

    st.markdown("**Navigation**")
    for icon, label in (
        ("dashboard", "Dashboard"),
        ("search", "Rechercher"),
        ("query_stats", "Market Insights"),
        ("school", "Learning"),
        ("person", "Profils"),
        ("settings", "Paramètres"),
    ):
        st.markdown(f":material/{icon}: &nbsp; {label}")


def render_topbar(
    *,
    profile_name: str | None,
    locations: list[str] | tuple[str, ...] = (),
    last_search: datetime | str | None = None,
) -> None:
    location = ", ".join(locations) if locations else "Localisation non renseignée"
    if isinstance(last_search, datetime):
        synchronization = last_search.strftime("%d/%m/%Y à %H:%M")
    else:
        synchronization = str(last_search or "Aucune recherche synchronisée")
    st.html(
        f"""
        <div class="ja-topbar">
          <div><div class="ja-topbar-meta">Profil actif</div>
          <div class="ja-topbar-main">{_escape(profile_name or 'Aucun profil')}</div></div>
          <div><div class="ja-topbar-meta">Localisation</div>
          <div class="ja-topbar-main">{_escape(location)}</div></div>
          <div><div class="ja-topbar-meta">Dernière recherche</div>
          <div class="ja-topbar-main">{_escape(synchronization)}</div></div>
        </div>
        """
    )


def _escape(value: Any) -> str:
    return (
        str(value)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&#x27;")
    )
