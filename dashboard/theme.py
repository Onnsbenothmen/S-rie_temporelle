# -*- coding: utf-8 -*-
"""theme.py — utilitaires de presentation partages par le dashboard.

Centralise : chemins des resultats, palette de couleurs, injection CSS et
quelques helpers (cartes KPI, chargement CSV tolerant, theming Plotly).

Chaque page fait :
    import sys; from pathlib import Path
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    from theme import ...
"""

from pathlib import Path

import pandas as pd
import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parent.parent
FIG = PROJECT_ROOT / "results" / "figures"
TAB = PROJECT_ROOT / "results" / "tables"
FORE = PROJECT_ROOT / "results" / "forecasts"
MODELS = PROJECT_ROOT / "results" / "models"

# Palette (accents par variable, cf. conventions du rapport)
ACCENT = "#0ea5e9"
ACCENT_DARK = "#0369a1"
COLORS = {
    "Load": "#2563eb",
    "Wind": "#10b981",
    "Solar": "#f59e0b",
    "naif": "#94a3b8",
    "saisonnier_naif": "#64748b",
    "SARIMA": "#8b5cf6",
    "LSTM": "#ef4444",
    "GRU": "#ec4899",
    "Prophet": "#0ea5e9",
}

_CSS = """
<style>
/* --- typographie & fond --- */
html, body, [class*="css"] { font-family: "Segoe UI", "Inter", sans-serif; }
.stApp {
    background: linear-gradient(180deg, #f8fafc 0%, #eef2f7 100%);
}
/* --- en-tete de page --- */
.ts-hero {
    background: linear-gradient(120deg, #0ea5e9 0%, #2563eb 60%, #7c3aed 100%);
    color: #fff; padding: 1.5rem 1.8rem; border-radius: 16px;
    box-shadow: 0 8px 24px rgba(37,99,235,.25); margin-bottom: 1rem;
}
.ts-hero h1 { color:#fff; font-size: 1.7rem; margin: 0 0 .3rem 0; }
.ts-hero p { color:#eaf2ff; margin: 0; font-size: .95rem; }
/* --- cartes KPI --- */
.ts-card {
    background:#fff; border:1px solid #e2e8f0; border-radius:14px;
    padding:1rem 1.1rem; box-shadow:0 2px 10px rgba(15,23,42,.06);
    height:100%;
}
.ts-card .lab { color:#64748b; font-size:.78rem; text-transform:uppercase;
    letter-spacing:.04em; font-weight:600; }
.ts-card .val { color:#0f172a; font-size:1.7rem; font-weight:700;
    line-height:1.2; }
.ts-card .sub { color:#94a3b8; font-size:.78rem; }
/* --- badges --- */
.ts-badge { display:inline-block; padding:.15rem .55rem; border-radius:999px;
    font-size:.72rem; font-weight:600; }
.ts-ok  { background:#dcfce7; color:#166534; }
.ts-ko  { background:#fee2e2; color:#991b1b; }
/* --- reduce padding top --- */
.block-container { padding-top: 2.2rem; }
</style>
"""


def inject_css():
    st.markdown(_CSS, unsafe_allow_html=True)


def page(icon, title, subtitle):
    """En-tete stylise commun a toutes les pages."""
    inject_css()
    st.markdown(
        f'<div class="ts-hero"><h1>{icon} {title}</h1>'
        f'<p>{subtitle}</p></div>',
        unsafe_allow_html=True,
    )


def card(label, value, sub=""):
    return (
        f'<div class="ts-card"><div class="lab">{label}</div>'
        f'<div class="val">{value}</div><div class="sub">{sub}</div></div>'
    )


def kpi(col, label, value, sub=""):
    col.markdown(card(label, value, sub), unsafe_allow_html=True)


def load_csv(name, folder=None):
    """Chargement tolerant d'une table CSV de results/ ."""
    path = (folder or TAB) / name
    if not path.exists():
        return None
    try:
        return pd.read_csv(path)
    except Exception:   # noqa: BLE001
        return None


def style_fig(fig, height=420):
    fig.update_layout(
        height=height,
        margin=dict(l=10, r=10, t=50, b=10),
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Segoe UI, Inter, sans-serif", size=13),
        legend=dict(orientation="h", yanchor="bottom", y=1.02,
                    xanchor="right", x=1),
    )
    return fig


def figure_categories():
    """Regroupe les figures par theme (pour les filtres de la galerie)."""
    cats = {
        "Donnees / EDA": ["time_series", "overview", "missing", "outliers",
                          "profiles", "hourly_profiles", "seasonal"],
        "Stationnarite / ACF-PACF": ["acf_pacf", "stl"],
        "ARIMA / SARIMA": ["resid", "prev_"],
        "GARCH": ["garch"],
        "VAR / VECM": ["var_", "fevd", "irf"],
        "Deep learning": ["lstm_gru"],
        "Evaluation": ["evaluation"],
    }
    return cats
