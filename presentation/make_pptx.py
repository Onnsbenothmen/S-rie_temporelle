# -*- coding: utf-8 -*-
"""Génère presentation_projet.pptx dans un style "template Canva".

Usage :  python presentation\\make_pptx.py
"""

from pathlib import Path

from pptx import Presentation
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.util import Inches, Pt

import theme_canva as T

ROOT = Path(__file__).resolve().parent.parent
OUT = Path(__file__).resolve().parent / "presentation_projet.pptx"

T.set_paths(ROOT / "results" / "figures", ROOT / "results" / "dashboard", ROOT)


def new(prs):
    return prs.slides.add_slide(prs.slide_layouts[6])


# --- Slides ----------------------------------------------------------------
def s1_title(prs):
    s = new(prs)
    T.gradient(s, T.DARK, T.DARK2, 40.0)
    T.dots(s, Inches(9.4), Inches(4.4), 7, 5, Inches(0.28), Inches(0.07),
           T.BLUE, alpha=30)
    T.circle(s, -Inches(2.2), -Inches(2.4), Inches(7), T.BLUE, alpha=12)
    T.circle(s, Inches(11.2), Inches(5.0), Inches(4), T.TEAL, alpha=10)

    T.textbox(s, T.MARGIN, Inches(1.45), Inches(9), Inches(0.4),
              "MINI-PROJET  ·  R & PYTHON", size=13, color=T.TEAL,
              bold=True, ls=3)
    T.textbox(s, T.MARGIN, Inches(1.95), Inches(10.6), Inches(1.8),
              "Prévision des séries\ntemporelles énergétiques", size=46,
              color=T.WHITE, bold=True, font=T.HEAD, spacing=1.02)
    T.textbox(s, T.MARGIN, Inches(3.95), Inches(8.6), Inches(0.9),
              "Charge, éolien et solaire en Allemagne (ENTSO-E) : "
              "exploration, modélisation et évaluation comparative de six "
              "familles de modèles.",
              size=15, color=T.MUTED, spacing=1.15)

    pills = [("ARIMA / SARIMA", T.BLUE), ("VAR / VECM", T.VIOLET),
             ("GARCH", T.CORAL), ("LSTM / GRU", T.TEAL),
             ("Prophet & Hybride", T.AMBER)]
    x = T.MARGIN
    for label, col in pills:
        w = Inches(0.28) + Inches(0.095) * len(label)
        T.rrect(s, x, Inches(5.2), w, Inches(0.46), color=T.WHITE, alpha=10,
                radius=0.5)
        T.textbox(s, x, Inches(5.2), w, Inches(0.46), label, size=11,
                  color=col, bold=True, align=PP_ALIGN.CENTER,
                  anchor=MSO_ANCHOR.MIDDLE)
        x += w + Inches(0.18)

    T.rect(s, T.MARGIN, Inches(6.55), Inches(0.07), Inches(0.62), T.TEAL)
    T.textbox(s, T.MARGIN + Inches(0.28), Inches(6.55), Inches(9),
              Inches(0.62), "50 400 observations horaires  ·  2015 → 2020",
              size=12, color=T.WHITE, anchor=MSO_ANCHOR.MIDDLE)
    T.textbox(s, Inches(9.9), Inches(6.55), Inches(2.8), Inches(0.62),
              "Année universitaire 2025-2026", size=12, color=T.MUTED,
              align=PP_ALIGN.RIGHT, anchor=MSO_ANCHOR.MIDDLE)
    T.note(s, "Bonjour. Ce projet porte sur la prévision de la charge "
             "électrique, de la production éolienne et solaire en Allemagne. "
             "Nous comparons six familles de modèles, en R et en Python, pour "
             "des horizons de 5 heures à 7 mois.")


def s2_agenda(prs):
    s = new(prs)
    T.chrome(s, "SOMMAIRE", "Le parcours de la présentation", 2)
    items = [
        ("01", "Contexte & problématique",
         "Enjeux du réseau, données ENTSO-E et question de recherche."),
        ("02", "Données & analyse exploratoire",
         "Structure horaire, saisonnalités et tests de stationnarité."),
        ("03", "Modélisation",
         "ARIMA, VAR/VECM, GARCH, LSTM/GRU, Prophet et approche hybride."),
        ("04", "Évaluation & conclusion",
         "RMSE, classement, Diebold-Mariano, limites et perspectives."),
    ]
    y = Inches(1.95)
    for num, title, sub in items:
        T.rrect(s, T.MARGIN, y, T.CW, Inches(1.02), color=T.WHITE, line=T.LINE,
                radius=0.14)
        T.rrect(s, T.MARGIN + Inches(0.22), y + Inches(0.22), Inches(0.58),
                Inches(0.58), color=T.BLUE, radius=0.22)
        T.textbox(s, T.MARGIN + Inches(0.22), y + Inches(0.22), Inches(0.58),
                  Inches(0.58), num, size=18, color=T.WHITE, bold=True,
                  font=T.HEAD, align=PP_ALIGN.CENTER,
                  anchor=MSO_ANCHOR.MIDDLE)
        T.textbox(s, T.MARGIN + Inches(1.05), y + Inches(0.17), Inches(10.5),
                  Inches(0.4), title, size=16, color=T.INK, bold=True,
                  font=T.HEAD)
        T.textbox(s, T.MARGIN + Inches(1.05), y + Inches(0.56), Inches(10.5),
                  Inches(0.4), sub, size=11.5, color=T.SLATE)
        y += Inches(1.16)
    T.note(s, "La présentation suit quatre temps : le contexte et les données, "
             "puis la modélisation, et enfin l'évaluation comparative et la "
             "conclusion.")


def s3_div01(prs):
    s = new(prs)
    T.gradient(s, T.DARK, T.DARK2, 40.0)
    T.dots(s, Inches(10.0), Inches(1.0), 6, 6, Inches(0.3), Inches(0.075),
           T.BLUE, alpha=25)
    T.textbox(s, T.MARGIN, Inches(2.7), Inches(8), Inches(0.4),
              "PARTIE 01", size=14, color=T.TEAL, bold=True, ls=3)
    T.textbox(s, T.MARGIN, Inches(3.15), Inches(9.5), Inches(0.9),
              "Contexte & problématique", size=40, color=T.WHITE, bold=True,
              font=T.HEAD)
    T.rect(s, T.MARGIN, Inches(4.25), Inches(0.8), Inches(0.09), T.TEAL)
    T.note(s, "Première partie : pourquoi ce sujet et quelle est la question "
             "de recherche.")


def s4_context(prs):
    s = new(prs)
    T.chrome(s, "01 · CONTEXTE", "Pourquoi prévoir la production et la charge ?", 4)
    T.bullet_list(s, [
        "La transition énergétique rend le réseau allemand **plus volatil** : "
        "forte part d'éolien et de solaire, production **intermittente**.",
        "À l'horizon 2030, l'Allemagne viserait environ **80 %** "
        "d'électricité renouvelable : l'équilibrage offre/demande devient "
        "critique.",
        "De bonnes prévisions servent au **dispatching**, au **dimensionnement "
        "du stockage** et à la **fixation des prix** sur les marchés.",
        "Trois séries cibles : **charge**, **éolien**, **solaire**, à quatre "
        "horizons : **h = 5, 10, 24** heures et **5 040 h (~7 mois)**.",
    ], T.MARGIN, Inches(2.0), Inches(6.3))
    T.rrect(s, Inches(7.5), Inches(1.95), Inches(5.15), Inches(3.4),
            color=T.VIOLET_T, radius=0.1)
    T.textbox(s, Inches(7.85), Inches(2.3), Inches(4.5), Inches(0.5),
              "Question de recherche", size=16, color=T.VIOLET, bold=True,
              font=T.HEAD)
    T.textbox(s, Inches(7.85), Inches(2.9), Inches(4.5), Inches(2.2),
              "Quelle famille de modèles offre le meilleur compromis "
              "précision / robustesse sur les séries énergétiques "
              "allemandes, selon l'horizon de prévision ?", size=13.5,
              color=T.INK, spacing=1.2)
    T.note(s, "La question centrale : comparer les familles de modèles selon "
             "l'horizon. Court terme, un modèle linéaire peut suffire ; long "
             "terme, les réseaux de neurones prennent l'avantage.")


def s5_data(prs):
    s = new(prs)
    T.chrome(s, "01 · DONNÉES", "Le jeu de données ENTSO-E", 5)
    cards = [
        ("◷", "Fréquence", "Séries horaires en MW, horodatage UTC."),
        ("▦", "Volume", "50 400 observations, 3 variables endogènes."),
        ("◎", "Période", "1er janvier 2015 → 30 septembre 2020."),
        ("⚠", "Anomalie", "Effet COVID visible au printemps 2020."),
        ("✂", "Découpage", "90 % entraînement / 10 % test, anti-fuite."),
        ("✔", "Outils", "R (forecast, vars, rugarch) et Python (statsmodels, "
         "Keras)."),
    ]
    T.cards_grid(s, cards, T.MARGIN, Inches(1.95), T.CW, Inches(3.85),
                 cols=3, tints=[T.BLUE_T, T.TEAL_T, T.CORAL_T, T.AMBER_T,
                                T.VIOLET_T], accents=[T.BLUE, T.TEAL, T.CORAL,
                                                      T.AMBER, T.VIOLET])
    T.keybar(s, "Aucune donnée manquante ; le test démarre le 5 mars 2020, en "
               "pleine crise sanitaire.", accent=T.BLUE)
    T.note(s, "Les données sont propres et complètes. Le point d'attention est "
             "le COVID, qui rend la période de test structurellement "
             "différente de l'entraînement.")


def s6_div02(prs):
    s = new(prs)
    T.gradient(s, T.DARK, T.TEAL, 40.0)
    T.dots(s, Inches(10.0), Inches(1.0), 6, 6, Inches(0.3), Inches(0.075),
           T.TEAL, alpha=30)
    T.textbox(s, T.MARGIN, Inches(2.7), Inches(8), Inches(0.4),
              "PARTIE 02", size=14, color=T.BLUE, bold=True, ls=3)
    T.textbox(s, T.MARGIN, Inches(3.15), Inches(9.5), Inches(0.9),
              "Données & analyse exploratoire", size=40, color=T.WHITE,
              bold=True, font=T.HEAD)
    T.rect(s, T.MARGIN, Inches(4.25), Inches(0.8), Inches(0.09), T.BLUE)
    T.note(s, "Deuxième partie : comprenons la structure statistique des "
             "séries avant toute modélisation.")


def s7_eda(prs):
    s = new(prs)
    T.chrome(s, "02 · ANALYSE EXPLORATOIRE",
             "Saisonnalités et structure des séries", 7, accent=T.TEAL)
    T.figure(s, "py_ts_overview.png", T.MARGIN, Inches(1.95), Inches(7.5),
             Inches(3.85), "Superposition des trois séries horaires (2015-2020)")
    T.bullet_list(s, [
        "**Double saisonnalité** : cycle journalier (24 h) et cycle annuel "
        "(8 760 h).",
        "La **charge** présente des pics marqués matin et soir, plus bas le "
        "week-end.",
        "L'**éolien** est sporadique et volatile ; le **solaire** suit "
        "fidèlement l'ensoleillement.",
        "Une **tendance** de fond et des régimes météo créent des "
        "non-linéarités.",
    ], Inches(8.45), Inches(2.0), Inches(4.2), size=12.5, accent=T.TEAL)
    T.note(s, "On voit immédiatement les deux saisonnalités. La charge est la "
             "série la plus régulière et donc la plus prévisible ; le solaire "
             "est le plus difficile.")


def s8_stationarity(prs):
    s = new(prs)
    T.chrome(s, "02 · STATIONNARITÉ", "Tests de racine unitaire et "
             "différenciation", 8, accent=T.TEAL)
    T.bullet_list(s, [
        "**ADF** et **KPSS** appliqués à chaque série : les niveaux sont "
        "**non stationnaires**.",
        "Après différenciation d'ordre 1, les séries deviennent "
        "**stationnaires** → choix de **d = 1**.",
        "Saisonnalité journalière : différenciation de lag 24 (série horaire), "
        "confirmée par l'**ACF/PACF**.",
        "Ces tests guident le choix des ordres **p, d, q** des modèles ARIMA.",
    ], T.MARGIN, Inches(2.0), Inches(6.3))
    T.figure(s, "py_acf_pacf_Load_d1.png", Inches(7.5), Inches(1.95),
             Inches(5.15), Inches(3.85),
             "ACF / PACF de la charge différenciée : décroissances lentes")
    T.note(s, "ADF et KPSS convergent : une différenciation suffit. L'ACF qui "
             "décroît lentement signale la mémoire longue et la saisonnalité.")


def s9_method(prs):
    s = new(prs)
    T.chrome(s, "02 · MÉTHODOLOGIE",
             "Du nettoyage à l'évaluation", 9, accent=T.TEAL)
    steps = [
        ("1", "Préparation", "Nettoyage, gestion de la saisonnalité, split "
         "temporel 90/10."),
        ("2", "Statistique", "ARIMA, SARIMA, VAR/VECM, GARCH."),
        ("3", "Machine learning", "LSTM, GRU, Prophet, modèle hybride."),
        ("4", "Évaluation", "RMSE, MAPE, comparaison au naïve."),
    ]
    x = T.MARGIN
    gap = Inches(0.3)
    cw = int((T.CW - gap * 3) / 4)
    for num, title, body in steps:
        T.rrect(s, x, Inches(2.2), cw, Inches(2.9), color=T.WHITE,
                line=T.LINE, radius=0.12)
        T.rrect(s, x + Inches(0.28), Inches(2.48), Inches(0.6), Inches(0.6),
                color=T.TEAL, radius=0.3)
        T.textbox(s, x + Inches(0.28), Inches(2.48), Inches(0.6), Inches(0.6),
                  num, size=20, color=T.WHITE, bold=True, font=T.HEAD,
                  align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
        T.textbox(s, x + Inches(0.28), Inches(3.28), cw - Inches(0.56),
                  Inches(0.5), title, size=15, color=T.INK, bold=True,
                  font=T.HEAD)
        T.textbox(s, x + Inches(0.28), Inches(3.8), cw - Inches(0.56),
                  Inches(1.1), body, size=11.5, color=T.SLATE, spacing=1.15)
        x += cw + gap
    T.keybar(s, "Démarche reproductible : chaque modèle est ajusté en R et en "
               "Python, avec les mêmes découpages temporels.", accent=T.TEAL)
    T.note(s, "La méthodologie est identique pour toutes les familles afin que "
             "la comparaison soit équitable : mêmes données, mêmes fenêtres.")


def s10_div03(prs):
    s = new(prs)
    T.gradient(s, T.DARK, T.VIOLET, 40.0)
    T.dots(s, Inches(10.0), Inches(1.0), 6, 6, Inches(0.3), Inches(0.075),
           T.VIOLET, alpha=30)
    T.textbox(s, T.MARGIN, Inches(2.7), Inches(8), Inches(0.4),
              "PARTIE 03", size=14, color=T.AMBER, bold=True, ls=3)
    T.textbox(s, T.MARGIN, Inches(3.15), Inches(10.5), Inches(0.9),
              "Modélisation", size=40, color=T.WHITE, bold=True, font=T.HEAD)
    T.rect(s, T.MARGIN, Inches(4.25), Inches(0.8), Inches(0.09), T.AMBER)
    T.note(s, "Troisième partie : les six familles de modèles et leurs "
             "résultats.")


def s11_arima_table(prs):
    s = new(prs)
    T.chrome(s, "03 · ARIMA / SARIMA",
             "Ordres retenus par série et par outil", 11, accent=T.VIOLET)
    rows = [
        ("Série", "ARIMA (Python)", "ARIMA (R, auto)", "d"),
        ("Charge / Load", "(2,1,2)", "(2,1,1)", "1"),
        ("Éolien / Wind", "(1,1,1)", "(1,1,0)", "1"),
        ("Solaire / Solar", "(1,1,1)", "(1,1,1)", "1"),
    ]
    x, y = T.MARGIN, Inches(2.05)
    w, rh = T.CW, Inches(0.62)
    widths = [Inches(3.9), Inches(3.3), Inches(3.3), Inches(1.4)]
    for ri, row in enumerate(rows):
        cx = x
        for ci, val in enumerate(row):
            if ri == 0:
                T.rrect(s, cx, y, widths[ci], rh, color=T.VIOLET, radius=0.16)
                txtc, b = T.WHITE, True
            else:
                bgc = T.WHITE if ri % 2 else T.VIOLET_T
                T.rect(s, cx, y, widths[ci], Pt(0.75), T.LINE)
                T.rect(s, cx, y, widths[ci], rh, bgc)
                T.rect(s, cx, y, widths[ci], Pt(0.75), T.LINE)
                txtc, b = (T.INK if ci == 0 else T.SLATE), (ci == 0)
            T.textbox(s, cx, y, widths[ci], rh, val, size=12.5, color=txtc,
                      bold=b, align=PP_ALIGN.CENTER,
                      anchor=MSO_ANCHOR.MIDDLE)
            cx += widths[ci]
        y += rh
    T.bullet_list(s, [
        "Les ordres sont **proches** entre R et Python : les deux outils "
        "convergent.",
        "La saisonnalité journalière est capturée via un terme **SARIMA** "
        "(P,D,Q,24).",
    ], T.MARGIN, Inches(5.0), Inches(11.9), size=13, accent=T.VIOLET)
    T.note(s, "Les ordres sélectionnés par auto.arima en R et par statsmodels "
             "en Python sont très proches, ce qui renforce la confiance dans "
             "le choix des modèles.")


def s12_arima_res(prs):
    s = new(prs)
    T.chrome(s, "03 · ARIMA / SARIMA",
             "Précision sur la charge à court terme", 12, accent=T.VIOLET)
    T.stat_card(s, T.MARGIN, Inches(2.0), Inches(2.55), Inches(1.75),
                "899 MW", "RMSE · h = 10", T.VIOLET_T, T.VIOLET)
    T.stat_card(s, T.MARGIN + Inches(2.7), Inches(2.0), Inches(2.55),
                Inches(1.75), "1,4 %", "MAPE · h = 10", T.BLUE_T, T.BLUE)
    T.stat_card(s, T.MARGIN, Inches(3.95), Inches(2.55), Inches(1.75),
                "1 069 MW", "RMSE · h = 24", T.BLUE_T, T.BLUE)
    T.stat_card(s, T.MARGIN + Inches(2.7), Inches(3.95), Inches(2.55),
                Inches(1.75), "1,5 %", "MAPE · h = 24", T.TEAL_T, T.TEAL)
    T.figure(s, "R_prev_Load.png", Inches(5.95), Inches(1.95), Inches(6.7),
             Inches(3.85),
             "R (forecast) : prévision de la charge vs valeurs observées")
    T.note(s, "Sur l'horizon court, ARIMA/SARIMA atteint 899 MW de RMSE à 10 h "
             "sur la charge, soit 1,4 % d'erreur relative. C'est excellent.")


def s13_var_vecm(prs):
    s = new(prs)
    T.chrome(s, "03 · VAR / VECM", "Dynamique multivariée et réponse "
             "impulsionnelle", 13, accent=T.VIOLET)
    T.figure(s, "py_var_irf_load.png", T.MARGIN, Inches(1.95), Inches(7.5),
             Inches(3.85), "Fonctions de réponse impulsionnelle (IRF) sur la charge")
    T.bullet_list(s, [
        "**Test de causalité de Granger** : les trois séries "
        "s'influencent mutuellement.",
        "Coïntégration détectée (**Johansen**) → estimation d'un **VECM** à "
        "terme d'erreur.",
        "Les **IRF** quantifient l'effet d'un choc de production éolienne sur "
        "la charge sur 24 h.",
        "Approche **multivariée** utile car les variables ne sont pas "
        "indépendantes.",
    ], Inches(8.45), Inches(2.0), Inches(4.2), size=12.5, accent=T.VIOLET)
    T.note(s, "VAR et VECM exploitent les dépendances entre charge, éolien et "
             "solaire, contrairement à ARIMA qui traite chaque série "
             "séparément.")


def s14_garch(prs):
    s = new(prs)
    T.chrome(s, "03 · GARCH", "Modéliser la volatilité de l'éolien", 14,
             accent=T.CORAL)
    T.bullet_list(s, [
        "L'**éolien** présente une **volatilité conditionnelle** : les "
        "périodes calmes et agitées alternent.",
        "Un modèle **GARCH(1,1)** (via `rugarch` en R) capture le "
        "**clustering** de volatilité.",
        "Il fournit des **intervalles de prévision** réalistes qui "
        "s'élargissent lors des épisodes venteux extrêmes.",
        "Utile pour le **pilotage des marges** et la gestion du risque "
        "réseau.",
    ], T.MARGIN, Inches(2.0), Inches(6.3), accent=T.CORAL)
    T.figure(s, "R_garch_Wind.png", Inches(7.5), Inches(1.95), Inches(5.15),
             Inches(3.85),
             "R (rugarch) : volatilité conditionnelle du vent")
    T.note(s, "Le GARCH ne prédit pas la valeur du vent mais son amplitude de "
             "variation : les intervalles de prévision s'adaptent au régime de "
             "vent.")


def s15_lstm(prs):
    s = new(prs)
    T.chrome(s, "03 · DEEP LEARNING", "Récurrent : LSTM et GRU sous Keras", 15,
             accent=T.TEAL)
    T.figure(s, "py_lstm_gru_loss_Load.png", T.MARGIN, Inches(1.95),
             Inches(7.5), Inches(3.85),
             "Courbes de perte (MSE) de l'entraînement LSTM vs GRU")
    T.bullet_list(s, [
        "Réseaux **LSTM** et **GRU** entraînés sous **Keras/TensorFlow** avec "
        "fenêtres glissantes.",
        "Les modèles apprennent **mémoire longue + saisonnalité** sans "
        "feature engineering manuel.",
        "Convergence stable ; le **GRU**, plus léger, est souvent compétitif.",
        "En **walk-forward**, le LSTM généralise bien au COVID "
        "(790 / 705 / 1 295 MW).",
    ], Inches(8.45), Inches(2.0), Inches(4.2), size=12.5, accent=T.TEAL)
    T.note(s, "Les courbes de perte montrent une convergence rapide et sans "
             "sur-apprentissage marqué. Le walk-forward LSTM reste performant "
             "malgré la rupture COVID.")


def s16_hybrid(prs):
    s = new(prs)
    T.chrome(s, "03 · PROPHET & HYBRIDE",
             "Modèle hybride et tendances longues", 16, accent=T.AMBER)
    T.figure(s, "py_hybrid_Load.png", T.MARGIN, Inches(1.95), Inches(7.5),
             Inches(3.85),
             "Composition du modèle hybride (résidu + série)")
    T.bullet_list(s, [
        "**Prophet** décompose **tendance + saisonnalités + jours fériés**, "
        "très lisible.",
        "Le **modèle hybride** combine une partie **linéaire** (ARIMA) et une "
        "partie **non linéaire** (résidu appris).",
        "Excellent sur les **tendances longues**, le point faible des modèles "
        "purement statistiques.",
        "Amélioration notable sur l'horizon **5 040 h** face à la naïve.",
    ], Inches(8.45), Inches(2.0), Inches(4.2), size=12.5, accent=T.AMBER)
    T.note(s, "L'approche hybride sépare la structure linéaire exploitable par "
             "ARIMA de la part non linéaire laissée à un modèle souple : c'est "
             "très efficace sur l'horizon long.")


def s17_div04(prs):
    s = new(prs)
    T.gradient(s, T.DARK, T.CORAL, 40.0)
    T.dots(s, Inches(10.0), Inches(1.0), 6, 6, Inches(0.3), Inches(0.075),
           T.CORAL, alpha=30)
    T.textbox(s, T.MARGIN, Inches(2.7), Inches(8), Inches(0.4),
              "PARTIE 04", size=14, color=T.TEAL, bold=True, ls=3)
    T.textbox(s, T.MARGIN, Inches(3.15), Inches(11), Inches(0.9),
              "Évaluation & conclusion", size=40, color=T.WHITE, bold=True,
              font=T.HEAD)
    T.rect(s, T.MARGIN, Inches(4.25), Inches(0.8), Inches(0.09), T.TEAL)
    T.note(s, "Quatrième partie : comparons les modèles de façon rigoureuse et "
             "tirons les conclusions.")


def s18_eval(prs):
    s = new(prs)
    T.chrome(s, "04 · ÉVALUATION", "RMSE comparés entre les familles", 18,
             accent=T.CORAL)
    T.figure(s, "py_evaluation_rmse.png", T.MARGIN, Inches(1.95), Inches(8.0),
             Inches(3.85), "RMSE par modèle et par horizon (charge)")
    T.bullet_list(s, [
        "Métriques : **RMSE** (MW), **MAPE** (%), comparaison à la "
        "**persistance naïve**.",
        "À **h = 10**, ARIMA_auto (R) est le meilleur (**512** sur l'éolien).",
        "À **h = 5 040**, le LSTM (**11 838**) écrase SARIMA (**65 847**).",
        "Le **walk-forward** valide la robustesse face aux régimes changeants.",
    ], Inches(8.9), Inches(2.0), Inches(3.75), size=12, accent=T.CORAL)
    T.note(s, "Message clé : aucun modèle ne gagne partout. Le choix dépend de "
             "l'horizon. C'est le résultat le plus important du projet.")


def s19_ranking(prs):
    s = new(prs)
    T.chrome(s, "04 · SYNTHÈSE", "Quel modèle pour quel horizon ?", 19,
             accent=T.CORAL)
    cols = [
        ("COURT TERME", "h = 5 · 10 h", T.BLUE, T.BLUE_T,
         "ARIMA / SARIMA\n(charge : 899 MW)"),
        ("MOYEN TERME", "h = 24 h", T.TEAL, T.TEAL_T,
         "LSTM / GRU\n(robustes au profil horaire)"),
        ("LONG TERME", "h = 5 040 h", T.AMBER, T.AMBER_T,
         "Hybride & Prophet\n(tendances longues)"),
    ]
    x = T.MARGIN
    gap = Inches(0.3)
    cw = int((T.CW - gap * 2) / 3)
    for tag, hz, accent, tint, body in cols:
        T.rrect(s, x, Inches(2.0), cw, Inches(3.7), color=tint, radius=0.09)
        T.textbox(s, x + Inches(0.35), Inches(2.35), cw - Inches(0.7),
                  Inches(0.4), tag, size=13, color=accent, bold=True, ls=1.5)
        T.textbox(s, x + Inches(0.35), Inches(2.78), cw - Inches(0.7),
                  Inches(0.5), hz, size=24, color=T.INK, bold=True,
                  font=T.HEAD)
        T.rect(s, x + Inches(0.35), Inches(3.45), Inches(0.7), Inches(0.07),
               accent)
        T.textbox(s, x + Inches(0.35), Inches(3.85), cw - Inches(0.7),
                  Inches(1.6), body, size=14, color=T.SLATE, spacing=1.2)
        x += cw + gap
    T.keybar(s, "Il n'existe pas de modèle universel : la meilleure méthode "
               "dépend de l'horizon visé.", accent=T.CORAL)
    T.note(s, "Synthèse : court terme un modèle statistique, moyen terme un "
             "réseau récurrent, long terme une approche hybride avec "
             "tendance.")


def s20_dm(prs):
    s = new(prs)
    T.chrome(s, "04 · SIGNIFICATIVITÉ", "Test de Diebold-Mariano", 20,
             accent=T.CORAL)
    T.stat_card(s, T.MARGIN, Inches(2.1), Inches(3.7), Inches(1.9),
                "p < 1e-60", "Significativité des écarts de RMSE", T.CORAL_T,
                T.CORAL)
    T.rrect(s, T.MARGIN + Inches(4.0), Inches(2.1), Inches(8.6), Inches(1.9),
            color=T.TEAL_T, radius=0.12)
    T.textbox(s, T.MARGIN + Inches(4.35), Inches(2.4), Inches(8.0),
              Inches(1.3), "Les différences de précision entre modèles ne "
              "sont pas dues au hasard : elles sont **statistiquement "
              "significatives**.", size=15, color=T.INK, spacing=1.2)
    T.bullet_list(s, [
        "Le test **Diebold-Mariano** compare deux séries d'erreurs de "
        "prévision.",
        "Sur l'horizon long, l'avantage du **LSTM sur SARIMA** est "
        "hautement significatif.",
        "Résultat robuste sur l'ensemble des séries et des horizons testés.",
    ], T.MARGIN, Inches(4.35), Inches(11.9), size=13.5, accent=T.TEAL)
    T.note(s, "Le test DM confirme que les classements observés ne relèvent "
             "pas du bruit d'échantillonnage : les écarts sont réels et "
             "significatifs.")


def s21_dashboard(prs):
    s = new(prs)
    T.chrome(s, "04 · RESTITUTION", "Tableau de bord interactif Streamlit", 21,
             accent=T.CORAL)
    T.figure(s, "dashboard_overview.png", T.MARGIN, Inches(1.95), Inches(8.0),
             Inches(3.85), "Aperçu du dashboard : exploration et prévisions")
    T.bullet_list(s, [
        "**Dashboard Streamlit** pour explorer séries et prévisions "
        "interactivement.",
        "Palette cohérente avec les figures : surlignage des séries "
        "clés.",
        "Permet de **comparer les modèles** et de visualiser les erreurs en "
        "temps réel.",
        "Outil de **vulgarisation** pour un public non technique.",
    ], Inches(8.9), Inches(2.0), Inches(3.75), size=12, accent=T.CORAL)
    T.note(s, "Un tableau de bord Streamlit a été développé pour rendre les "
             "résultats explorables et compréhensibles par des non "
             "spécialistes.")


def s22_bilan(prs):
    s = new(prs)
    T.chrome(s, "04 · BILAN", "Ce que le projet démontre", 22, accent=T.CORAL)
    cards = [
        ("✓", "Démarche complète", "Exploration, modélisation et évaluation "
         "de six familles de modèles."),
        ("⇄", "Double implémentation", "Chaque modèle en R et en Python, "
         "résultats cohérents."),
        ("↗", "Effet de l'horizon", "Le meilleur modèle change avec "
         "l'horizon de prévision."),
        ("⚡", "Valeur pratique", "Prévisions utiles au réseau et à "
         "l'équilibrage offre/demande."),
    ]
    T.cards_grid(s, cards, T.MARGIN, Inches(2.0), T.CW, Inches(3.7), cols=2,
                 tints=[T.BLUE_T, T.TEAL_T, T.AMBER_T, T.CORAL_T],
                 accents=[T.BLUE, T.TEAL, T.AMBER, T.CORAL])
    T.note(s, "Le projet est complet : toutes les étapes clés d'un pipeline de "
             "séries temporelles ont été couvertes et comparées.")


def s23_limits(prs):
    s = new(prs)
    T.chrome(s, "04 · LIMITES", "Les limites à garder en tête", 23, accent=T.CORAL)
    T.bullet_list(s, [
        "Données **hors variables exogènes** : météo, prix, jours fériés non "
        "intégrés directement.",
        "La **période COVID** crée une rupture de distribution difficile à "
        "anticiper.",
        "Les modèles **deep learning** demandent des ressources de calcul "
        "importantes.",
        "Séries **non stationnaires** et non linéaires : les modèles "
        "linéaires plafonnent sur le long terme.",
    ], T.MARGIN, Inches(2.05), Inches(11.9), size=14)
    T.rrect(s, T.MARGIN, Inches(5.35), T.CW, Inches(0.95), color=T.AMBER_T,
            radius=0.12)
    T.textbox(s, T.MARGIN + Inches(0.35), Inches(5.35), T.CW - Inches(0.7),
              Inches(0.95), "Ces limites ouvrent naturellement sur des "
              "perspectives d'enrichissement du modèle.", size=13, color=T.INK,
              anchor=MSO_ANCHOR.MIDDLE)
    T.note(s, "Reconnaître les limites est essentiel : la météo et les "
             "facteurs exogènes sont la principale piste d'amélioration.")


def s24_perspectives(prs):
    s = new(prs)
    T.chrome(s, "04 · PERSPECTIVES", "Et maintenant ?", 24, accent=T.CORAL)
    cards = [
        ("☂", "Ajouter la météo", "Intégrer température, vent et "
         "ensoleillement comme variables exogènes."),
        ("⌘", "Modèles avancés", "Transformer, Temporal Fusion Transformer, "
         "apprentissage ensembliste."),
        ("↺", "Mise en production", "Réentraînement glissant et déploiement "
         "en temps réel."),
        ("€", "Valorisation", "Estimer les gains économiques des prévisions "
         "améliorées."),
    ]
    T.cards_grid(s, cards, T.MARGIN, Inches(2.0), T.CW, Inches(3.7), cols=2,
                 tints=[T.TEAL_T, T.VIOLET_T, T.BLUE_T, T.AMBER_T],
                 accents=[T.TEAL, T.VIOLET, T.BLUE, T.AMBER])
    T.note(s, "Les perspectives naturelles : enrichir les entrées, tester des "
             "architectures plus récentes et industrialiser le pipeline.")


def s25_thanks(prs):
    s = new(prs)
    T.gradient(s, T.DARK, T.DARK2, 40.0)
    T.dots(s, Inches(9.4), Inches(4.4), 7, 5, Inches(0.28), Inches(0.07),
           T.TEAL, alpha=30)
    T.circle(s, -Inches(2.2), Inches(3.6), Inches(7), T.BLUE, alpha=12)
    T.textbox(s, T.MARGIN, Inches(2.5), Inches(11), Inches(1.0),
              "Merci de votre attention", size=44, color=T.WHITE, bold=True,
              font=T.HEAD)
    T.rect(s, T.MARGIN, Inches(3.65), Inches(0.8), Inches(0.09), T.TEAL)
    T.textbox(s, T.MARGIN, Inches(3.95), Inches(9), Inches(0.6),
              "Questions & discussion", size=18, color=T.MUTED)
    T.textbox(s, T.MARGIN, Inches(5.9), Inches(11), Inches(0.4),
              "Prévision des séries temporelles énergétiques  ·  ENTSO-E  ·  "
              "R & Python", size=12, color=T.MUTED)
    T.note(s, "Nous arrivons à la fin : merci de votre attention, je suis "
             "disponible pour vos questions.")


def main():
    prs = Presentation()
    prs.slide_width = int(T.SW)
    prs.slide_height = int(T.SH)
    for fn in (s1_title, s2_agenda, s3_div01, s4_context, s5_data, s6_div02,
               s7_eda, s8_stationarity, s9_method, s10_div03, s11_arima_table,
               s12_arima_res, s13_var_vecm, s14_garch, s15_lstm, s16_hybrid,
               s17_div04, s18_eval, s19_ranking, s20_dm, s21_dashboard,
               s22_bilan, s23_limits, s24_perspectives, s25_thanks):
        fn(prs)
    prs.save(str(OUT))
    print(f"OK -> {OUT}  ({len(prs.slides._sldIdLst)} slides)")


if __name__ == "__main__":
    main()
