# -*- coding: utf-8 -*-
"""4_Walkforward.py — prévisions walk-forward 1 pas (par variable)."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from theme import FORE, COLORS, page, style_fig

st.set_page_config(page_title="Walk-forward", page_icon="📈", layout="wide")
page("📈", "Prévisions walk-forward (1 pas)",
     "Origine glissante sur le jeu de test : observations vs modèles "
     "(results/forecasts).")

files = sorted(FORE.glob("py_walkforward_*.csv"))
if not files:
    st.info("Aucune prévision walk-forward — lancez `evaluation.py`.")
    st.stop()

v = st.selectbox("Variable", [f.stem.replace("py_walkforward_", "")
                              for f in files])
df = pd.read_csv(FORE / f"py_walkforward_{v}.csv")
df["DateTime"] = pd.to_datetime(df["DateTime"])
model_cols = [c for c in df.columns if c not in ("Observe", "DateTime")]

c1, c2 = st.columns([3, 1])
models = c1.multiselect("Modèles", model_cols, default=model_cols)
window = c2.selectbox("Fenêtre affichée", ["Tout", "1 semaine (168)",
                       "1 mois (720)", "3 mois (2160)"])
nmap = {"Tout": len(df), "1 semaine (168)": 168, "1 mois (720)": 720,
        "3 mois (2160)": 2160}
view = df.tail(nmap[window]).reset_index(drop=True)

# Métriques sur la fenêtre affichée
if models:
    rows = []
    for m in models:
        if m not in view.columns:
            continue
        e = view["Observe"].values - view[m].values
        rows.append({"Modèle": m,
                     "RMSE": float(np.sqrt(np.nanmean(e ** 2))),
                     "MAE": float(np.nanmean(np.abs(e)))})
    if rows:
        st.dataframe(pd.DataFrame(rows),
                     width="stretch", hide_index=True)

fig = go.Figure()
fig.add_scatter(x=view["DateTime"], y=view["Observe"], name="Observé",
                line=dict(color="#0f172a", width=2))
for m in models:
    if m in view.columns:
        fig.add_scatter(x=view["DateTime"], y=view[m], name=m,
                        line=dict(color=COLORS.get(m), width=1.2))
st.plotly_chart(style_fig(fig, 480), width="stretch")
