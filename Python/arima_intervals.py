# -*- coding: utf-8 -*-
"""
arima_intervals.py
==================
Intervalles de prediction a 95 % du MODELE SARIMA RETENU (par variable).

Pourquoi un script separe :
  les modeles SARIMA sont ajustes via statsmodels en mode low_memory=True
  (obligatoire : l'ajustement pleine memoire d'un SARIMA saisonnier sur
  45 360 points depasse la RAM disponible). Ce mode ne conserve pas la
  covariance de prevision -> get_forecast().conf_int() renvoie NaN.
  On recalcule donc l'IC du modele retenu avec pmdarima.ARIMA (memes
  ordres), execute dans son propre processus pour disposer de toute la RAM.

Le script lit results/tables/py_arima_model_comparison.csv pour identifier
le modele retenu par variable (AICc minimal), complete
results/tables/py_arima_intervals.csv (deja alimente pour ARIMA_auto par
arima_var.py) et trace la bande a 95 % sur results/figures/py_prev_<v>.png.

Usage :
    python Python/arima_intervals.py                 # toutes les variables
    python Python/arima_intervals.py Wind Solar      # une passe par variable
                                                      # (1 processus = 1 fit)
"""

import gc
import sys

import numpy as np
import pandas as pd

from data_preparation import PROJECT_ROOT, load_germany_series
from arima_var import na_interp_hour, R_AUTO_SEASONAL

TABLES = PROJECT_ROOT / "results" / "tables"
FIGURES = PROJECT_ROOT / "results" / "figures"

HORIZONS = (5, 10, 24)


def retained_models():
    comp = pd.read_csv(TABLES / "py_arima_model_comparison.csv")
    best = {}
    for v, sub in comp.groupby("Variable"):
        best[v] = sub.loc[sub["AICc"].idxmin(), "Modele"]
    return best


def seasonal_orders(v, choix):
    if choix == "SARIMA_manuel":
        return (1, 1, 1), (1, 1, 1, 24)
    if choix == "SARIMA_auto":
        return R_AUTO_SEASONAL[v]
    raise ValueError(choix)


def main():
    df = load_germany_series().copy()
    for v in ("Load", "Wind", "Solar"):
        df[v] = na_interp_hour(df[v])
    n = len(df)
    n_train = int(np.floor(0.90 * n))
    train, test = df.iloc[:n_train], df.iloc[n_train:]

    best = retained_models()
    print("Modeles retenus :", best)

    demande = [a for a in sys.argv[1:] if a in ("Load", "Wind", "Solar")]
    variables = demande or ["Load", "Wind", "Solar"]
    print("Variables traitees :", variables, flush=True)

    existing = TABLES / "py_arima_intervals.csv"
    base = pd.read_csv(existing) if existing.exists() else pd.DataFrame()
    # on repart uniquement des lignes non saisonnieres (ARIMA_auto)
    if not base.empty:
        base = base[~base["Modele"].isin(["SARIMA_manuel", "SARIMA_auto"])]

    rows = []
    for v in variables:
        choix = best.get(v)
        if choix == "ARIMA_auto":
            print(f"{v} : {choix} -> IC deja fourni par arima_var.py")
            continue
        try:
            from pmdarima.arima import ARIMA
            order, sorder = seasonal_orders(v, choix)
            print(f"{v} : ajustement pmdarima {order}x{sorder} ...", flush=True)
            m = ARIMA(order=order, seasonal_order=sorder,
                      suppress_warnings=True, maxiter=10).fit(train[v])
            pr, ci = m.predict(n_periods=max(HORIZONS),
                               return_conf_int=True, alpha=0.05)
            for h in HORIZONS:
                for step in range(1, h + 1):
                    rows.append({
                        "Variable": v, "Modele": choix, "Horizon": h,
                        "step": step, "mean": float(pr[step - 1]),
                        "lower": float(ci[step - 1, 0]),
                        "upper": float(ci[step - 1, 1]),
                    })
            _plot(v, choix, train, test, pr, ci)
            print(f"{v} : IC OK", flush=True)
            del m
            gc.collect()
        except Exception as exc:   # noqa: BLE001
            print(f"{v} : IC ignorés ({exc})")

    new = pd.DataFrame(rows)
    if new.empty:
        print("Aucune nouvelle ligne : la table existante est laissee en l'etat.")
        return
    # fusion ADDITIVE et idempotente : on part de la table existante, on
    # concatene les nouvelles lignes, puis on deduplique sur la cle
    # (Variable, Modele, Horizon, step) en gardant la version la plus recente.
    if not base.empty:
        out = pd.concat([base, new], ignore_index=True)
    else:
        out = new
    key = ["Variable", "Modele", "Horizon", "step"]
    out = out.drop_duplicates(subset=key, keep="last")
    cols = ["Variable", "Modele", "Horizon", "step", "mean", "lower", "upper"]
    out = out[[c for c in cols if c in out.columns]]
    out = out.sort_values(["Variable", "Modele", "Horizon", "step"])
    out.to_csv(TABLES / "py_arima_intervals.csv", index=False)
    print("Table ecrite :", TABLES / "py_arima_intervals.csv",
          f"({len(out)} lignes)")


def _plot(v, choix, train, test, pr, ci):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    idx = test.iloc[:24].index
    fig, ax = plt.subplots(figsize=(13, 6))
    hist = train[v].iloc[-24 * 21:]
    ax.plot(hist.index, hist.values, label="Historique (train)")
    ax.plot(idx, test[v].iloc[:24].values, label="Observe (test)")
    ax.plot(idx, pr[:24], "r--", label=f"Prevision {choix}")
    ax.fill_between(idx, ci[:24, 0], ci[:24, 1], color="red", alpha=0.15,
                    label="Intervalle 95 %")
    ax.set_title(f"Prevision {choix} - {v} (h=24) + IC 95 %")
    ax.legend()
    fig.tight_layout()
    fig.savefig(FIGURES / f"py_prev_{v}.png", dpi=130)
    plt.close(fig)


if __name__ == "__main__":
    main()
