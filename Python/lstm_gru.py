# -*- coding: utf-8 -*-
"""
lstm_gru.py
===========
SECTION 4 (Python) - modeles profonds pour la prevision horaire.

Principes methodologiques (identiques au socle classique) :
  - split STRICTEMENT chronologique : fit (90 % du train), validation
    (derniere tranche du train), test (les 5 040 h finales) ;
  - normalisation MinMax calculee UNIQUEMENT sur la tranche d'ajustement
    (aucune information du test dans les statistiques de normalisation) ;
  - architecture recurrence univariee fenetre glissante -> 1 pas, puis
    PREVISION RECURSIVE pour h = 10, 24 et 5 040 (equivalent du mode
    dynamique des SARIMA) ;
  - deux architectures comparees : LSTM et GRU (keras 3), selection du
    meilleur sur la tranche de validation ;
  - regularisation par Dropout (p = DROPOUT) : justifie par le risque de
    sur-ajustement du reseau recurrent sur ~45 000 points horaires et par
    les courbes de perte train/validation (cf. rapport, section 4.1) ;
  - validation croisee TEMPORELLE (expanding window, jamais de k-fold
    classique) : n_folds fenetres d'entrainement croissantes, evaluation
    1 pas sur la fenetre suivante -> py_lstm_gru_cv.csv ;
  - seeds fixes (SEED = 123) pour la reproductibilite.

Sorties :
  - results/tables/py_lstm_gru_metrics.csv  (MSE/RMSE/MAE/MAPE par h,
    LSTM ET GRU reportes separement)
  - results/tables/py_lstm_gru_cv.csv       (RMSE par fold / architecture)
  - results/figures/py_lstm_gru_forecast_<v>.png (h=24) et _loss_<v>.png
  - results/models/lstm_gru_<v>.keras (meilleure architecture) et
    results/models/lstm_gru_<v>_<KIND>.keras (les deux architectures)
"""

import os
os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "2")

import numpy as np
import pandas as pd

from data_preparation import PROJECT_ROOT, load_germany_series

SEED = 123
WINDOW = 168          # 7 jours de fenetre de memoire (horaire)
VAL_H = 5040          # tranche de validation = 10 % du train (~3.5 mois)
HORIZONS = (10, 24, 5040)
BATCH = 256
UNITS = 32
MAX_EPOCHS = 30
PATIENCE = 4
DROPOUT = 0.2         # regularisation (LSTM/GRU -> Dropout -> Dense)
CV_FOLDS = 3          # validation croisee temporelle (expanding window)
CV_EPOCHS = 8         # budget reduit par fold (la CV multiplie les fits)
CV_MIN_FRAC = 0.5     # premiere fenetre d'entrainement = 50 % du train

TABLES = PROJECT_ROOT / "results" / "tables"
FIGURES = PROJECT_ROOT / "results" / "figures"
MODELS = PROJECT_ROOT / "results" / "models"


def na_interp_hour(series):
    """Interpolation des NA horaires sensible a la saisonnalite (24h).

    Identique a arima_var.na_interp_hour : mediane par heure de la journee
    puis interpolation lineaire locale (les NA sont rares : <0.2 %).
    """
    hour = series.index.hour
    med = series.groupby(hour).transform("median")
    filled = series.fillna(med)
    return filled.interpolate(method="linear").ffill().bfill()


def prepare_sequences(y, window_size, horizon=1):
    """Decoupe une serie en fenetres (features) et cible immediate.

    Retourne X ((n_window, window_size, 1), float32) et y_next (n_window,).
    horizon > 1 est supporte (cible directe multi-pas) mais la prevision
    recursive (horizon=1) est privilegiee ici.
    """
    y = np.asarray(y, dtype=np.float64)
    n = len(y)
    X, Y = [], []
    for t in range(window_size, n - horizon + 1):
        X.append(y[t - window_size: t])
        Y.append(y[t: t + horizon])
    X = np.asarray(X, dtype=np.float32)
    Y = np.asarray(Y, dtype=np.float32)
    if horizon == 1:
        Y = Y.ravel()
    return X, Y


def build_net(kind, units=UNITS):
    """Construit un reseau recurrent keras (LSTM ou GRU) -> 1 pas.

    Architecture : couche recurrente (LSTM ou GRU) -> Dropout(DROPOUT) ->
    Dense(1). Le Dropout desactive aleatoirement une fraction des unites a
    chaque pas de maniere a limiter le sur-ajustement (le reseau compte peu
    d'unites et beaucoup d'observations, le Dropout agit comme un bruit
    regularisant plutot qu'un goulot d'etranglement).
    """
    try:
        from keras import Sequential, layers
    except Exception as exc:   # noqa: BLE001
        raise RuntimeError(
            "keras/tensorflow indisponible : " + str(exc)) from exc
    model = Sequential([
        (layers.LSTM(units, input_shape=(WINDOW, 1))
         if kind == "LSTM" else layers.GRU(units, input_shape=(WINDOW, 1))),
        layers.Dropout(DROPOUT),
        layers.Dense(1),
    ])
    model.compile(optimizer="adam", loss="mse")
    return model


def recursive_forecast(y0, model, scaler, h):
    """Prevision recursive h pas : injecte chaque prediction dans la fenetre.

    Operation en echelle normalisee (0..1) puis retour a l'echelle originale
    (MW) via scaler.inverse_transform. Le modele est trace en tf.function
    (un pas graphifie) : ~10x plus rapide que model.predict appele h fois,
    ce qui rend la trajectoire h=5040 exploitable sur CPU.
    """
    import tensorflow as tf
    graph = tf.function(
        lambda x: model(x, training=False)[0, 0],
        autograph=False,
    )
    x = np.asarray(y0[-WINDOW:], dtype=np.float32).reshape(1, WINDOW, 1)
    pred = np.empty(h, dtype=np.float64)
    for i in range(h):
        p = float(graph(tf.constant(x)))
        pred[i] = p
        x = np.concatenate([x[:, 1:, :],
                            np.asarray([[[p]]], dtype=np.float32)], axis=1)
    return np.asarray(scaler.inverse_transform(pred.reshape(-1, 1)).ravel(),
                      dtype=np.float64)


def recursive_forecast_fast(y0, model, scaler, h):
    """Alias de recursive_forecast (la recursion est deja graphifiee)."""
    return recursive_forecast(y0, model, scaler, h)


def train_dl(y, v, scaler):
    """Ajuste LSTM et GRU, retourne le meilleur sur validation + courbes."""
    fit_slice, val_slice, test_slice = y["fit"].values, y["val"].values, y["test"].values

    s_fit = scaler.transform(fit_slice.reshape(-1, 1)).ravel()
    s_val = scaler.transform(val_slice.reshape(-1, 1)).ravel()
    X_fit, y_fit = prepare_sequences(s_fit, WINDOW, 1)
    X_val, y_val = prepare_sequences(s_val, WINDOW, 1)

    results = {}
    best = (None, np.inf, None)
    for kind in ("LSTM", "GRU"):
        np.random.seed(SEED)
        model = build_net(kind)
        from keras.callbacks import EarlyStopping
        hist = model.fit(
            X_fit, y_fit, validation_data=(X_val, y_val),
            epochs=MAX_EPOCHS, batch_size=BATCH, verbose=0,
            callbacks=[EarlyStopping(
                monitor="val_loss", patience=PATIENCE, restore_best_weights=True)],
        )
        val_loss = float(np.min(hist.history["val_loss"]))
        results[kind] = {"model": model, "val_loss": val_loss,
                         "history": {k: list(x) for k, x in hist.history.items()}}
        if val_loss < best[1]:
            best = (kind, val_loss, model)
        print(f"{kind} {v} : val_loss = {val_loss:.6f}")

    if best[0] is None:
        raise RuntimeError(f"aucune architecture {v} n'a converge (loss NaN)")

    kind_ok, _, model_ok = best
    print(f"Meilleure architecture {v} : {kind_ok}")
    MODELS.mkdir(parents=True, exist_ok=True)
    (MODELS / f"arch_{v}.txt").write_text(kind_ok)

    fh = results[kind_ok]["history"]
    fig_loss = _plot_loss(fh, v, kind_ok)
    return model_ok, kind_ok, results, fig_loss


# ---------------------------------------------------------------------------
# graphiques
# ---------------------------------------------------------------------------

def _plot_loss(history, var, kind):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(figsize=(11, 4))
    ax.plot(history["loss"], label="train")
    ax.plot(history["val_loss"], label="validation")
    ax.set_title(f"Loss {kind} - {var}")
    ax.set_xlabel("epoch"); ax.set_ylabel("MSE")
    ax.legend(); fig.tight_layout()
    return fig


def _plot_forecast(x, y, fc, var, kind):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(figsize=(13, 6))
    ax.plot(x.index, x.values, label="Historique (train)")
    ax.plot(y.index, y.values, label="Observe (test)")
    ax.plot(fc.index, fc.values, "r--", label=f"Prevision {kind} (h=24)")
    ax.set_title(f"Prevision {kind} - {var} (h=24)")
    ax.legend(); fig.tight_layout()
    return fig


# ---------------------------------------------------------------------------
# partie principale
# ---------------------------------------------------------------------------

def metrics(y, f):
    """Mise a l'echele originale et calcul des metriques (comme le socle)."""
    m = {"MSE": float(np.mean((y - f) ** 2)),
         "RMSE": float(np.sqrt(np.mean((y - f) ** 2))),
         "MAE": float(np.mean(np.abs(y - f)))}
    eps = 1e-9
    m["MAPE"] = float(np.mean(np.abs((y - f) / (y + eps))) * 100)
    return m


# ---------------------------------------------------------------------------
# validation croisee TEMPORELLE (expanding window)
# ---------------------------------------------------------------------------

def _graph_predict(model):
    """Fonction de prediction 1 pas graphifiee (tf.function)."""
    import tensorflow as tf
    return tf.function(lambda x: model(x, training=False)[0, 0],
                       autograph=False)


def time_series_cv(series, kind, var, n_folds=CV_FOLDS, max_val=720):
    """Validation croisee temporelle par fenetres d'entrainement CROISSANTES.

    Principe (jamais de k-fold classique) : la premiere fenetre couvre
    CV_MIN_FRAC du train, chaque fold suivante ajoute un bloc ; l'evaluation
    1 pas se fait sur le bloc SUIVANT, avec un reseau re-entraine a neuf.
    La derniere fenetre de validation est bornee (max_val) pour limiter le
    cout de la prediction pas-a-pas.
    """
    from sklearn.preprocessing import MinMaxScaler
    vals = np.asarray(series, dtype=float)
    n = len(vals)
    min_train = int(CV_MIN_FRAC * n)
    fold = (n - min_train) // n_folds
    rows = []
    for k in range(n_folds):
        tr_end = min_train + k * fold
        va_end = min(tr_end + fold, n)
        tr, va = vals[:tr_end], vals[tr_end:va_end]
        scaler = MinMaxScaler().fit(tr.reshape(-1, 1))
        s_tr = scaler.transform(tr.reshape(-1, 1)).ravel()
        X, y = prepare_sequences(s_tr, WINDOW, 1)
        cut = int(0.9 * len(X))
        np.random.seed(SEED)
        model = build_net(kind)
        from keras.callbacks import EarlyStopping
        model.fit(
            X[:cut], y[:cut], validation_data=(X[cut:], y[cut:]),
            epochs=CV_EPOCHS, batch_size=BATCH, verbose=0,
            callbacks=[EarlyStopping(monitor="val_loss", patience=2,
                                     restore_best_weights=True)],
        )
        s_full = scaler.transform(
            np.concatenate([tr, va]).reshape(-1, 1)).ravel()
        n_eval = min(len(va), max_val)
        g = _graph_predict(model)
        import tensorflow as tf
        p = np.empty(n_eval, dtype=np.float64)
        for i in range(n_eval):
            idx = tr_end + i
            x = s_full[idx - WINDOW:idx].reshape(1, WINDOW, 1).astype(np.float32)
            p[i] = float(g(tf.constant(x)))
        p = scaler.inverse_transform(p.reshape(-1, 1)).ravel()
        obs = va[:n_eval]
        rows.append({
            "Variable": var, "Modele": kind, "Fold": k + 1,
            "n_train": tr_end, "RMSE": float(np.sqrt(np.mean((obs - p) ** 2))),
            "MAE": float(np.mean(np.abs(obs - p))),
        })
        print(f"  CV {var} {kind} fold {k + 1}/{n_folds} "
              f"(n_train={tr_end}) : RMSE={rows[-1]['RMSE']:.2f}")
    return rows


def main():
    import sys
    try:
        import keras           # noqa: F401 - verifie la dispo des NN
    except Exception as exc:   # noqa: BLE001
        sys.exit("keras/tensorflow indisponible : " + str(exc))

    print("Chargement des donnees...")
    df = load_germany_series()
    df = df.copy()
    for v in ("Load", "Wind", "Solar"):
        df[v] = na_interp_hour(df[v])
    n = len(df)
    n_train = int(np.floor(0.90 * n))
    train_full = df.iloc[:n_train]
    test = df.iloc[n_train:]
    fit = train_full.iloc[: n_train - VAL_H]
    val = train_full.iloc[n_train - VAL_H:]

    from sklearn.preprocessing import MinMaxScaler

    do_cv = "--no-cv" not in sys.argv
    table = []
    cv_rows = []
    for v in ("Load", "Wind", "Solar"):
        print(f"##### {v} #####")
        scaler = MinMaxScaler()
        scaler.fit(np.asarray(fit[v]).reshape(-1, 1))
        dataset = {"fit": fit[v], "val": val[v], "test": test[v]}

        model_best, kind_best, results, fig_loss = train_dl(dataset, v, scaler)

        y0 = pd.concat([fit[v], val[v]]).values
        y0_s = scaler.transform(y0.reshape(-1, 1)).ravel()

        # --- les DEUX architectures sont evaluees (comparaison LSTM vs GRU) ---
        pred_h24 = None
        for kind, res in results.items():
            mdl = res["model"]
            preds = {h: recursive_forecast(y0_s, mdl, scaler, h)
                     for h in HORIZONS}
            for h in HORIZONS:
                y_ref = test[v].iloc[:h].values
                m = metrics(y_ref, preds[h])
                m.update({"Variable": v, "Modele": kind, "Horizon": h})
                table.append(m)
                print(f"{v} {kind} h={h} : " + " ".join(
                    f"{k}={val:.1f}" for k, val in m.items()
                    if k not in ("Variable", "Modele", "Horizon")))
            MODELS.mkdir(parents=True, exist_ok=True)
            mdl.save(MODELS / f"lstm_gru_{v}_{kind}.keras")
            if kind == kind_best:
                pred_h24 = preds[24]

        MODELS.mkdir(parents=True, exist_ok=True)
        model_best.save(MODELS / f"lstm_gru_{v}.keras")
        fig_fc = _plot_forecast(fit[v].iloc[-504:], test[v].iloc[:24],
                                pd.Series(pred_h24, index=test.iloc[:24].index), v, kind_best)
        fig_fc.savefig(FIGURES / f"py_lstm_gru_forecast_{v}.png", dpi=130)
        fig_loss.savefig(FIGURES / f"py_lstm_gru_loss_{v}.png", dpi=130)

        if do_cv:
            print(f"Validation croisee temporelle - {v} ({kind_best})...")
            cv_rows += time_series_cv(pd.concat([fit[v], val[v]]),
                                      kind_best, v)

    out = pd.DataFrame(table)
    out = out[["Variable", "Modele", "Horizon", "MSE", "RMSE", "MAE", "MAPE"]]
    out.to_csv(TABLES / "py_lstm_gru_metrics.csv", index=False)
    print("Table ecrite :", TABLES / "py_lstm_gru_metrics.csv")
    print(out.to_string(index=False))

    if cv_rows:
        cv_df = pd.DataFrame(cv_rows)
        cv_df.to_csv(TABLES / "py_lstm_gru_cv.csv", index=False)
        print("Table ecrite :", TABLES / "py_lstm_gru_cv.csv")
    return out


def deploy():
    """--deploy : recalcule metriques/figures depuis les modeles .keras deja
    entraines (evite de retailler 6 reseaux), avec recursion rapide."""
    import sys
    try:
        from keras.models import load_model
    except Exception as exc:   # noqa: BLE001
        sys.exit("keras/tensorflow indisponible : " + str(exc))
    from sklearn.preprocessing import MinMaxScaler

    print("Chargement des donnees...")
    df = load_germany_series()
    df = df.copy()
    for v in ("Load", "Wind", "Solar"):
        df[v] = na_interp_hour(df[v])
    n = len(df)
    n_train = int(np.floor(0.90 * n))
    train_full = df.iloc[:n_train]
    test = df.iloc[n_train:]
    fit = train_full.iloc[: n_train - VAL_H]
    val = train_full.iloc[n_train - VAL_H:]

    table = []
    for v in ("Load", "Wind", "Solar"):
        print(f"##### {v} #####")
        scaler = MinMaxScaler()
        scaler.fit(np.asarray(fit[v]).reshape(-1, 1))
        model = load_model(MODELS / f"lstm_gru_{v}.keras")
        ar = (MODELS / f"arch_{v}.txt")
        kind = (ar.read_text().strip() if ar.exists() else "LSTM/GRU")
        print(f"Architecture {v} : {kind}")
        y0 = scaler.transform(
            pd.concat([fit[v], val[v]]).values.reshape(-1, 1)).ravel()
        preds = {h: recursive_forecast_fast(y0, model, scaler, h)
                 for h in HORIZONS}
        for h in HORIZONS:
            fc = preds[h]
            y_ref = test[v].iloc[:h].values
            m = metrics(y_ref, fc)
            m.update({"Variable": v, "Modele": kind, "Horizon": h})
            table.append(m)
            print(f"{v} h={h} : " + " ".join(f"{k}={val:.1f}" for k, val
                                             in m.items() if k not in
                                             ("Variable", "Modele", "Horizon")))
        fig_fc = _plot_forecast(fit[v].iloc[-504:], test[v].iloc[:24],
                                pd.Series(preds[24],
                                          index=test.iloc[:24].index),
                                v, kind)
        fig_fc.savefig(FIGURES / f"py_lstm_gru_forecast_{v}.png", dpi=130)

    out = pd.DataFrame(table)
    out.to_csv(TABLES / "py_lstm_gru_metrics.csv", index=False)
    print("Table ecrite :", TABLES / "py_lstm_gru_metrics.csv")
    print(out.to_string(index=False))
    return out


if __name__ == "__main__":
    import sys
    if "--deploy" in sys.argv:
        deploy()
    else:
        main()