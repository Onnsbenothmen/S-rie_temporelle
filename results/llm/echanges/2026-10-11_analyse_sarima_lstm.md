# Échange du 11/10/2026 — volet IA (manuel, no-API)

## Contexte fourni (extrait du prompt_llm.md)
- ENTSO-E Allemagne, horaire 01/01/2015–30/09/2020 (50 400 h), séries : Load, Wind, Solar (MW).
- Découpage chronologique 90%/10% ; horizons h=10,24,5040 ; métriques MSE/RMSE/MAE/MAPE.
- Objectif : interroger sur les résultats existants (fichiers CSV/figures) sans inventer de chiffres.

## Fichier(s) sourcés
- `results/tables/py_arima_model_comparison.csv`
- `results/tables/py_arima_metrics.csv`
- `results/tables/py_arima_diagnostics.csv`
- `results/tables/py_var_order.csv`, `py_granger.csv`, `py_johansen.csv`, `py_vecm.csv`
- `results/tables/py_garch_persistence.csv`, `py_garch_coefficients.csv`
- `results/tables/py_lstm_gru_metrics.csv`
- `results/tables/py_evaluation_ranking.csv`

## Question posée (type)
« Justifier la hiérarchie SARIMA vs LSTM à court/moyen/long terme à partir des RMSE présents et formuler 5 recommandations hiérarchisées. »

## Réponse synthétique (à relire et adapter au rapport)
- À h=10/24 : SARIMA/SARIMA_auto dominent souvent sur Load/Wind/Solar (erreurs faibles) ; LSTM compétitif sur Load h=10. À h=5040 : LSTM surpasse SARIMA sur Load (RMSE ~11.8k vs 65.8k), tendance inverse ou moins claire selon Wind/Solar (MAPE explosif Solar).
- Granger : seule Wind → Load significative (p=0.0022). Johansen r=2 ; VECM valide l'ajustement à court terme.
- GARCH : forte persistance (proche/≥0.9) ; Solar très erratique près de zéro (MAPE trompeur).
- Limites : test début COVID (05/03/2020), VAR p=14, m=24 uniquement, pas de régresseurs de Fourier/externes.
- Recommandations : 1) privilégier SARIMA à h court, LSTM à très long horizon sur Load ; 2) documenter Solar MAPE ; 3) tester régresseurs Fourier (m=168) ; 4) améliorer LSTM (multi-variable) ; 5) rapporter DM entre SARIMA/LSTM sur les trajectoires.

## Validité
Seuls les chiffres ci-dessus ont été extraits des tables CSV produites. Aucun ordre non justifié n'a été ajouté.

## Archivée par
Élève du mini-projet séries temporelles — 11/10/2026.