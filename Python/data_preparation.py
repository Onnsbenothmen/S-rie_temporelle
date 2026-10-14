# -*- coding: utf-8 -*-
"""
data_preparation.py
===================
Chargement et préparation des données énergétiques allemandes
(ENSO-E / Open Power System Data), fréquence horaire.

Pourquoi ce module séparé ?
----------------------------
Toutes les analyses (EDA, stationnarité, modélisation) doivent lire
les DONNÉES DANS LE MÊME FORMAT natif (DatetimeIndex + freq='h').
Un seul point d'entrée garantit cohérence et reproductibilité :
aucun chemin en dur dans les notebooks, la source vit ici.
"""

from pathlib import Path

import pandas as pd

# Racine du projet : deux niveaux au-dessus de Python/ (Python -> projet)
PROJECT_ROOT = Path(__file__).resolve().parent.parent

RAW_CSV = PROJECT_ROOT / "data" / "raw" / "time_series_60min_singleindex.csv"
PROCESSED_CSV = PROJECT_ROOT / "data" / "processed" / "germany_energy_analysis.csv"

# ==> Pourquoi ces colonnes ?
# Le fichier brut couvre toute l'Europe ; on ne conserve que les séries
# allemandes réellement mesurées : consommation, éolien total, solaire.
# (l'éolien total = onshore + offshore, déjà agrégé par le fournisseur).
COLUMNS_RAW = {
    "utc_timestamp": "DateTime",
    "DE_load_actual_entsoe_transparency": "Load",
    "DE_wind_generation_actual": "Wind",
    "DE_solar_generation_actual": "Solar",
}

# ==> Pourquoi un début en 2015 ?
# La première observation (31/12/2014 23h) est entièrement vide ;
# les tests de continuité ont montré que 01/01/2015 00:00 marque la
# première heure complète. On conserve ainsi 5,75 ans (>= 3 ans exigés).
ANALYSIS_START = "2015-01-01 00:00:00"


def load_raw_germany():
    """Lit le fichier brut ENTSO-E et ne garde que les colonnes Allemagne.

    Retourne un DataFrame avec un index DatetimeIndex exploitable
    (tri chronologique + suppression de la ligne vide initiale).
    """
    # low_memory=False : pandas évite d'inférer le dtype par blocs,
    # ce qui gère proprement les lignes à fortes proportions de NA.
    df = pd.read_csv(
        RAW_CSV,
        usecols=list(COLUMNS_RAW.keys()),
        low_memory=False,
    ).rename(columns=COLUMNS_RAW)

    # Timestamps UTC déjà présents chez le fournisseur -> pas d'ambiguïté
    # d'heure d'été ; c'est ce qui permet une fréquence strictement horaire.
    df["DateTime"] = pd.to_datetime(df["DateTime"], utc=True)

    # Tri chronologique + suppression des lignes sans timestamp.
    df = df.sort_values("DateTime").dropna(subset=["DateTime"])

    return df.reset_index(drop=True)


def load_germany_series():
    """Charge la version analytique déjà nettoyée (2015-01-01 debut).

    Retourne un DataFrame aux VAR native pandas : index DatetimeIndex
    UTC, fréquence déclarée 'h' (60 min). Les NA de Wind/Solar sont
    conservés ici : leur traitement (interpolation) sera justifié au
    moment de la modélisation, pas avant.
    """
    if PROCESSED_CSV.exists():
        df = pd.read_csv(PROCESSED_CSV)
    else:
        # Repli : reconstruire la version analytique à partir du brut.
        df = load_raw_germany()
        df = df[df["DateTime"] >= pd.Timestamp(ANALYSIS_START, tz="UTC")]

    df["DateTime"] = pd.to_datetime(df["DateTime"], utc=True)
    df = df.sort_values("DateTime").set_index("DateTime")

    # ==> Pourquoi asfreq('h') silencieux ici ?
    # On veut un objet ts natif avec une fréquence déclarée. asfreq
    # impose une grille horaire régulière et révélerait les trous
    # éventuels (ici il n'y en a pas : vérifié dans 01_donnees).
    df = df.asfreq("h")

    return df


def chronological_split(df, train_ratio=0.90):
    """Découpage chronologique 90% / 10%, jamais aléatoire.

    PRÉCAUTION MÉTHODOLOGIQUE : en séries temporelles un split
    aléatoire fuiterait l'information future dans le train et
    favoriserait artificiellement les modèles. On coupe donc
    uniquement à la date n_train.
    """
    n = len(df)
    n_train = int(round(train_ratio * n))
    return df.iloc[:n_train], df.iloc[n_train:]