# Gabarit de prompt — analyse assistée par IA (copier/coller)

Remplacez les bloc-notes `<...>` par les valeurs réelles tirées de
`results/tables/` et `results/figures/`. Collez ensuite l'ensemble dans un
assistant de votre choix et archivez la réponse dans `echanges/`.

---

## Contexte (à coller tel quel)

Projet universitaire de séries temporelles énergétiques (Allemagne, ENTSO-E),
fréquence horaire, 01/2015 → 09/2020 (50 400 h UTC). Données : Load
(consommation), Wind (éolien), Solar (solaire) en MW. Modélisation en R et
Python, double code, comparaison point à point.

Découpage CHRONOLOGIQUE 90 % / 10 % (test débutant le 05/03/2020, 5 040 h).
Horizons évalués : h = 10, 24, 5 040. Métriques : MSE, RMSE, MAE, MAPE (MAPE
sans division par zéro — Solar nul la nuit).

## Résultats factuels (à coller depuis les tables)

- **Comparaison ARIMA/SARIMA (AICc) — `R_arima_model_comparison.csv` /
  `py_arima_model_comparison.csv`** : ordres retenus et AICc minimaux :
  `<reporter les 3 lignes par variable>`.
- **Diagnostic résidus — `R_arima_diagnostics.csv` / `py_arima_diagnostics.csv`** :
  Ljung-Box(24), Jarque-Bera, ARCH-LM(12) : `<reporter les p-valeurs>`.
- **Prévisions — `R_arima_metrics.csv` / `py_arima_metrics.csv`** : RMSE/MAPE
  par modèle et horizon : `<reporter>`.
- **VAR jour. — `R_var_order.csv`** : ordre retenu p = <p_sel>
  (critère AIC). **Granger `R_granger.csv`** : seules
  <liste des paires significatives> ayant p < 0,05.
- **Johansen `R_johansen.csv` / `py_johansen.csv`** : trace → r = <r_hat>
  relations de cointégration. **VECM `R_vecm.csv`/`py_vecm.csv`** :
  <beta normalisé + constantes> ; alpha <vitesses d'ajustement>.
- **GARCH `R_garch_persistence.csv` / `py_garch_persistence.csv`** :
  persistance et stationnarité par série ; fortes persistances
  (<valeurs>), éventuelle non-stationnarité (Solar).
- **Outliers `outliers_summary.csv`** : <nb points atypiques IQR/MAD>.

## Questions à traiter (l'étudiant doit pouvoir défendre chaque réponse)

1. **Choix des modèles** : justifier la hiérarchie SARIMA_manuel vs
   SARIMA_auto vs ARIMA_auto (AICc) et l'absence de SARIMA à saisonnalité
   hebdomadaire (m=168) sur 45 000 points — quelles alternatives
   (régresseurs de Fourier, LSTM) ?
2. **Interprétation économique** : que révèle la causalité de Granger
   (seulement Wind→Load) et la cointégration r=2 entre Load, Wind, Solar ?
   Comment lire les vitesse d'ajustement (alpha) du VECM ?
3. **Volatilité** : pourquoi une forte persistance GARCH (ou >1) et qu'est-ce
   que cela implique pour la prévision de la volatilité (demi-vie) ?
4. **Limites** : MAPE explosif sur Solar au-delà de h=24, ordre VAR élevé
   (p=14 sur ~1 890 jours), période de test débutant à l'entrée du COVID —
   quelles précautions d'interprétation ?

## Contraintes de réponse

- Répondre en français, style rapport de données (neutre, précis).
- Ne jamais inventer de chiffres : tout chiffre avancé doit venir du
  contexte ci-dessus.
- Signalier les points faibles aussi nettement que les points forts.
- Terminer par une liste de 5 à 8 recommandations hiérarchisées.

---

`results/llm/README.md` précise la procédure d'archivage.