# -*- coding: utf-8 -*-
"""app.py — Accueil / vue d'ensemble du projet (dashboard Streamlit)."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import pandas as pd
import plotly.express as px
import streamlit as st

from theme import (FIG, TAB, FORE, MODELS, ACCENT, COLORS, page, kpi,
                   load_csv, style_fig)

st.set_page_config(page_title="Énergie allemande — Séries temporelles",
                   page_icon="⚡", layout="wide")
page("⚡", "Énergie allemande (ENTSO-E) — séries temporelles",
     "Load / Wind / Solar · horaire · 01/01/2015 → 30/09/2020 · "
     "split chronologique 90/10 · horizons h = 5/10/24/5040")

# ---------------------------------------------------------------- KPI
ov = load_csv("data_overview_summary.csv")
n_obs = int(ov["n_obs"].iloc[0]) if ov is not None else 50400
period = (f"{ov['start'].iloc[0][:10]} → {ov['end'].iloc[0][:10]}"
          if ov is not None else "2015 → 2020")

c = st.columns(5)
kpi(c[0], "Observations", f"{n_obs:,}".replace(",", " "), "horaire UTC")
kpi(c[1], "Variables", "3", "Load / Wind / Solar")
kpi(c[2], "Figures", len(list(FIG.glob("*.png"))), "results/figures")
kpi(c[3], "Tables", len(list(TAB.glob("*.csv"))), "results/tables")
kpi(c[4], "Modèles", len(list(MODELS.glob("*"))), "results/models")

st.write("")

# ---------------------------------------------------------------- ranking
left, right = st.columns([3, 2])
with left:
    st.subheader("🏆 Meilleur RMSE par variable et horizon")
    rank = load_csv("py_evaluation_ranking.csv")
    if rank is not None and not rank.empty:
        best = (rank.sort_values("RMSE")
                .groupby(["Variable", "Horizon"], as_index=False)
                .first())
        fig = px.bar(best, x="Variable", y="RMSE", color="Horizon",
                     barmode="group", text="Modele",
                     color_discrete_sequence=px.colors.qualitative.Bold)
        fig.update_traces(textposition="outside", cliponaxis=False)
        st.plotly_chart(style_fig(fig, 430), width="stretch")
    else:
        st.info("`py_evaluation_ranking.csv` absent — lancez `evaluation.py`.")

with right:
    st.subheader("🔎 Top 10 global")
    if rank is not None and not rank.empty:
        top = rank.sort_values("RMSE").head(10)
        st.dataframe(
            top[["Source", "Variable", "Modele", "Horizon", "RMSE", "MAE"]],
            width="stretch", hide_index=True, height=430)
    else:
        st.info("Classement indisponible.")

# ---------------------------------------------------------------- statut
st.subheader("🧩 État du pipeline")
checks = [
    ("Données préparées", TAB / "data_overview_summary.csv"),
    ("ARIMA / SARIMA", TAB / "py_arima_metrics.csv"),
    ("GARCH", TAB / "py_garch_coefficients.csv"),
    ("VAR / VECM", TAB / "py_vecm.csv"),
    ("LSTM / GRU", TAB / "py_lstm_gru_metrics.csv"),
    ("Validation croisée temporelle", TAB / "py_lstm_gru_cv.csv"),
    ("Intervalles de prédiction", TAB / "py_arima_intervals.csv"),
    ("Prophet", TAB / "py_prophet_metrics.csv"),
    ("Hybride SARIMA+LSTM", TAB / "py_hybrid_metrics.csv"),
    ("Walk-forward", TAB / "py_walkforward_metrics.csv"),
    ("Diebold–Mariano", TAB / "py_diebold_mariano.csv"),
    ("Échanges LLM", FORE.parent / "llm" / "echanges"),
]
cols = st.columns(4)
for i, (label, path) in enumerate(checks):
    ok = path.exists() and (not path.is_dir() or any(path.iterdir()))
    badge = ('<span class="ts-badge ts-ok">disponible</span>' if ok else
             '<span class="ts-badge ts-ko">à produire</span>')
    cols[i % 4].markdown(
        f'<div class="ts-card" style="margin-bottom:.6rem">'
        f'<div class="lab">{label}</div>{badge}</div>',
        unsafe_allow_html=True)

st.caption("© Mini-projet Séries Temporelles — TEK-UP · dashboard Streamlit")
