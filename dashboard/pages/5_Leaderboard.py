# -*- coding: utf-8 -*-
"""5_Leaderboard.py — classement des modèles par RMSE (variable × horizon)."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import plotly.express as px
import streamlit as st

from theme import page, load_csv, style_fig

st.set_page_config(page_title="Leaderboard", page_icon="🏁", layout="wide")
page("🏁", "Leaderboard des modèles",
     "Classement par RMSE à travers variables, horizons et familles de modèles.")

r = load_csv("py_evaluation_ranking.csv")
if r is None or r.empty:
    st.info("`py_evaluation_ranking.csv` absent — lancez `evaluation.py`.")
    st.stop()

c1, c2, c3 = st.columns(3)
var = c1.selectbox("Variable", ["Toutes"] + sorted(r["Variable"].unique()))
hors = c2.selectbox("Horizon", ["Tous"] + sorted(r["Horizon"].unique()))
srcs = c3.multiselect("Source", sorted(r["Source"].unique()),
                      default=sorted(r["Source"].unique()))

sub = r[r["Source"].isin(srcs)]
if var != "Toutes":
    sub = sub[sub["Variable"] == var]
if hors != "Tous":
    sub = sub[sub["Horizon"] == hors]
sub = sub.sort_values("RMSE")

if sub.empty:
    st.warning("Aucune ligne pour ce filtre.")
    st.stop()

fig = px.bar(sub, x="RMSE", y="Modele", color="Source", orientation="h",
             hover_data=["Variable", "Horizon", "MAE", "MAPE"],
             color_discrete_sequence=px.colors.qualitative.Bold)
fig.update_layout(yaxis=dict(categoryorder="total ascending"))
st.plotly_chart(style_fig(fig, max(400, 26 * sub["Modele"].nunique())),
                width="stretch")

st.dataframe(sub, width="stretch", hide_index=True)

best = sub.loc[sub.groupby("Variable")["RMSE"].idxmin()]
st.subheader("🥇 Meilleur modèle par variable")
st.dataframe(best[["Variable", "Modele", "Source", "Horizon", "RMSE", "MAE"]],
             width="stretch", hide_index=True)
