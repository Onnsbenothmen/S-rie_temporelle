# -*- coding: utf-8 -*-
"""
garch.py
========
SECTION 3.3 (Python) - modelisation de la volatilite (ARCH / GARCH).

Transposition Python (package `arch`) du script R/06_GARCH.R :
  - ARMA(1,0)-GARCH(1,1) / GARCH(2,1) / EGARCH(1,1) sur les variations
    journalieres (D1) de Load, Wind et Solar ;
  - innovations t de Student (queues lourdes, cf. Jarque-Bera) ;
  - diagnostics : Ljung-Box sur residus standardises et carres,
    Jarque-Bera, persistance et demi-vie ;
  - graphique de la volatilite conditionnelle (les 3 plus forts sigma).

Correspondance des choix avec R/06_GARCH.R :
  - les series sont standardisees (moyenne 0, ecart-type 1) : la
    persistance (alpha+beta) est invariante d'echelle, mais le
    conditionnement de l'optimiseur est meilleur ;
  - persistance sGARCH = SOMME de TOUS les alpha + TOUS les beta
    (alpha2 inclus pour GARCH(2,1)) ; beta1 pour EGARCH ;
  - sorties prefixees `py_`.
"""

import warnings
from pathlib import Path

import numpy as np
import pandas as pd

from arch import arch_model
from scipy.stats import jarque_bera
from statsmodels.stats.diagnostic import acorr_ljungbox

from data_preparation import load_germany_series, PROJECT_ROOT

warnings.filterwarnings("ignore")

TABLES = PROJECT_ROOT / "results" / "tables"
FIGURES = PROJECT_ROOT / "results" / "figures"
TABLES.mkdir(parents=True, exist_ok=True)
FIGURES.mkdir(parents=True, exist_ok=True)

SEED = 123
np.random.seed(SEED)


# ---------------------------------------------------------------------------
# Diagnostics
# ---------------------------------------------------------------------------
def lb_pvalue(x, lag=12, fitdf=1):
    """p-value du test de Ljung-Box (autocorrelation)."""
    out = acorr_ljungbox(x, lags=[lag], return_df=True)
    return float(out["lb_pvalue"].iloc[0])


def persistance(params, modele):
    """Persistance de la volatilite (meme convention que R/06_GARCH.R)."""
    if modele == "EGARCH(1,1)":
        return float(params.get("beta[1]", np.nan))
    alphas = [v for k, v in params.items() if k.startswith("alpha")]
    betas = [v for k, v in params.items() if k.startswith("beta")]
    return float(np.nansum(alphas) + np.nansum(betas))


def demi_vie(pers):
    """Demi-vie du choc de volatilite (en jours)."""
    if 0 < pers < 1:
        return round(np.log(0.5) / np.log(pers), 1)
    return np.nan


# ---------------------------------------------------------------------------
# Ajustement d'un modele de volatilite
# ---------------------------------------------------------------------------
def garch_analysis(x, modele, p=1, q=1, dist="t"):
    """Ajuste un GARCH/EGARCH sur une serie numpy (variations journalieres).

    `modele` : 'GARCH' (sGARCH) ou 'EGARCH'. `p`,`q` : ordres ARCH/GARCH.
    Retourne (resultat_arch, dict_parametres) ou (None, None) en cas d'echec.
    """
    if modele == "EGARCH":
        am = arch_model(x, mean="AR", lags=1, vol="EGARCH", p=p, o=0, q=q, dist=dist)
    else:
        am = arch_model(x, mean="AR", lags=1, vol="GARCH", p=p, q=q, dist=dist)
    try:
        # maxiter releve : la surface de vraisemblance est tres plate pres
        # d'une persistance proche de 1 (Load en particulier) et SLSQP
        # atteint souvent la limite d'iterations par defaut.
        res = am.fit(disp="off", options={"maxiter": 10000})
        return res, dict(res.params)
    except Exception:  # noqa: BLE001 - echec d'optimisation -> modele ignore
        return None, None


# ---------------------------------------------------------------------------
# Pipeline principal
# ---------------------------------------------------------------------------
def run():
    df = load_germany_series()

    # Moyennes journalieres (comme R/06_GARCH.R) puis 1ere difference.
    daily = df.resample("D").mean()
    dseries = daily[["Load", "Wind", "Solar"]].diff().dropna()

    specs = [("GARCH(1,1)", "GARCH", 1, 1),
             ("GARCH(2,1)", "GARCH", 2, 1),
             ("EGARCH(1,1)", "EGARCH", 1, 1)]

    table_coef, table_diag, table_pers = [], [], []

    for v in ["Load", "Wind", "Solar"]:
        x = dseries[v].values.astype(float)
        x = (x - x.mean()) / x.std()  # standardisation (cf. R)

        fits = {}
        for nom, modele, p, q in specs:
            res, params = garch_analysis(x, modele, p, q)
            fits[nom] = res
            if res is None:
                print(f"Echec d'estimation : {v} {nom}")
                continue
            pers = persistance(params, nom)
            # Convergence "propre" sur la valeur brute (par ex. 1e-7 n'est
            # pas une vraie dynamique ARCH). Sur Load, SLSQP converge vers
            # une solution de coin (pers~0 = variance constante avec t nu->2,
            # ou pers~1 = IGARCH) : resultat conserve mais flagge, et le
            # phenomene discute dans le rapport (surface de vraisemblance
            # plate pres de la non-stationnarite).
            ok = (pers > 1e-6) and (pers < 1.0 - 1e-6)
            row = {
                "Variable": v, "Modele": nom,
                "mu": round(params.get("Const", params.get("mu", np.nan)), 3),
                "ar1": round(params.get("y[1]", params.get("ar.L1", np.nan)), 4),
                "omega": params.get("omega", np.nan),
                "alpha1": round(params.get("alpha[1]", np.nan), 4),
                "alpha2": round(params.get("alpha[2]", np.nan), 4),
                "beta1": round(params.get("beta[1]", np.nan), 4),
                "Persistance": round(pers, 4),
                "Demi_vie": demi_vie(pers),
                "Convergence_ok": bool(ok),
                "nu_t": round(params.get("nu", np.nan), 2),
                "AIC": round(res.aic / len(x), 2),
                "BIC": round(res.bic / len(x), 2),
            }
            table_coef.append(row)
            table_pers.append({"Variable": v, "Modele": nom,
                               "Persistance": round(pers, 4),
                               "Demi_vie": demi_vie(pers),
                               "Convergence_ok": bool(ok)})

        # Diagnostic du GARCH(1,1) de reference.
        f = fits.get("GARCH(1,1)")
        if f is not None:
            stdr = np.asarray(f.resid / f.conditional_volatility, dtype=float)
            stdr = stdr[~np.isnan(stdr)]  # NaN du 1er pas AR(1) si present
            jb = jarque_bera(stdr)
            table_diag.append({
                "Variable": v, "Modele": "GARCH(1,1)",
                "LB_res_12": lb_pvalue(stdr, 12, fitdf=1),
                "LB_res2_12": lb_pvalue(stdr ** 2, 12, fitdf=1),
                "JB_stat": round(jb.statistic, 2), "JB_p": jb.pvalue,
            })
            print(f"GARCH(1,1) {v} : LB(res) p={lb_pvalue(stdr,12,1):.3g} "
                  f"LB(res^2) p={lb_pvalue(stdr**2,12,1):.3g}")

            # Graphique : variations + volatilite conditionnelle (alignes
            # sur l'index de la serie differentiee).
            import matplotlib
            matplotlib.use("Agg")
            import matplotlib.pyplot as plt
            dates = dseries.index
            sig = pd.Series(f.conditional_volatility, index=dates) * dseries[v].std()
            fig, ax = plt.subplots(2, 1, figsize=(13, 7), sharex=True)
            ax[0].plot(dates, dseries[v].values, color="grey", lw=0.5)
            ax[0].plot(dates, sig.values, color="darkred", lw=1.2)
            ax[0].set_title(f"Variations journalieres de {v} et volatilite conditionnelle")
            ax[1].plot(dates, sig.values, color="darkred")
            ax[1].set_title(f"Volatilite conditionnelle (sigma) - GARCH(1,1) - {v}")
            idx3 = np.argsort(sig.values)[-3:]
            ax[1].scatter(dates[idx3], sig.values[idx3], color="black", zorder=5)
            for i in idx3:
                ax[1].annotate(str(dates[i].date()), (dates[i], sig.values[i]),
                               textcoords="offset points", xytext=(0, 5), fontsize=8)
            fig.tight_layout()
            fig.savefig(FIGURES / f"py_garch_{v}.png", dpi=130)
            plt.close(fig)

    pd.DataFrame(table_coef).to_csv(TABLES / "py_garch_coefficients.csv", index=False)
    pd.DataFrame(table_diag).to_csv(TABLES / "py_garch_diagnostics.csv", index=False)
    pd.DataFrame(table_pers).to_csv(TABLES / "py_garch_persistence.csv", index=False)

    print("\n=== py_garch_coefficients.csv ===")
    print(pd.DataFrame(table_coef).to_string(index=False))
    print("\n=== py_garch_diagnostics.csv ===")
    print(pd.DataFrame(table_diag).to_string(index=False))


if __name__ == "__main__":
    run()
