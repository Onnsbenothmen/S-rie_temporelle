# -*- coding: utf-8 -*-
"""
evaluation.py
=============
SECTION 6 (Python) - evaluation comparee des modeles.

Quatre blocs :
  1. LEADERBOARD : agrege les metriques produites par les scripts
     classiques (R et Python), LSTM/GRU (et, si presents, Prophet/hybride)
     en une table unique (results/tables/py_evaluation_ranking.csv),
     classement par RMSE.
  2. WALK-FORWARD 1 pas sur le test (5 040 h), origine glissante :
     modeles naif, saisonnier-naif (24 h), SARIMA retenu (R), LSTM et GRU.
     Chaque pas n'utilise que l'information disponible AVANT t.
  3. DIEBOLD-MARIANO : test TOUTES PAIRES (erreurs au carre) entre les
     modeles du walk-forward, avec correction petits echantillons
     Harvey-Leybourne-Newbold et variance HAC (Newey-West, retard h-1).
  4. TABLEAU DE COMPARAISON enrichi : metriques + complexite + cout de
     calcul + interpretabilite (exige au 8.2 du cahier des charges).

Sorties :
  results/tables/py_evaluation_ranking.csv
  results/tables/py_walkforward_metrics.csv
  results/tables/py_diebold_mariano.csv
  results/tables/py_model_comparison.csv
  results/figures/py_evaluation_rmse.png
  results/forecasts/py_walkforward_<v>.csv  (pour le dashboard)
"""

import os
os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "2")

import numpy as np
import pandas as pd
from scipy import stats

from data_preparation import PROJECT_ROOT, load_germany_series
from arima_var import na_interp_hour, R_AUTO_SEASONAL

TABLES = PROJECT_ROOT / "results" / "tables"
FIGURES = PROJECT_ROOT / "results" / "figures"
FORECASTS = PROJECT_ROOT / "results" / "forecasts"
MODELS = PROJECT_ROOT / "results" / "models"

VAL_H = 5040
WINDOW = 168
SEED = 123

# Modele classique retenu par variable (identique a R, section 3.1)
SARIMA_RETENU = {
    "Load": ((1, 1, 1), (1, 1, 1, 24)),
    "Wind": ((1, 1, 1), (1, 1, 1, 24)),
    "Solar": R_AUTO_SEASONAL["Solar"],
}

# Metadonnees qualitatives pour le tableau de comparaison (8.2 du CDC).
# "Complexite" = nb approx. de parametres estimes ; "Cout" = temps de calcul
# relatif observe ; "Interpretabilite" = lisibilite structurelle du modele.
MODEL_META = {
    "naif":            ("Baseline", 0, "Tres faible", "Tres elevee"),
    "saisonnier_naif": ("Baseline", 0, "Tres faible", "Tres elevee"),
    "ARIMA_auto":      ("Econometrique", 8, "Faible", "Elevee"),
    "SARIMA_manuel":   ("Econometrique", 6, "Faible", "Elevee"),
    "SARIMA_auto":     ("Econometrique", 8, "Faible", "Elevee"),
    "SARIMA":          ("Econometrique", 6, "Faible", "Elevee"),
    "LSTM":            ("Deep learning", 8600, "Eleve", "Faible"),
    "GRU":             ("Deep learning", 6500, "Eleve", "Faible"),
    "LSTM/GRU":        ("Deep learning", 8600, "Eleve", "Faible"),
    "Prophet":         ("Decomposition", 40, "Moyen", "Moyenne"),
    "Hybride_SARIMA_LSTM": ("Hybride", 8700, "Tres eleve", "Faible"),
}


# ---------------------------------------------------------------------------
# 1. leaderboard
# ---------------------------------------------------------------------------

def leaderboard():
    frames = []
    sources = [
        ("R_arima_metrics.csv", "R_clasique"),
        ("py_arima_metrics.csv", "Python_clasique"),
        ("py_lstm_gru_metrics.csv", "Python_LSTM_GRU"),
        ("py_prophet_metrics.csv", "Python_Prophet"),
        ("py_hybrid_metrics.csv", "Python_Hybride"),
    ]
    for f, src in sources:
        p = TABLES / f
        if not p.exists():
            print("manquant (ignore) :", p)
            continue
        d = pd.read_csv(p)
        d["Source"] = src
        frames.append(d)
    allm = pd.concat(frames, ignore_index=True)
    allm = allm[["Source", "Variable", "Modele", "Horizon",
                 "MSE", "RMSE", "MAE", "MAPE"]]
    allm = allm.sort_values(["Variable", "Horizon", "RMSE"])
    allm.to_csv(TABLES / "py_evaluation_ranking.csv", index=False)
    print("Leaderboard :", len(allm), "lignes -> py_evaluation_ranking.csv")
    for v in allm["Variable"].unique():
        for h in sorted(allm["Horizon"].unique()):
            sub = allm[(allm.Variable == v) & (allm.Horizon == h)]
            best = sub.loc[sub.RMSE.idxmin()]
            print(f"  {v} h={h} : meilleur = {best.Modele} "
                  f"({best.Source}) RMSE={best.RMSE:.1f}")
    return allm


# ---------------------------------------------------------------------------
# 2. walk-forward 1 pas
# ---------------------------------------------------------------------------

def _lstm_walkforward(y_scaled, start, model):
    import tensorflow as tf
    graph = tf.function(lambda x: model(x, training=False)[0, 0],
                        autograph=False)
    n = len(y_scaled)
    preds = np.empty(n - start)
    for k, i in enumerate(range(start, n)):
        x = np.asarray(y_scaled[i - WINDOW:i], dtype=np.float32)
        preds[k] = float(graph(tf.constant(x.reshape(1, WINDOW, 1))))
    return preds


def _sarima_walkforward(y_train, y_test, order, sorder):
    """Walk-forward 1 pas : etat de Kalman mis a jour sans re-estimation.

    Les parametres SARIMA sont estimes une seule fois sur le train, puis le
    filtre de Kalman est RE-APPLIQUE a la serie complete (train + test) avec
    refit=False : chaque prediction a un pas utilise les observations reelles
    disponibles jusqu'a t-1 (aucune re-estimation). C'est l'equivalent exact
    de la boucle append/forecast, mais en un seul balayage : la version
    incrementale recalculait la covariance d'etat sur tout l'historique et
    explosait en memoire (O(n^2), cf. bug corrige 2).
    """
    from statsmodels.tsa.statespace.sarimax import SARIMAX
    res = SARIMAX(y_train, order=order, seasonal_order=sorder,
                  enforce_stationarity=False,
                  enforce_invertibility=False).fit(
        disp=False, method="lbfgs", maxiter=100, low_memory=True)
    full = pd.concat([y_train, y_test])
    res_full = res.apply(full, refit=False)
    fc = res_full.get_prediction(start=len(y_train), end=len(full) - 1)
    return np.asarray(fc.predicted_mean, dtype=float)


def _deep_walkforward(full, ytr, n_train, v, kind):
    """Walk-forward 1 pas d'une architecture profonde sauvegardee."""
    from sklearn.preprocessing import MinMaxScaler
    from keras.models import load_model
    path = MODELS / f"lstm_gru_{v}_{kind}.keras"
    if not path.exists():
        path = MODELS / f"lstm_gru_{v}.keras"     # repli ancien nommage
    if not path.exists():
        raise FileNotFoundError(path)
    sc = MinMaxScaler().fit(np.asarray(ytr).reshape(-1, 1))
    mdl = load_model(path)
    y_s = sc.transform(np.asarray(full).reshape(-1, 1)).ravel()
    p_s = _lstm_walkforward(y_s, n_train, mdl)
    return sc.inverse_transform(p_s.reshape(-1, 1)).ravel()


def walk_forward():
    try:
        import keras           # noqa: F401
    except Exception as exc:   # noqa: BLE001
        print("keras indisponible :", exc)

    df = load_germany_series().copy()
    for v in ("Load", "Wind", "Solar"):
        df[v] = na_interp_hour(df[v])
    n = len(df)
    n_train = int(np.floor(0.90 * n))
    train = df.iloc[:n_train]
    test = df.iloc[n_train:]

    wf_metrics, errors, preds_ok = [], {}, {}
    for v in ("Load", "Wind", "Solar"):
        print(f"##### walk-forward {v} #####")
        ytr, yte = train[v], test[v]
        full = pd.concat([ytr, yte])
        err = {}

        # naif et saisonnier-naif : observations passees reelles
        err["naif"] = yte.values - full.shift(1).iloc[n_train:].values
        err["saisonnier_naif"] = yte.values - full.shift(24).iloc[n_train:].values

        # SARIMA retenu (R)
        try:
            order, sorder = SARIMA_RETENU[v]
            err["SARIMA"] = yte.values - _sarima_walkforward(ytr, yte, order, sorder)
        except Exception as exc:   # noqa: BLE001
            print(f"  SARIMA walk-forward ignore ({v}) : {exc}")

        # LSTM et GRU (modeles sauvegardes, recursion 1 pas)
        for kind in ("LSTM", "GRU"):
            try:
                err[kind] = yte.values - _deep_walkforward(full, ytr, n_train, v, kind)
            except Exception as exc:   # noqa: BLE001
                print(f"  {kind} walk-forward ignore ({v}) : {exc}")

        for lab, e in err.items():
            m = {"MSE": float(np.mean(e ** 2)),
                 "RMSE": float(np.sqrt(np.mean(e ** 2))),
                 "MAE": float(np.mean(np.abs(e))),
                 "Variable": v, "Modele": lab}
            wf_metrics.append(m)
            print(f"  {lab:16s} RMSE={m['RMSE']:.2f} MAE={m['MAE']:.2f}")
        errors[v] = err

        # export des previsions walk-forward pour le dashboard
        exp = pd.DataFrame({"Observe": yte.values}, index=yte.index)
        for lab in err:
            exp[lab] = yte.values - err[lab]
        FORECASTS.mkdir(parents=True, exist_ok=True)
        exp.to_csv(FORECASTS / f"py_walkforward_{v}.csv")
        preds_ok[v] = exp

    wf = pd.DataFrame(wf_metrics)[["Variable", "Modele", "MSE", "RMSE", "MAE"]]
    wf.to_csv(TABLES / "py_walkforward_metrics.csv", index=False)
    return wf, errors


# ---------------------------------------------------------------------------
# 3. Diebold-Mariano (toutes paires)
# ---------------------------------------------------------------------------

def diebold_mariano(e1, e2, h=1):
    """DM entre deux series d'erreurs ; correction HLN + variance HAC."""
    e1, e2 = np.asarray(e1, float), np.asarray(e2, float)
    mask = np.isfinite(e1) & np.isfinite(e2)
    e1, e2 = e1[mask], e2[mask]
    d = e1 ** 2 - e2 ** 2
    n = len(d)
    dbar = float(np.mean(d))
    gamma0 = float(np.mean((d - dbar) ** 2))
    var = gamma0
    for k in range(1, h):
        gamma = float(np.mean((d[:n - k] - dbar) * (d[k:] - dbar)))
        var += 2.0 * gamma
    if var <= 0:
        return np.nan, np.nan
    stat = dbar / np.sqrt(var / n)
    stat *= np.sqrt((n + 1 - 2 * h + h * (h - 1) / n) / n)   # HLN
    p = 2.0 * stats.t.sf(abs(stat), df=n - 1)
    return float(stat), float(p)


def dm_table(errors):
    """DM sur TOUTES les paires de modeles presentes par variable.

    Stat < 0 => le modele A a une erreur quadratique moyenne plus faible
    (donc meilleur) que B.
    """
    from itertools import combinations
    rows = []
    for v in ("Load", "Wind", "Solar"):
        err = errors.get(v, {})
        labs = [k for k in ("naif", "saisonnier_naif", "SARIMA", "LSTM", "GRU")
                if k in err]
        for a, b in combinations(labs, 2):
            stat, p = diebold_mariano(err[a], err[b], h=1)
            if not np.isfinite(stat):
                continue
            if p < 0.05:
                concl = f"{a} meilleur" if stat < 0 else f"{b} meilleur"
            else:
                concl = "non significatif"
            rows.append({"Variable": v, "A": a, "B": b,
                         "DM_stat": round(stat, 3), "p_value": p,
                         "Conclusion": concl})
    dm = pd.DataFrame(rows)
    dm.to_csv(TABLES / "py_diebold_mariano.csv", index=False)
    return dm


# ---------------------------------------------------------------------------
# 4. tableau de comparaison enrichi (metriques + complexite + interpretabilite)
# ---------------------------------------------------------------------------

def comparison_table(ranking):
    """Fusionne le classement RMSE avec les metadonnees qualitatives."""
    agg = (ranking.groupby("Modele")
           .agg(RMSE_median=("RMSE", "median"),
                RMSE_min=("RMSE", "min"),
                Par_variable=("Variable", "nunique"))
           .reset_index())
    rows = []
    for _, r in agg.iterrows():
        fam, par, cout, interp = MODEL_META.get(
            r["Modele"], ("Autre", np.nan, "n.d.", "n.d."))
        rows.append({
            "Modele": r["Modele"], "Famille": fam,
            "Parametres_approx": par, "Cout_calcul": cout,
            "Interpretabilite": interp,
            "RMSE_median": round(r["RMSE_median"], 1),
            "RMSE_min": round(r["RMSE_min"], 1),
            "Nb_variables": int(r["Par_variable"]),
        })
    comp = pd.DataFrame(rows).sort_values("RMSE_median")
    comp.to_csv(TABLES / "py_model_comparison.csv", index=False)
    print("\n===== TABLEAU DE COMPARAISON (complexite / interpretabilite) =====")
    print(comp.to_string(index=False))
    return comp


def plot_rmse(wf):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, axes = plt.subplots(1, 3, figsize=(17, 5))
    for ax, v in zip(axes, ("Load", "Wind", "Solar")):
        sub = wf[wf.Variable == v]
        ax.bar(sub.Modele, sub.RMSE)
        ax.set_title(f"Walk-forward 1 pas - {v}")
        ax.set_ylabel("RMSE")
        ax.tick_params(axis="x", rotation=30)
    fig.tight_layout()
    fig.savefig(FIGURES / "py_evaluation_rmse.png", dpi=130)
    plt.close(fig)


def main():
    np.random.seed(SEED)
    print("===== 1. Leaderboard =====")
    ranking = leaderboard()
    print("===== 2. Walk-forward 1 pas =====")
    wf, errors = walk_forward()
    print("===== 3. Diebold-Mariano (toutes paires) =====")
    dm = dm_table(errors)
    print(dm.to_string(index=False))
    print("===== 4. Tableau de comparaison enrichi =====")
    comparison_table(ranking)
    plot_rmse(wf)
    print("\nTermine : py_evaluation_ranking.csv, py_walkforward_metrics.csv, "
          "py_diebold_mariano.csv, py_model_comparison.csv, py_evaluation_rmse.png")
    return wf, dm


if __name__ == "__main__":
    main()
