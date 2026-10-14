# -*- coding: utf-8 -*-
"""1_Figures.py — galerie interactive des figures (R + Python)."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import streamlit as st

from theme import FIG, page, figure_categories

st.set_page_config(page_title="Figures", page_icon="🖼️", layout="wide")
page("🖼️", "Galerie des figures", "Toutes les figures produites par les "
     "scripts R et Python (results/figures).")

pngs = sorted(FIG.glob("*.png"))
if not pngs:
    st.info("Aucune figure pour l'instant : lancez d'abord les scripts R/notebooks.")
    st.stop()

cats = figure_categories()


def category_of(name):
    low = name.lower()
    for cat, keys in cats.items():
        if any(k in low for k in keys):
            return cat
    return "Autres"


mapping = {p.name: category_of(p.name) for p in pngs}
all_cats = ["Toutes"] + sorted(set(mapping.values()))

f1, f2, f3, f4 = st.columns([2, 2, 2, 1])
cat = f1.selectbox("Thème", all_cats)
var = f2.selectbox("Variable", ["Toutes", "Load", "Wind", "Solar"])
source = f3.selectbox("Source", ["Toutes", "R", "Python"])
ncol = f4.radio("Colonnes", [2, 3, 4], horizontal=True, index=1)

q = st.text_input("🔎 Recherche par nom", "").strip().lower()

sel = [p for p in pngs
       if (cat == "Toutes" or mapping[p.name] == cat)
       and (var == "Toutes" or var.lower() in p.name.lower())
       and (source == "Toutes" or p.name.lower().startswith(source.lower()))
       and (q == "" or q in p.name.lower())]

st.caption(f"{len(sel)} figure(s) affichée(s) sur {len(pngs)}.")

cols = st.columns(ncol)
for i, p in enumerate(sel):
    with cols[i % ncol]:
        st.image(str(p), caption=p.name, width="stretch")
        st.download_button("Télécharger", data=p.read_bytes(),
                           file_name=p.name, mime="image/png",
                           key=f"dl_{p.name}", width="stretch")
