from __future__ import annotations

from dataclasses import dataclass

import streamlit as st


@dataclass(frozen=True, slots=True)
class JobAgentTokens:
    background: str = "#F7F8FA"
    surface: str = "#FFFFFF"
    surface_alt: str = "#F1F4F8"
    text_primary: str = "#182230"
    text_secondary: str = "#667085"
    border: str = "#E4E7EC"
    accent: str = "#315C8C"
    accent_soft: str = "#EAF1F8"
    shadow: str = "0 1px 3px rgba(16, 24, 40, 0.06)"
    radius_sm: str = "10px"
    radius_md: str = "14px"
    radius_lg: str = "18px"
    spacing: str = "1rem"


TOKENS = JobAgentTokens()


def apply_jobagent_theme() -> None:
    """Applique le thème visuel partagé sans modifier le métier."""

    t = TOKENS
    st.html(
        f"""
        <style>
        :root {{
          --ja-background: {t.background};
          --ja-surface: {t.surface};
          --ja-surface-alt: {t.surface_alt};
          --ja-text: {t.text_primary};
          --ja-muted: {t.text_secondary};
          --ja-border: {t.border};
          --ja-accent: {t.accent};
          --ja-accent-soft: {t.accent_soft};
          --ja-shadow: {t.shadow};
          --ja-radius-sm: {t.radius_sm};
          --ja-radius-md: {t.radius_md};
          --ja-radius-lg: {t.radius_lg};
          --ja-spacing: {t.spacing};
        }}
        [data-testid="stAppViewContainer"] {{
          background: var(--ja-background);
          color: var(--ja-text);
        }}
        [data-testid="stMainBlockContainer"] {{
          box-sizing: border-box;
          max-width: none;
          width: 100%;
          padding-left: 2rem;
          padding-right: 2rem;
          padding-top: 1.75rem;
        }}
        [data-testid="stSidebar"] {{
          background: var(--ja-surface-alt);
          border-right: 1px solid var(--ja-border);
        }}
        [data-testid="stSidebarContent"] {{ padding-top: 1.25rem; }}
        [data-testid="stVerticalBlockBorderWrapper"] {{
          background: var(--ja-surface);
          border-color: var(--ja-border);
          border-radius: var(--ja-radius-md);
          box-shadow: var(--ja-shadow);
        }}
        [data-testid="stMetric"] {{
          background: var(--ja-surface);
          border: 1px solid var(--ja-border);
          border-radius: var(--ja-radius-md);
          box-shadow: var(--ja-shadow);
          padding: .9rem 1rem;
        }}
        [data-testid="stMetricLabel"] {{ color: var(--ja-muted); }}
        [data-testid="stMetricValue"] {{ color: var(--ja-text); }}
        [data-testid="stButton"] button,
        [data-testid="stLinkButton"] a {{ border-radius: var(--ja-radius-sm); }}
        [data-testid="stExpander"] details {{
          background: var(--ja-surface);
          border-color: var(--ja-border);
          border-radius: var(--ja-radius-md);
        }}
        [data-baseweb="tab-list"] {{ gap: .25rem; }}
        [data-baseweb="tab"] {{ border-radius: var(--ja-radius-sm); }}
        hr {{ border-color: var(--ja-border); }}
        .ja-brand {{ padding: .25rem 0 1rem; }}
        .ja-brand-mark {{
          align-items: center; display: flex; gap: .65rem;
          color: var(--ja-text); font-size: 1.25rem; font-weight: 750;
          letter-spacing: .08em;
        }}
        .ja-brand-icon {{
          align-items: center; background: var(--ja-text); border-radius: 12px;
          color: white; display: inline-flex; font-size: 1.15rem;
          height: 2.35rem; justify-content: center; width: 2.35rem;
        }}
        .ja-brand-subtitle {{ color: var(--ja-muted); font-size: .76rem; margin: .3rem 0 0 3rem; }}
        .ja-topbar {{
          align-items: center; background: var(--ja-surface); border: 1px solid var(--ja-border);
          border-radius: var(--ja-radius-md); box-shadow: var(--ja-shadow); display: flex;
          gap: 1.25rem; justify-content: space-between; margin-bottom: 1.25rem;
          padding: .8rem 1rem;
        }}
        .ja-topbar-main {{ color: var(--ja-text); font-weight: 650; }}
        .ja-topbar-meta {{ color: var(--ja-muted); font-size: .82rem; }}
        .ja-eyebrow {{ color: var(--ja-accent); font-size: .75rem; font-weight: 700; letter-spacing: .08em; text-transform: uppercase; }}
        @media (max-width: 1440px) {{
          [data-testid="stMainBlockContainer"] {{ padding-left: 1.5rem; padding-right: 1.5rem; }}
        }}
        @media (max-width: 1100px) {{
          [data-testid="stMainBlockContainer"] {{ padding-left: 1.25rem; padding-right: 1.25rem; }}
          .ja-topbar {{ align-items: flex-start; flex-direction: column; gap: .25rem; }}
        }}
        </style>
        """
    )
