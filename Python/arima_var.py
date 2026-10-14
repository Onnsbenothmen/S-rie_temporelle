# -*- coding: utf-8 -*-
"""
arima_var.py
============
SECTION 3 (Python) - transposition 1-pour-1 du socle classique R.

Ce module reproduit en Python (statsmodels / pmdarima) le contenu de :
  - R/04_ARIMA_SARIMA.R   -> section 3.1 : ARIMA / SARIMA
  - R/05_VAR_VECM.R       -> section 3.2 : VAR / Granger / Johansen / VECM

Methode COMMUNE avec le script R (comparabilite point a point) :
  * donnees   : data/processed/germany_energy_analysis.csv (2015-2020)
  * NA        : interpolation sensible a la saisonnalite intra-journaliere
  * split     : chronologique 90% / 10% (jamais aleatoire, anti-fuite)
  * selection : AICc minimal parmi les candidats ARIMA / SARIMA
  * metriques : MSE / RMSE / MAE / MAPE (Solar jamais divise par 0)

Differences assumees et documentees dans le rapport :
  - l'ordre "SARIMA_auto" est l'ordre retenu par auto.arima (R) ; la version
    saisonniere de pmdarima (port python d'auto.arima) crash en memoire sur
    45 000 observations obsevrees -> on refitte les ordres R via SARIMAX.
    La recherche AUTO non saisonniere est par contre bien independante :
    pmdarima retrouve exactement ARIMA(5,1,1) pour Load comme auto.arima.
  - le test de Johansen (statsmodels) impose la constante HORS de l'espace
    de cointegration ; les statistiques de trace sont identiques a celles
    de ca.jo (R) mais les valeurs critiques different. On utilise donc le
    tableau Osterwald-Lenum / urca (constante RESTREINTE a l'espace de
    cointegration, config "ecdet = const") pour la decision du rang, afin
    que le rang retenu (r = 2) soit comparable a R.
  - statsmodels calcule le VECM en unites standardisees puis on re-exprime
    beta / alpha dans les unites MW d'origine (la statistique de trace de
    Johansen est invariante par changement d'echelle des colonnes).
"""

import warnings

warnings.filterwarnings("ignore")

import numpy as np
import pandas as pd

from scipy import stats
from statsmodels.tsa.statespace.sarimax import SARIMAX
from statsmodels.stats.diagnostic import acorr_ljungbox
from statsmodels.tsa.stattools import grangercausalitytests
from statsmodels.tsa.vector_ar.var_model import VAR
from statsmodels.tsa.vector_ar.vecm import coint_johansen, VECM, VECMResults

from data_preparation import PROJECT_ROOT, load_germany_series

TABLES = PROJECT_ROOT / "results" / "tables"
FIGURES = PROJECT_ROOT / "results" / "figures"
TABLES.mkdir(parents=True, exist_ok=True)
FIGURES.mkdir(parents=True, exist_ok=True)

VARIABLES = ["Load", "Wind", "Solar"]
N_PER_DAY = 24
HORIZONS = [5, 10, 24, 5040]       # section 6 : h=5 a 10 pas + documentation h=5040
INTERVAL_HORIZONS = (5, 10, 24)    # intervalles de prediction (modeles a IC disponibles)
TEST_H = 5040                      # longueur du jeu de test (10 % de 50400)

# Ordres auto.arima (R) refoits ici via SARIMAX (section 3.1, modele 3)
R_AUTO_SEASONAL = {
    "Load":  ((2, 1, 2), (1, 1, 0, 24)),
    "Wind":  ((1, 1, 2), (1, 0, 0, 24)),
    "Solar": ((2, 1, 2), (0, 1, 1, 24)),
}

# Ordres SARIMA RETENUS par variable (AICc minimal, section 3.1)
SARIMA_RETENU = {
    "Load":  ((1, 1, 1), (1, 1, 1, 24)),
    "Wind":  ((1, 1, 1), (1, 1, 1, 24)),
    "Solar": R_AUTO_SEASONAL["Solar"],
}

# ---------------------------------------------------------------------------
# HELPERS COMMUNS
# ---------------------------------------------------------------------------

def na_interp_hour(series):
    """Interpolation des NA horaires sensible a la saisonnalite (24h).

    Analogue de forecast::na.interp : on retire la moyenne par heure de la
    journee, on interpole LINEAIREMENT le residu (les NA sont des heures
    isolees), puis on rajoute la saisonnalite. Ne combine pas avec forecast
    pour rester dans la pile Python (numpy/pandas uniquement).
    """
    hour_means = series.groupby(series.index.hour).transform("mean")
    resid = series - hour_means
    resid = resid.interpolate("linear")
    resid = resid.fillna(resid.bfill().fillna(0.0))     # extremites le cas echeant
    return resid + hour_means


def mape_ignore_zero(actual, predicted):
    """MAPE en % sans division par zero (Solar est a 0 la nuit)."""
    a = np.asarray(actual)
    p = np.asarray(predicted)
    mask = a != 0
    return float(np.mean(np.abs((a[mask] - p[mask]) / a[mask])) * 100)


def metrics(actual, predicted):
    """MSE / RMSE / MAE / MAPE, signature identique a la fonction R."""
    e = np.asarray(actual) - np.asarray(predicted)
    return {
        "MSE": float(np.mean(e ** 2)),
        "RMSE": float(np.sqrt(np.mean(e ** 2))),
        "MAE": float(np.mean(np.abs(e))),
        "MAPE": float(mape_ignore_zero(actual, predicted)),
    }


def build_lags(x, q):
    """Matrice de 1..q retards (l'equivalent R de build_lags)."""
    n = len(x)
    out = np.full((n, q), np.nan)
    for k in range(1, q + 1):
        if k < n:
            out[k:, k - 1] = x[:-k]
    return out


def arch_lm_test(resid, q=12):
    """Test ARCH-LM manuel (meme implementation que le script R).

    H0 : "pas d'effet ARCH" -> on regresse e^2 sur ses 12 retards et on
    utilise LM = n * R^2 ~ chi2(q).
    """
    e2 = np.asarray(resid) ** 2
    lagged = build_lags(e2, q)
    x = np.column_stack([np.ones(len(e2)), lagged])
    m = ~np.isnan(x).any(axis=1)
    y, X = e2[m], x[m]
    beta, *_ = np.linalg.lstsq(X, y, rcond=None)
    yhat = X @ beta
    ssres = float(np.sum((y - yhat) ** 2))
    sstot = float(np.sum((y - y.mean()) ** 2))
    r2 = 1.0 - ssres / sstot
    stat = len(y) * r2
    p = float(stats.chi2.sf(stat, q))
    return stat, p


def aicc_of(aic, k, n):
    """AIC corrige (petit echantillon) : aic + 2k(k+1)/(n-k-1)."""
    if n - k - 1 <= 0:
        return np.nan
    return aic + 2.0 * k * (k + 1) / (n - k - 1)


# ---------------------------------------------------------------------------
# SECTION 3.1 - ARIMA / SARIMA
# ---------------------------------------------------------------------------

def diagnostics_arima(resid, model_df, nom):
    """Diagnostic identique a 'diagnostiquer' du script R.

    Ljung-Box lag 24 (fitdf = p+q+P+Q), Jarque-Bera, ARCH-LM 12 retards.
    Le premier residu du filtre de Kalman peut etre NaN : on l'ecarte
    (comme stats::residuals qui ne renvoie aucun NA).
    """
    resid = np.asarray(resid, dtype=float)
    resid = resid[np.isfinite(resid)]
    lb = acorr_ljungbox(resid, lags=[24], model_df=model_df, return_df=True)
    jb = stats.jarque_bera(resid)
    arch_stat, arch_p = arch_lm_test(resid, q=12)
    return {
        "Variable": nom,
        "LB_stat": round(float(lb["lb_stat"].iloc[0]), 2),
        "LB_p": float(lb["lb_pvalue"].iloc[0]),
        "JB_stat": round(float(jb.statistic), 2),
        "JB_p": float(jb.pvalue),
        "ARCH_stat": round(arch_stat, 2),
        "ARCH_p": arch_p,
        "LjungBox_OK": bool(lb["lb_pvalue"].iloc[0] > 0.05),
        "JB_normal_OK": bool(jb.pvalue > 0.05),
        "ARCH_absent": bool(arch_p > 0.05),
    }


def fit_manuel(tr):
    """SARIMA(1,1,1)(1,1,1)_24 guide par l'ACF/PACF (identique au R)."""
    return SARIMAX(
        tr, order=(1, 1, 1), seasonal_order=(1, 1, 1, 24),
        enforce_stationarity=False, enforce_invertibility=False,
    ).fit(disp=False, method="lbfgs", maxiter=100, low_memory=True)


def fit_auto_nonseasonal(tr):
    """Recherche AUTO non saisonniere (pmdarima, port d'auto.arima).

    d force a 1 (EDA). pmdarima retrouve de maniere independante les memes
    ordres que auto.arima(R) : verifie sur Load -> ARIMA(5,1,1).
    """
    from pmdarima.arima import auto_arima
    return auto_arima(
        tr, d=1, seasonal=False, stepwise=True, approximation=True,
        suppress_warnings=True, error_action="ignore",
    )


def fit_auto_seasonal(tr, v):
    """SARIMA selectionne par auto.arima (R), refitte ici via SARIMAX.

    pmdarima (version saisonniere) crash en memoire sur 45 000 points ;
    ordres R documentes dans R_AUTO_SEASONAL.
    """
    order, sorder = R_AUTO_SEASONAL[v]
    return SARIMAX(
        tr, order=order, seasonal_order=sorder,
        enforce_stationarity=False, enforce_invertibility=False,
    ).fit(disp=False, method="lbfgs", maxiter=200, low_memory=True)


def spec_str(model, seasonal):
    """Spec au format R ("ARIMA1,1,1,1,1,1,24" / "ARIMA5,1,1")."""
    if hasattr(model, "order") and not hasattr(model, "model"):
        # modele pmdarima (auto_arima)
        o = tuple(model.order) + tuple(model.seasonal_order) if seasonal \
            else tuple(model.order)
    else:
        # resultat statsmodels SARIMAX (ordre accessible via .model)
        o = tuple(model.model.order) + tuple(model.model.seasonal_order) \
            if seasonal else tuple(model.model.order)
    return "ARIMA" + ",".join(str(x) for x in o)


def section_arima(df):
    """Reproduit R/04_ARIMA_SARIMA.R : tableaux comparaison/diag/metriques."""
    n = len(df)
    n_train = int(np.floor(0.90 * n))
    dfi = df.copy()
    for v in VARIABLES:
        dfi[v] = na_interp_hour(dfi[v])
    train = dfi.iloc[:n_train]
    test = dfi.iloc[n_train:]

    table_comp, table_diag, table_met, table_int = [], [], [], []

    for v in VARIABLES:
        print(f"\n##### SERIE : {v} #####")

        manuel = fit_manuel(train[v])
        auto_ar = fit_auto_nonseasonal(train[v])
        auto_sa = fit_auto_seasonal(train[v], v)

        k_m = len(manuel.params)
        k_a = auto_ar.arima_res_.params.size
        k_s = len(auto_sa.params)
        comp = pd.DataFrame({
            "Variable": v,
            "Modele": ["SARIMA_manuel", "ARIMA_auto", "SARIMA_auto"],
            "AIC": [manuel.aic, auto_ar.aicc(), auto_sa.aic],
            "AICc": [
                aicc_of(manuel.aic, k_m, n_train),
                auto_ar.aicc(),
                aicc_of(auto_sa.aic, k_s, n_train),
            ],
            "BIC": [manuel.bic, auto_ar.bic(), auto_sa.bic],
            "Spec": [
                spec_str(manuel, True),
                spec_str(auto_ar, False),
                spec_str(auto_sa, True),
            ],
        })
        table_comp.append(comp)
        print(comp.to_string(index=False))

        i_best = int(np.argmin(comp["AICc"]))
        choix = comp["Modele"].iloc[i_best]
        print(f"Modele retenu (AICc minimal) : {choix}")

        if choix == "SARIMA_manuel":
            meilleur = manuel
        elif choix == "ARIMA_auto":
            meilleur = None          # traite ci-dessous via auto_ar
        else:
            meilleur = auto_sa

        # Diagnostic des residus du meilleur modele
        if choix == "ARIMA_auto":
            resid = auto_ar.arima_res_.resid
            model_df = auto_ar.order[0] + auto_ar.order[2]
        else:
            resid = meilleur.resid
            p, d, q = meilleur.model.order
            sp, sd, sq, sm = meilleur.model.seasonal_order
            model_df = p + q + sp + sq
        table_diag.append(diagnostics_arima(np.asarray(resid), model_df, v))
        print(f"Diagnostic {v} : " + str(table_diag[-1]))

        # Graphique des residus (style checkresiduals)
        try:
            import matplotlib
            matplotlib.use("Agg")
            import matplotlib.pyplot as plt
            fig, ax = plt.subplots(2, 2, figsize=(13, 8))
            ax[0, 0].plot(resid, lw=0.5)
            ax[0, 0].set_title(f"Residus - {choix} - {v}")
            ax[0, 1].acorr(np.nan_to_num(resid), maxlags=40)
            ax[0, 1].set_title("ACF residus")
            ax[1, 0].hist(resid, bins=60)
            ax[1, 0].set_title("Distribution des residus")
            stats.probplot(resid[~np.isnan(resid)], dist="norm", plot=ax[1, 1])
            ax[1, 1].set_title("QQ-plot normal")
            fig.tight_layout()
            fig.savefig(FIGURES / f"py_resid_{v}.png", dpi=130)
            plt.close(fig)
        except Exception as exc:   # noqa: BLE001 - graphique non bloquant
            print("figure residus ignoree :", exc)

        # Previsions ponctuelles h = 5, 10, 24, 5040 pour les trois candidats.
        # NB : l'intervalle de prediction n'est PAS recolte ici pour les
        # modeles statsmodels ajustes en low_memory (leur covariance de
        # prevision n'est pas conservee -> IC = NaN). On obtient les IC du
        # modele RETENU juste apres, via pmdarima (voir plus bas).
        for lab, mdl, seasonal in [("SARIMA_manuel", manuel, True),
                                   ("ARIMA_auto", auto_ar, False),
                                   ("SARIMA_auto", auto_sa, True)]:
            for h in HORIZONS:
                try:
                    if seasonal:
                        fc = pd.Series(mdl.get_forecast(steps=h).predicted_mean)
                    else:
                        fc = pd.Series(mdl.predict(n_periods=h))
                    m = metrics(np.asarray(test[v].iloc[:h]),
                                np.asarray(fc.iloc[:h]))
                    m.update({"Variable": v, "Modele": lab, "Horizon": h})
                    table_met.append(m)
                except Exception as exc:   # noqa: BLE001
                    print(f"echec prevision {lab}/{v}/h={h} : {exc}")

        # Intervalles de prediction a 95 % du MODELE RETENU (h = 5, 10, 24).
        # Uniquement pour le candidat pmdarima ARIMA_auto, qui expose l'IC de
        # facon fiable. Pour les specifications SARIMA (statsmodels), l'IC est
        # calcule par le script dedie arima_intervals.py (processus separe,
        # la prevision d'IC saisonniere exigeant un ajustement memoire lourd).
        int_ret = None
        if choix == "ARIMA_auto":
            try:
                pr, ci = auto_ar.predict(n_periods=max(INTERVAL_HORIZONS),
                                         return_conf_int=True, alpha=0.05)
                pr = np.asarray(pr)
                int_ret = {"mean": pr, "lo": ci[:, 0], "hi": ci[:, 1]}
                for h in INTERVAL_HORIZONS:
                    for step in range(1, h + 1):
                        table_int.append({
                            "Variable": v, "Modele": choix, "Horizon": h,
                            "step": step, "mean": float(pr[step - 1]),
                            "lower": float(ci[step - 1, 0]),
                            "upper": float(ci[step - 1, 1]),
                        })
            except Exception as exc:   # noqa: BLE001
                print(f"intervalles ignorees ({choix}/{v}) : {exc}")

        # Graphique de prevision h=24 du modele retenu (+ bande a 95 % si dispo)
        if int_ret is not None:
            prev_mdl = pd.Series(int_ret["mean"][:24],
                                 index=test.iloc[:24].index)
            lo24, hi24 = int_ret["lo"][:24], int_ret["hi"][:24]
        elif choix == "ARIMA_auto":
            prev_mdl = pd.Series(
                auto_ar.predict(n_periods=24), index=test.iloc[:24].index)
            lo24, hi24 = None, None
        else:
            getf = meilleur.get_forecast(steps=24)
            prev_mdl = pd.Series(getf.predicted_mean,
                                 index=test.iloc[:24].index)
            lo24, hi24 = None, None
        try:
            import matplotlib
            matplotlib.use("Agg")
            import matplotlib.pyplot as plt
            hist = train[v].iloc[-24 * 21:]
            fig, ax = plt.subplots(figsize=(13, 6))
            ax.plot(hist.index, hist.values, label="Historique (train)")
            ax.plot(test.iloc[:24].index, test[v].iloc[:24].values,
                    label="Observe (test)")
            ax.plot(prev_mdl.index, prev_mdl.values, "r--",
                    label=f"Prevision {choix}")
            if lo24 is not None:
                ax.fill_between(prev_mdl.index, lo24, hi24, color="red",
                                alpha=0.15, label="Intervalle 95 %")
                ax.set_title(f"Prevision {choix} - {v} (h=24) + IC 95 %")
            else:
                ax.set_title(f"Prevision {choix} - {v} (h=24)")
            ax.legend()
            fig.tight_layout()
            fig.savefig(FIGURES / f"py_prev_{v}.png", dpi=130)
            plt.close(fig)
        except Exception as exc:   # noqa: BLE001
            print("figure prevision ignoree :", exc)

    comp_df = pd.concat(table_comp, ignore_index=True)
    diag_df = pd.DataFrame(table_diag)
    met_df = pd.DataFrame(table_met)
    int_df = pd.DataFrame(table_int)

    comp_df.to_csv(TABLES / "py_arima_model_comparison.csv", index=False)
    diag_df.to_csv(TABLES / "py_arima_diagnostics.csv", index=False)
    met_df.to_csv(TABLES / "py_arima_metrics.csv", index=False)
    int_df.to_csv(TABLES / "py_arima_intervals.csv", index=False)

    print("\n===== TABLEAU DES METRIQUES (PY) =====")
    print(met_df.to_string(index=False))
    return comp_df, diag_df, met_df


# ---------------------------------------------------------------------------
# SECTION 3.2 - VAR / Granger / Johansen / VECM
# ---------------------------------------------------------------------------

# Valeurs critiques Osterwald-Lenum 1992 (95 %), configuration constante
# restreinte a l'espace de cointegration (urca ecdet='const'), p-r = 3..1,
# pour n = 3 variables. Ce sont exactement les jo@cval[, 2] de R/05.
JOHANSEN_CV_95 = np.array([34.91, 19.96, 9.24])

# R se cale sur 2100 jours (aggregate par date) ; floor(0.90 * nd) = 1890.
DAILY_ND = 2100
DAILY_NTR = int(np.floor(0.90 * DAILY_ND))


def section_var(dfi):
    """Reproduit R/05_VAR_VECM.R a l'echelle journaliere."""
    df = dfi.copy()
    for v in VARIABLES:
        df[v] = na_interp_hour(df[v])

    # Agrregation journaliere par MOYENNES (meme justification que R/05)
    daily = df.groupby(df.index.date).mean()
    daily.index = pd.to_datetime(daily.index)
    daily.index.freq = "D"
    tr = daily.iloc[:DAILY_NTR][VARIABLES]
    dtr = tr.diff().dropna()

    print("=" * 60)
    print("DONNEES JOURNALIERES :", len(daily), "jours | Train :",
          DAILY_NTR, "| Test :", len(daily) - DAILY_NTR)
    print("=" * 60)

    # --- Selection de l'ordre du VAR (differences, critere AIC) ---
    sel = VAR(dtr).select_order(15)
    p_sel = int(sel.aic)                       # statsmodels 0.15 : meilleur ordre AIC
    ics = sel.ics                              # dictionnaire AIC/HQ/BIC/FPE par lag
    table_ord = pd.DataFrame({
        "AIC": ics["aic"][1:], "HQ": ics["hqic"][1:], "SC": ics["bic"][1:],
        "FPE": ics["fpe"][1:],
    }, index=range(1, 16))
    print("Ordre retenu (AIC) : p =", p_sel)

    # Enregistrement sous le format R_var_order.csv (lignes criteres / colonnes lags)
    ord_out = table_ord.T.copy()
    ord_out.columns = range(1, 16)
    ord_out.to_csv(TABLES / "py_var_order.csv")

    # --- VAR(p) en differences + stabilite ---
    var_fit = VAR(dtr).fit(p_sel)
    nvar = 3
    comp = np.zeros((nvar * p_sel, nvar * p_sel))
    for lag in range(p_sel):
        comp[:nvar, lag * nvar:(lag + 1) * nvar] = var_fit.coefs[lag]
    comp[nvar:, :nvar * (p_sel - 1)] = np.eye(nvar * (p_sel - 1))
    maxmod = float(np.max(np.abs(np.linalg.eigvals(comp))))
    print("Racines du VAR : max modulus =", round(maxmod, 4), "(<1 stable)")

    # --- Granger bivarie (6 paires ordonnees, VAR(p) avec const) ---
    gr = []
    pairs = [("Wind", "Load"), ("Solar", "Load"), ("Load", "Wind"),
             ("Solar", "Wind"), ("Load", "Solar"), ("Wind", "Solar")]
    for cx, dy in pairs:
        g = grangercausalitytests(dtr[[dy, cx]].values, maxlag=p_sel,
                                  addconst=True)
        fstat, f_p = g[p_sel][0]["ssr_ftest"][0], g[p_sel][0]["ssr_ftest"][1]
        gr.append({"Hypothese": f"{cx} -> {dy}", "stat": fstat, "p": f_p,
                   "Conclusion": "OUI (rejet H0)" if f_p < 0.05 else "non"})
    gr_df = pd.DataFrame(gr)
    print("\n--- Causalite de Granger (H0 : X ne cause pas Y) ---")
    print(gr_df.to_string(index=False))
    gr_df.to_csv(TABLES / "py_granger.csv", index=False)

    # --- Diagnostic des residus du VAR ---
    resid_v = var_fit.resid
    whiten = var_fit.test_whiteness(nlags=16)
    norm = var_fit.test_normality()
    arch_rows = []
    for i, v in enumerate(VARIABLES):
        s, p = arch_lm_test(resid_v.iloc[:, i].values, q=5)
        arch_rows.append({"Test": f"ARCH_LM_{v}", "p": p})
    diag_rows = [
        {"Test": "Portmanteau", "p": float(whiten.pvalue)},
        {"Test": "Normalite", "p": float(norm.pvalue)},
    ] + arch_rows
    diag_df = pd.DataFrame(diag_rows)
    print("\n--- Diagnostic des residus du VAR ---")
    print(diag_df.to_string(index=False))
    diag_df.to_csv(TABLES / "py_var_diagnostics.csv", index=False)

    # --- Johansen (trace), statistiques identiques a R ---
    mean = tr.mean().values
    std = tr.std().values
    zs = (tr - tr.mean()) / tr.std()
    jo = coint_johansen(zs, det_order=0, k_ar_diff=p_sel)
    lr1 = np.asarray(jo.lr1)
    r_hat = int(np.sum(lr1 > JOHANSEN_CV_95))
    jo_df = pd.DataFrame({"Test": "Trace", "Rank": range(3),
                          "stat": lr1, "cv_95": JOHANSEN_CV_95})
    print("\n--- Johansen (trace) ---")
    print(jo_df.to_string(index=False))
    print(">>> Rang retenu : r =", r_hat)
    jo_df.to_csv(TABLES / "py_johansen.csv", index=False)

    vecm = None
    vecm_alpha = None
    vmod = var_fit

    if r_hat >= 1:
        # --- VECM : estimation en unites standardisees puis re-expression ---
        # dans les unites MW d'origine (beta / alpha).
        # z = diag(1/std)(y - mean) ; EC = beta_std' z + const_coint
        #   = beta_orig' y + c_orig  avec beta_orig = diag(1/std) beta_std
        #   et c_orig = const_coint - beta_orig' mean.
        # On renormalise ensuite a la cajorls : les r premieres lignes des
        # variables deviennent l'identite (B @ inv(B[:r,:r])), l'alpha et la
        # constante subissent la meme transformation de colonnes.
        vm = VECM(zs, k_ar_diff=p_sel, coint_rank=r_hat,
                  deterministic="co").fit()

        beta_std = np.asarray(vm.beta)         # (3, r), lignes = variables
        alpha_std = np.asarray(vm.alpha)       # (3, r)
        const_coint = np.asarray(vm.const_coint).ravel()   # (r,)

        B = np.diag(1.0 / std) @ beta_std      # coefficients sur y (niveaux)
        c = const_coint - B.T @ mean           # constante dans chaque ECT
        A = np.diag(std) @ alpha_std           # vitesses d'ajustement (MW)

        C = B[:r_hat, :r_hat]                  # renormalisation type cajorls
        if abs(np.linalg.det(C)) > 1e-12:
            B = B @ np.linalg.inv(C)
            c = c @ np.linalg.inv(C)
            # EC_new = G' EC_old (G = inv(C)) => alpha_new G' = alpha_old
            # => alpha_new = alpha_old @ (G')^-1 = alpha_old @ C'
            A = A @ C.T

        Bfull = np.vstack([B, c.reshape(1, -1)])
        vecm = pd.DataFrame(Bfull.round(4),
                            index=["Load.l1", "Wind.l1", "Solar.l1", "constant"],
                            columns=[f"ECT_{i + 1}" for i in range(r_hat)])
        vecm_alpha = pd.DataFrame(
            A.T.round(4), index=[f"ect{i + 1}" for i in range(r_hat)],
            columns=[f"{v}.d" for v in VARIABLES])
        print("\n--- Relations de cointegration normalisees (beta) ---")
        print(vecm.to_string())
        print("\n--- Vitesses d'ajustement (alpha) ---")
        print(vecm_alpha.to_string())

        vecm.to_csv(TABLES / "py_vecm.csv", index=False)
        vecm_alpha.to_csv(TABLES / "py_vecm_alpha.csv", index=False)

        # IRF / FEVD depuis le VECM
        vmod = vm

    # --- Impulsion-reponse de Load a Wind / Solar + FEVD ---
    print("IRF/FEVD : calcul en cours...", flush=True)
    irf = vmod.irf(28)
    irfs = np.asarray(irf.irfs)                # (horizon, n, n_impulse)
    if isinstance(vmod, VECMResults):
        # statsmodels 0.15 ne fournit plus to_var/fevd sur le VECM : on
        # construit la decomposition de la variance a partir des MA
        # orthonormalises (Cholesky de la covariance residuelle, ordre
        # Load, Wind, Solar comme dans vars::fevd par defaut).
        oma = np.asarray(vmod.orth_ma_rep(29))   # (29, n, n)
        n_hor = 28
        fevd = np.zeros((n_hor, 3, 3))
        for h in range(1, n_hor + 1):
            den = np.sum(oma[:h] ** 2, axis=(0, 2))
            for i in range(3):
                for j in range(3):
                    fevd[h - 1, i, j] = np.sum(oma[:h, i, j] ** 2) / den[i]
    else:
        fevd = np.asarray(vmod.fevd(28).fevd)  # (horizon, n, n_var)

    fev_rows = []
    for i, vv in enumerate(VARIABLES):
        for h in range(1, 29):
            row = {"Variable": vv, "Horizon": h}
            for j, jj in enumerate(VARIABLES):
                row[jj] = fevd[h - 1, i, j]
            fev_rows.append(row)
    fev_df = pd.DataFrame(fev_rows)
    fev_df.to_csv(TABLES / "py_var_fevd.csv", index=False)

    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        fig, ax = plt.subplots(figsize=(13, 6))
        for imp in [1, 2]:                     # Wind, Solar (ordre: Load, Wind, Solar)
            ax.plot(range(29), irfs[:, 0, imp],
                    label=f"Reponse de Load a un choc de {VARIABLES[imp]}")
        ax.axhline(0, color="grey", lw=0.8)
        ax.set_title("Reponse de Load a un choc de Wind / Solar (VECM)")
        ax.legend()
        fig.tight_layout()
        fig.savefig(FIGURES / "py_var_irf_load.png", dpi=130)
        plt.close(fig)

        fig, ax = plt.subplots(figsize=(13, 6))
        ax.plot(range(1, 29), fevd[:28, 0, 1], label="Part de Wind")
        ax.plot(range(1, 29), fevd[:28, 0, 2], label="Part de Solar")
        ax.set_title("Decomposition de la variance de Load")
        ax.legend()
        fig.tight_layout()
        fig.savefig(FIGURES / "py_var_fevd_load.png", dpi=130)
        plt.close(fig)
    except Exception as exc:   # noqa: BLE001
        print("figure IRF/FEVD ignoree :", exc)

    return p_sel, maxmod, gr_df, diag_df, jo_df, vecm, vecm_alpha, fev_df


# ---------------------------------------------------------------------------

def run():
    df = load_germany_series()
    print("Donnees chargees :", df.shape)

    comp, diag, met = section_arima(df)
    p_sel, maxmod, gr, vdiag, jo, vecm, alpha, fev = section_var(df)

    print("\n" + "=" * 60)
    print("SECTION 3 (Python) TERMINEE : ARIMA/SARIMA + VAR/Granger/VECM")
    print("p(VAR) =", p_sel, "| maxmod =", round(maxmod, 4))
    print("Tables ecrites dans", TABLES)
    print("=" * 60)


if __name__ == "__main__":
    run()