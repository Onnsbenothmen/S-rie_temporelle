# -*- coding: utf-8 -*-
"""
hybrid_arima_lstm.py
====================
SECTION 4.2 (Python) - approche HYBRIDE econometrie + deep learning.

Principe (hybridation classique tendance/residu non lineaire) :
  1. un modele SARIMA (retenu en section 3.1) capture la dynamique lineaire
     (tendance + saisonnalite) de la serie ;
  2. les RESIDUS de ce SARIMA sont supposes contenir la structure non
     lineaire restante ; un LSTM est entraine dessus (fenetre glissante) ;
  3. la prevision hybride = prevision SARIMA + prevision LSTM du residu.

Methodologie identique au reste du projet :
  - split STRICTEMENT chronologique 90 % / 10 % (anti-fuite) ;
  - normalisation MinMax des residus calculee sur le SEUL train ;
  - prevision recursive multi-pas du residu pour h = 5, 10, 24, 5040.

Sortie : results/tables/py_hybrid_metrics.csv (integre au leaderboard).
"""

import os
os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "2")

import numpy as np
import pandas as pd

from data_preparation import PROJECT_ROOT, load_germany_series
from arima_var import SARIMA_RETENU, na_interp_hour, metrics
from lstm_gru import build_net, prepare_sequences, WINDOW, SEED

TABLES = PROJECT_ROOT / "results" / "tables"
FIGURES = PROJECT_ROOT / "results" / "figures"
MODELS = PROJECT_ROOT / "results" / "models"

HORIZONS = (5, 10, 24, 5040)
RESID_EPOCHS = 20
BATCH = 256

# SARIMA retenu par variable (identique a R / Python, section 3.1)
SORDER = {
    "Load": ((1, 1, 1), (1, 1, 1, 24)),
    "Wind": ((1, 1, 1), (1, 1, 1, 24)),
    "Solar": SARIMA_RETENU["Solar"],
}


def _recursive(y0_scaled, model, scaler, h):
    x = np.asarray(y0_scaled[-WINDOW:], dtype=np.float32).reshape(1, WINDOW, 1)
    out = []
    for _ in range(h):
        p = float(model.predict(x, verbose=0)[0, 0])
        out.append(p)
        x = np.concatenate([x[:, 1:, :],
                            np.asarray([[[p]]], dtype=np.float32)], axis=1)
    return scaler.inverse_transform(np.asarray(out).reshape(-1, 1)).ravel()


def hybrid_one(v, train, test):
    from statsmodels.tsa.statespace.sarimax import SARIMAX
    from sklearn.preprocessing import MinMaxScaler

    order, sorder = SORDER[v]
    print(f"  [{v}] ajustement SARIMAX {order}x{sorder} ...", flush=True)
    lin = SARIMAX(np.asarray(train[v]), order=order, seasonal_order=sorder,
                  enforce_stationarity=False,
                  enforce_invertibility=False).fit(disp=False, method="lbfgs",
                                                   maxiter=30, low_memory=True)
    print(f"  [{v}] SARIMAX ajuste, residus + LSTM ...", flush=True)

    # Residus in-sample (composante non lineaire)
    fitted = np.asarray(lin.fittedvalues)
    resid = np.asarray(train[v]) - fitted
    resid = resid[np.isfinite(resid)]

    # LSTM sur les residus (normalisation sur le train uniquement)
    scaler = MinMaxScaler().fit(resid.reshape(-1, 1))
    s_res = scaler.transform(resid.reshape(-1, 1)).ravel()
    X, y = prepare_sequences(s_res, WINDOW, 1)
    cut = int(0.9 * len(X))
    np.random.seed(SEED)
    net = build_net("LSTM")
    from keras.callbacks import EarlyStopping
    net.fit(X[:cut], y[:cut], validation_data=(X[cut:], y[cut:]),
            epochs=RESID_EPOCHS, batch_size=BATCH, verbose=0,
            callbacks=[EarlyStopping(monitor="val_loss", patience=3,
                                     restore_best_weights=True)])
    print(f"  [{v}] LSTM residus entraine, prevision ...", flush=True)

    # Prevision hybride aux horizons demandes
    rows = []
    max_h = max(HORIZONS)
    lin_fc = np.asarray(lin.forecast(max_h))
    resid_fc = _recursive(s_res, net, scaler, max_h)
    hybrid = lin_fc + resid_fc
    for h in HORIZONS:
        m = metrics(np.asarray(test[v].iloc[:h]), hybrid[:h])
        m.update({"Variable": v, "Modele": "Hybride_SARIMA_LSTM", "Horizon": h})
        rows.append(m)
    return rows, hybrid, test[v].values


def _plot(v, obs, fc):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    h = min(168, len(fc))
    fig, ax = plt.subplots(figsize=(13, 6))
    ax.plot(range(h), obs[:h], label="Observe (test)")
    ax.plot(range(h), fc[:h], "r--", label="Hybride SARIMA+LSTM")
    ax.set_title(f"Hybride SARIMA + LSTM - {v} (h={h})")
    ax.legend()
    fig.tight_layout()
    fig.savefig(FIGURES / f"py_hybrid_{v}.png", dpi=130)
    plt.close(fig)


def main():
    import keras              # noqa: F401 - verifie la dispo
    df = load_germany_series().copy()
    for v in ("Load", "Wind", "Solar"):
        df[v] = na_interp_hour(df[v])
    n = len(df)
    n_train = int(np.floor(0.90 * n))
    train, test = df.iloc[:n_train], df.iloc[n_train:]

    table = []
    for v in ("Load", "Wind", "Solar"):
        print(f"##### hybride {v} #####")
        rows, fc, obs = hybrid_one(v, train, test)
        table += rows
        _plot(v, obs, fc)
        print(pd.DataFrame(rows).to_string(index=False))

    out = pd.DataFrame(table)
    out = out[["Variable", "Modele", "Horizon", "MSE", "RMSE", "MAE", "MAPE"]]
    TABLES.mkdir(parents=True, exist_ok=True)
    out.to_csv(TABLES / "py_hybrid_metrics.csv", index=False)
    print("Table ecrite :", TABLES / "py_hybrid_metrics.csv")
    return out


if __name__ == "__main__":
    main()
