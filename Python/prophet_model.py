# -*- coding: utf-8 -*-
"""
prophet_model.py
================
SECTION 4.3 (Python) - modele additionnel Prophet (Meta).

Prophet decompose automatiquement la serie en tendance (piecewise lineaire),
saisonnalites (quotidienne / hebdomadaire / annuelle) et effets de jours
feries. Il est robuste aux donnees manquantes et sert ici de comparateur
"decomposition automatique" face au SARIMA et au LSTM/GRU.

Methodologie identique au reste du projet :
  - split STRICTEMENT chronologique 90 % / 10 % (anti-fuite) ;
  - ajustement sur le train seulement, prevision sur le test ;
  - metriques aux horizons h = 5, 10, 24, 5040.

Sortie : results/tables/py_prophet_metrics.csv (integre au leaderboard).
"""

import os
os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "2")

import logging
logging.getLogger("cmdstanpy").setLevel(logging.WARNING)
logging.getLogger("prophet").setLevel(logging.WARNING)

import numpy as np
import pandas as pd

from data_preparation import PROJECT_ROOT, load_germany_series
from arima_var import na_interp_hour, metrics

TABLES = PROJECT_ROOT / "results" / "tables"
FIGURES = PROJECT_ROOT / "results" / "figures"

HORIZONS = (5, 10, 24, 5040)


def fit_predict(v, train, test):
    from prophet import Prophet
    ds = pd.DataFrame({"ds": train.index.tz_localize(None) if
                       train.index.tz is not None else train.index,
                       "y": train[v].values})
    m = Prophet(daily_seasonality=True, weekly_seasonality=True,
                yearly_seasonality=True, interval_width=0.95)
    m.fit(ds)

    future = m.make_future_dataframe(periods=len(test), freq="h")
    fc = m.predict(future).set_index("ds").iloc[-len(test):]

    pred = fc["yhat"].values
    rows = []
    for h in HORIZONS:
        mm = metrics(np.asarray(test[v].iloc[:h]), pred[:h])
        mm.update({"Variable": v, "Modele": "Prophet", "Horizon": h})
        rows.append(mm)
    return rows, pred, fc


def _plot(v, obs, fc):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    h = min(168, len(fc))
    fig, ax = plt.subplots(figsize=(13, 6))
    ax.plot(range(h), obs[:h], label="Observe (test)")
    ax.plot(range(h), fc["yhat"].values[:h], "r--", label="Prophet")
    ax.fill_between(range(h), fc["yhat_lower"].values[:h],
                    fc["yhat_upper"].values[:h], color="red", alpha=0.15,
                    label="Intervalle 95 %")
    ax.set_title(f"Prophet - {v} (h={h})")
    ax.legend()
    fig.tight_layout()
    fig.savefig(FIGURES / f"py_prophet_{v}.png", dpi=130)
    plt.close(fig)


def main():
    df = load_germany_series().copy()
    for v in ("Load", "Wind", "Solar"):
        df[v] = na_interp_hour(df[v])
    n = len(df)
    n_train = int(np.floor(0.90 * n))
    train, test = df.iloc[:n_train], df.iloc[n_train:]

    table = []
    for v in ("Load", "Wind", "Solar"):
        print(f"##### Prophet {v} #####")
        rows, pred, fc = fit_predict(v, train, test)
        table += rows
        _plot(v, test[v].values, fc)
        print(pd.DataFrame(rows).to_string(index=False))

    out = pd.DataFrame(table)
    out = out[["Variable", "Modele", "Horizon", "MSE", "RMSE", "MAE", "MAPE"]]
    TABLES.mkdir(parents=True, exist_ok=True)
    out.to_csv(TABLES / "py_prophet_metrics.csv", index=False)
    print("Table ecrite :", TABLES / "py_prophet_metrics.csv")
    return out


if __name__ == "__main__":
    main()
