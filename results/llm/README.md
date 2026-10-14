# Volet IA générative — protocole manuel

Objectif du volet : rédiger des **analyses narratives** et des **notions
d'interprétation** pour le rapport, via un modèle de langage, SANS exposer de
clé API ni inventer de contenu.

## Principe

Aucun titre/crédit API n'est configuré dans ce mini-projet : l'assistant IA
est consulté **hors ligne par l'étudiant** (copier/coller dans un chat grand
public ou un outil local), puis la **transcription** est archivée dans ce dos
sier. C'est ce journal qui constitue la partie reproductible du volet.

## Procédure (5 étapes)

1. **Générer les résumés factuels** depuis les tables/figures de `results/`
   (voir `prompt_llm.md` pour le gabarit) et les COLLER dans le prompt.
2. Consigner la date-vérification du modèle utilisé (nom, version/date).
3. Reprendre uniquement les éléments **vérifiables** et **confrontés aux
   résultats** dans le rapport ; jamais de chiffre non sourcé.
4. Enregistrer chaque échange sous `results/llm/echanges/YYYY-MM-DD_<sujet>.md`.
5. Marquer dans le rapport (`rapport/chapters/` section IA) les passages issus
   de l'assistant avec la mention « analyse assistée par IA ».

## Déjà archivé

- `echanges/2026-10-11_analyse_sarima_lstm.md` — hiérarchie SARIMA vs LSTM.
- `echanges/2026-10-12_interpretation_var_vecm_garch.md` — lecture VAR/VECM,
  causalité de Granger, persistance GARCH (avec relecture critique).
- `echanges/2026-10-12_hierarchie_modeles_recommandations.md` — hiérarchie
  par horizon, walk-forward vs trajectoire, recommandations (relecture
  critique : corrections, rejets, ajouts).

## Contraintes anti-hallucination

- Les **statistiques** (p-valeurs, AIC, RMSE…) proviennent exclusivement des
  tables CSV de `results/tables/`, jamais du souvenir du modèle.
- Les ordres retenus, conclusions des tests et valeurs de métriques doivent
  être *repris tels quels* dans le prompt pour éviter toute divergence.
- Le rendu final du rapport est de la responsabilité de l'étudiant : toute
  formulation trompeuse héritée du modèle doit être corrigée.