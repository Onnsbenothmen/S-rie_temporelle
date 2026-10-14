# rapport/ - rapport scientifique final

Ce dossier contiendra le rapport final du mini-projet :

- `rapport_final.docx` : rapport éditable (généré depuis `notebooks/analyse_complete.Rmd`
  ou via Quarto/Pandoc, texte + figures + tableaux).
- `rapport_final.pdf`  : version PDF du rapport.

Contenu prévu :
1. Introduction et thématique (Énergie - Allemagne, ENTSO-E).
2. Données (source, période, transformations, manquants).
3. Analyse exploratoire (saisonnalités, stationnarité, outliers).
4. Socle classique R (sections 3.1 ARIMA/SARIMA, 3.2 VAR/VECM, 3.3 GARCH) :
   choix d'ordres, diagnostics, tableaux de performances.
5. Transposition Python et modèles avancés (LSTM/GRU) - fait.
6. Évaluation comparée (walk-forward + Diebold-Mariano) - fait.
7. Conclusion et limites.

Les tableaux et figures sont automatiquement écrits par les scripts dans
`results/tables/` et `results/figures/` (ce dossier de notes ne contient que
le texte source).