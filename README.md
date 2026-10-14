# Mini-projet Séries Temporelles — Énergie en Allemagne (ENTSO-E)

Analyse et prévision des séries temporelles énergétiques allemandes à fréquence **horaire** : Load (consommation), Wind (éolien), Solar (solaire), en MW. Période 01/01/2015–30/09/2020 (50 400 heures UTC), source ENTSO-E. Rendu 12/10/2026 — socle classique exigé en **R et Python**.

**Dépôt GitHub :** https://github.com/Onnsbenothmen/S-rie_temporelle

## Arborescence (essentielle)
- `data/processed/` — données préparées
- `R/` — scripts R complets (audités/corrigés)
- `Python/` — transposition Python (arima_var, garch, lstm_gru, evaluation)
- `results/tables/`, `results/figures/`, `results/forecasts/`, `results/models/`, `results/llm/`
- `rapport/` — rapport LaTeX (compilé en PDF)
- `dashboard/` — Streamlit
- `notebooks/` — Rmd + Jupyter

## Exécution rapide (Python)
```bash
# Données -> déjà présentes
python Python/arima_var.py  # 3.1–3.2 (4–6 min env standard) -> py_*.csv + figures
python Python/garch.py      # 3.3 -> py_garch_*
python Python/lstm_gru.py   # 4  (entrainement court ou --deploy)
python Python/lstm_gru.py --deploy  # rapide via modèles .keras
python Python/evaluation.py # 6  leaderboard + walk-forward + DM
```

## Dépendances Python (essentielles)
Voir `dashboard/requirements.txt` et `Python/*`. Principales : pandas, numpy, scipy, matplotlib, seaborn, statsmodels, pmdarima, arch, scikit-lelearn, keras/tensorflow, torch (optionnel), streamlit, plotly.

## Remarques
- Split chronologique strict 90/10. Test commence 05/03/2020 (à interpréter).
- Solar MAPE explosif aux heures nulles (proche de zéro) — à justifier dans le rapport.
- SARIMA : m=24 uniquement. VAR sur moyennes journalières (cointégration r=2). GARCH : forte persistance ; Load parfois dégénéré (convergence = False).
- Volet IA : protocole manuel, sans clé API (cf. `results/llm/`).
- Tables/figures préfixées `py_` (Python), `R_` (R).
- Données brutes (`data/raw/`, ~124 Mo) **non versionnées** (limite GitHub de 100 Mo) ; la version analytique préparée est fournie dans `data/processed/`.
```txt
État (synthétique) :
- 3.1–3.2 : OK (py_arima_*, py_var_*, py_johansen, py_vecm*)
- 3.3 : OK (py_garch_*)
- 4 : OK (py_lstm_gru_metrics.csv + py_lstm_gru_cv.csv, figures, modèles par arch.)
- 6 : OK (py_evaluation_*, py_walkforward_*, DM toutes paires)
```
