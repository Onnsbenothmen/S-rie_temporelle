# -*- coding: utf-8 -*-
"""2_Tableaux.py — explorateur interactif des tables de résultats (CSV)."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pandas as pd
import streamlit as st

from theme import TAB, page, load_csv

st.set_page_config(page_title="Tableaux", page_icon="📋", layout="wide")
page("📋", "Explorateur de tableaux",
     "Parcourez et filtrez les résultats chiffrés (results/tables).")

tables = sorted(p.name for p in TAB.glob("*.csv"))
if not tables:
    st.info("Aucune table pour l'instant : lancez d'abord les scripts R/notebooks.")
    st.stop()

c1, c2 = st.columns([3, 1])
choice = c1.selectbox("Table", tables)
df = load_csv(choice)
if df is None:
    st.error("Lecture impossible.")
    st.stop()

c2.metric("Dimensions", f"{len(df)} × {len(df.columns)}")

# Recherche plein-texte (filtre les lignes contenant la requête)
q = st.text_input("🔎 Rechercher une valeur (toutes colonnes)", "")
view = df
if q.strip():
    mask = df.astype(str).apply(
        lambda col: col.str.contains(q, case=False, na=False)).any(axis=1)
    view = df[mask]
    st.caption(f"{len(view)} ligne(s) correspondante(s).")

# Choix des colonnes
cols = st.multiselect("Colonnes à afficher", list(df.columns),
                      default=list(df.columns))
view = view[cols] if cols else view

st.dataframe(view, width="stretch", height=560, hide_index=True)

st.download_button("⬇️ Télécharger la table filtrée (CSV)",
                   data=view.to_csv(index=False).encode("utf-8"),
                   file_name=f"{choice}", mime="text/csv")

with st.expander("Aperçu technique (types et statistiques descriptives)"):
    st.write("**Types :**")
    st.dataframe(pd.DataFrame({"colonne": df.columns,
                               "type": [str(t) for t in df.dtypes],
                               "non_na": df.notna().sum().values,
                               "valeurs_uniques": [df[c].nunique()
                                                   for c in df.columns]}),
                 width="stretch", hide_index=True)
    st.write("**Describe :**")
    try:
        st.dataframe(df.describe(include="all").transpose(),
                     width="stretch")
    except Exception:   # noqa: BLE001
        st.caption("Statistiques indisponibles pour cette table.")
