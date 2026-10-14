# -*- coding: utf-8 -*-
"""3_Diebold_Mariano.py — test de Diebold–Mariano (comparaisons 1 pas)."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import numpy as np
import plotly.express as px
import streamlit as st

from theme import page, load_csv, style_fig

st.set_page_config(page_title="Diebold–Mariano", page_icon="🥊", layout="wide")
page("🥊", "Test de Diebold–Mariano",
     "Comparaison par paires des erreurs de prévision (effets carrés, 1 pas).")

dm = load_csv("py_diebold_mariano.csv")
if dm is None or dm.empty:
    st.info("`py_diebold_mariano.csv` absent — lancez `evaluation.py`.")
    st.stop()

# Compatibilité ancien (A_LSTM) / nouveau (A, B) format de colonnes
rename = {}
if "A_LSTM" in dm.columns:
    rename["A_LSTM"] = "A"
dm = dm.rename(columns=rename)

c = st.columns(4)
c[0].metric("Comparaisons", len(dm))
if "Conclusion" in dm.columns:
    sig = dm[~dm["Conclusion"].str.contains("non significatif", na=False)]
    c[1].metric("Significatives (5 %)", len(sig))
    c[2].metric("Non significatives", len(dm) - len(sig))
if "p_value" in dm.columns:
    c[3].metric("p-value minimale", f"{dm['p_value'].min():.2e}")

v = st.selectbox("Variable", ["Toutes"] + sorted(dm["Variable"].unique()))
sub = dm if v == "Toutes" else dm[dm["Variable"] == v]

if {"A", "B"} <= set(dm.columns):
    fig = px.bar(sub, x="DM_stat", y=sub["A"] + " vs " + sub["B"],
                 color="Conclusion", orientation="h",
                 color_discrete_sequence=px.colors.qualitative.Set2)
    fig.add_vline(x=0, line_dash="dash", line_color="#334155")
    st.plotly_chart(style_fig(fig, max(380, 30 * len(sub))),
                    width="stretch")
st.caption("DM_stat < 0 ⇒ le modèle A a l'erreur quadratique moyenne la plus "
           "faible (A « meilleur »). Les barres à droite favorisent B.")

show = sub.copy()
if "p_value" in show.columns:
    show["p_value"] = show["p_value"].map(lambda x: f"{x:.2e}")
st.dataframe(show, width="stretch", hide_index=True)
